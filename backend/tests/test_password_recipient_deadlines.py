"""Audit work cannot extend a password recipient's original DB deadline."""

from contextlib import closing
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.password_helpers import call, link_token, login_password, provision, reset_request
from tests.test_iam import ORIGIN, csrf
from tests.test_iam_emergency import issue, operator, request
from y3management.application import create_app
from y3management.audit.infrastructure import Audit
from y3management.audit.public import Event, PasswordEmergencyEvent
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize("flow", ["setup", "reset", "emergency"])
def test_final_recipient_deadline_after_audit(
    password_app: tuple[Settings, Database, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    flow: str,
) -> None:
    token: str
    settings, db, password = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as actor:
        login_password(actor, password)
        with closing(TestClient(actor.app, base_url=ORIGIN)) as recipient:
            if flow == "setup":
                response = call(
                    actor, "/admin/master-accounts", csrf(actor), {"login_id": "deadline.master"}
                )
                assert response.status_code == 201
                ident = response.json()["account_id"]
                token = link_token(response.json()["setup_link"])
                table = "iam_credentials"
                path = "/auth/credentials/complete"
                field = "setup_token"
            elif flow == "reset":
                ident = provision(actor, recipient, password)
                response = reset_request(actor, ident)
                assert response.status_code == 201
                token = link_token(response.json()["reset_link"])
                table = "iam_reset_credentials"
                path = "/auth/password-reset/complete"
                field = "reset_token"
            else:
                service, principal, target = operator(settings, db, tmp_path / "operator")
                ident = str(target)
                token = issue(service, principal, request(service, principal, target))
                table = "iam_password_emergency_credentials"
                path = "/auth/emergency-recovery/password/complete"
                field = "emergency_token"
            recipient.cookies.clear()
            nonce = csrf(recipient)
            with db.session() as session:
                if flow == "emergency":
                    session.execute(
                        text(
                            "WITH c AS (UPDATE iam_password_emergency_cases "
                            "SET expires_at=clock_timestamp()+interval '3 seconds' WHERE "
                            "account_id=:a "
                            "RETURNING id,expires_at), p AS (UPDATE iam_security_states s SET "
                            "expires_at=c.expires_at "
                            "FROM iam_password_emergency_credentials e JOIN c ON c.id=e.case_id "
                            "WHERE s.id=e.id RETURNING s.id,s.expires_at) "
                            "UPDATE iam_password_emergency_credentials e SET "
                            "expires_at=p.expires_at FROM p WHERE e.id=p.id"
                        ),
                        {"a": ident},
                    )
                else:
                    session.execute(
                        text(
                            f"UPDATE {table} SET expires_at=clock_timestamp()+interval '3 seconds' "
                            "WHERE account_id=:a"
                        ),
                        {"a": ident},
                    )
                session.commit()
            reached = []
            append, emergency = Audit.append, Audit.append_password_emergency

            def delayed(adapter: Audit, event: Event) -> None:
                append(adapter, event)
                if event.action in ("setup_complete", "password_reset_complete"):
                    reached.append(event.action)
                    adapter.s.execute(text("SELECT pg_sleep(1.6)"))
                    adapter.s.execute(text("SELECT pg_sleep(1.6)"))

            def delayed_emergency(adapter: Audit, event: PasswordEmergencyEvent) -> None:
                emergency(adapter, event)
                if event.action == "complete":
                    reached.append(event.action)
                    adapter.s.execute(text("SELECT pg_sleep(1.6)"))
                    adapter.s.execute(text("SELECT pg_sleep(1.6)"))

            with monkeypatch.context() as patch:
                patch.setattr(Audit, "append", delayed)
                patch.setattr(Audit, "append_password_emergency", delayed_emergency)
                response = call(recipient, path, nonce, {field: token, "new_password": password})
            assert response.status_code == (400 if flow == "setup" else 401)
            assert len(reached) == 1
            assert "__Host-y3-auth" not in recipient.cookies
            with db.session() as session:
                account = session.execute(
                    text(
                        "SELECT state,password_hash IS NULL,password_reset_pending FROM "
                        "iam_accounts WHERE id=:a"
                    ),
                    {"a": ident},
                ).one()
                assert tuple(account) == (
                    ("PENDING_SETUP", True, False) if flow == "setup" else ("ACTIVE", True, True)
                )
                assert (
                    session.execute(
                        text(f"SELECT consumed FROM {table} WHERE account_id=:a"), {"a": ident}
                    ).scalar_one()
                    is False
                )
