"""C2 and final-delivery invariants retained after retiring the second factor."""

from dataclasses import replace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.password_helpers import call, login_password, prepare_login
from tests.test_iam import ORIGIN, SyntheticSecret, csrf
from y3management.application import create_app
from y3management.audit.infrastructure import Audit
from y3management.audit.public import Event
from y3management.config import Settings
from y3management.contracts import Rejected
from y3management.database import Database
from y3management.iam.infrastructure import IAM
from y3management.iam.public import LoginProof, Reservation
from y3management.iam.security import Security

pytestmark = pytest.mark.postgres


def attempt(client: TestClient, password: str, identifier: str = "master.test") -> Any:
    return call(client, "/auth/login", csrf(client), {"login_id": identifier, "password": password})


def test_c2_shared_budget_success_does_not_clear(
    password_app: tuple[Settings, Database, str],
) -> None:
    settings, db, password = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        for _ in range(2):
            assert attempt(client, "wrong").status_code == 401
        login_password(client, password)
        assert call(client, "/auth/logout", csrf(client), {}).status_code == 204
        for _ in range(3):
            assert attempt(client, "wrong").status_code == 401
        assert attempt(client, password).status_code == 429
        with db.session() as session:
            assert (
                session.execute(
                    text("SELECT count(*) FROM iam_attempts WHERE outcome='failure'")
                ).scalar_one()
                == 5
            )


def test_waiting_is_bounded_and_counts_toward_admission(
    password_app: tuple[Settings, Database, str],
) -> None:
    settings, db, password = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        for _ in range(5):
            prepare_login(client, "master.test", password)
        assert attempt(client, password).status_code == 429
        with db.session() as session:
            assert (
                session.execute(
                    text(
                        "SELECT count(*) FROM iam_attempts WHERE policy_version=2 "
                        "AND outcome='pending' AND lease_until>clock_timestamp()"
                    )
                ).scalar_one()
                == 5
            )
            session.execute(
                text("UPDATE iam_attempts SET lease_until=clock_timestamp()-interval '1 second'")
            )
            session.commit()
        assert attempt(client, password).status_code == 429
        with db.session() as session:
            assert (
                session.execute(
                    text("SELECT count(*) FROM iam_attempts WHERE outcome='failure'")
                ).scalar_one()
                == 5
            )


@pytest.mark.parametrize("failure", ["audit", "finish", "finish_ack", "cleanup"])
def test_failed_final_delivery_never_returns_cookie(
    password_app: tuple[Settings, Database, str], monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    settings, db, password = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        login_password(client, password)
        preserved = SyntheticSecret(client.cookies.get("__Host-y3-auth") or "")
        with db.session() as session:
            original_id = session.execute(text("SELECT id FROM iam_sessions")).scalar_one()
        client.cookies.clear()
        nonce = csrf(client)
        append, finish = Audit.append, Security.finish

        def audit(adapter: Audit, value: Event) -> None:
            if value.action == "login" and value.success:
                raise Rejected(503, "unavailable")
            append(adapter, value)

        def fail_finish(adapter: Security, reservation: Reservation, success: bool) -> None:
            if success:
                if failure == "finish_ack":
                    finish(adapter, reservation, success)
                    adapter.s.commit()
                raise Rejected(503, "unavailable")
            finish(adapter, reservation, success)

        def fail_cleanup(adapter: IAM, sid: Any, **kwargs: Any) -> None:
            raise Rejected(503, "unavailable")

        with monkeypatch.context() as patch:
            if failure == "audit":
                patch.setattr(Audit, "append", audit)
            else:
                patch.setattr(Security, "finish", fail_finish)
            if failure == "cleanup":
                patch.setattr(IAM, "revoke_undelivered_session", fail_cleanup)
            response = call(
                client, "/auth/login", nonce, {"login_id": "master.test", "password": password}
            )
        assert response.status_code == 503
        assert "__Host-y3-auth" not in client.cookies
        with db.session() as session:
            rows = session.execute(
                text("SELECT id,revoked FROM iam_sessions WHERE id<>:i"), {"i": original_id}
            ).all()
            assert len(rows) == (0 if failure == "audit" else 1)
            if failure not in ("audit", "cleanup"):
                assert rows[0].revoked
            if failure == "cleanup":
                assert response.json()["detail"] == "unavailable"
                session.execute(
                    text("UPDATE iam_sessions SET revoked=true WHERE id=:i"), {"i": rows[0].id}
                )
                session.commit()
        assert (
            client.get(
                "/api/v1/auth/me", headers={"Cookie": "__Host-y3-auth=" + preserved}
            ).status_code
            == 200
        )


@pytest.mark.parametrize("where", ["start", "final"])
def test_actual_budget_key_binding(
    password_app: tuple[Settings, Database, str], monkeypatch: pytest.MonkeyPatch, where: str
) -> None:
    settings, db, password = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        reserve, verify = Security.reserve, IAM.verify_login

        def altered(adapter: Security, identifier: str) -> Reservation:
            normal = reserve(adapter, identifier)
            foreign = reserve(adapter, "unassigned.test")
            return replace(
                foreign, account_id=normal.account_id, security_version=normal.security_version
            )

        def changed(
            adapter: IAM, identifier: str, value: str, reservation: Reservation
        ) -> LoginProof | None:
            proof = verify(adapter, identifier, value, reservation)
            with db.session() as session:
                session.execute(
                    text("UPDATE iam_accounts SET login_budget_key=:k"), {"k": bytes(32)}
                )
                session.commit()
            return proof

        with monkeypatch.context() as patch:
            if where == "start":
                patch.setattr(Security, "reserve", altered)
            else:
                patch.setattr(IAM, "verify_login", changed)
            assert attempt(client, password).status_code == 503
        with db.session() as session:
            assert session.execute(text("SELECT count(*) FROM iam_sessions")).scalar_one() == 0


def test_failed_login_audit_principal_and_unknown(
    password_app: tuple[Settings, Database, str],
) -> None:
    settings, db, _ = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        for name in ("master.test", "unknown.test", "master.test"):
            assert attempt(client, "wrong", name).status_code == 401
        with db.session() as session:
            account = session.execute(text("SELECT id,organization_id FROM iam_accounts")).one()
            events = session.execute(
                text(
                    "SELECT organization_id,target_id FROM audit_events "
                    "WHERE action='login' AND NOT success ORDER BY happened_at"
                )
            ).all()
            assert [tuple(row) for row in events] == [
                (account.organization_id, account.id),
                (None, None),
                (account.organization_id, account.id),
            ]
