# ruff: noqa: F811
"""Purpose, expiry, atomicity and commit uncertainty of management authority."""

import hashlib
import json
from contextlib import closing

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from tests.test_iam import ORIGIN, csrf
from tests.test_iam_mfa import Authenticator, call, enroll, login_mfa, mfa, protect  # noqa: F401
from tests.test_iam_mfa_management import (
    add,
    delete,
    keys,
    link_token,
    recovery_options,
    recovery_request,
)
from tests.test_iam_mfa_management_races import provision
from y3management.application import create_app
from y3management.audit.infrastructure import Audit
from y3management.audit.public import Event
from y3management.config import Settings
from y3management.contracts import Rejected
from y3management.database import Database

pytestmark = pytest.mark.postgres


def snapshot(db: Database) -> str:
    with db.session() as s:
        value = {}
        for table in (
            "iam_accounts",
            "iam_admin_grants",
            "iam_login_ids",
            "iam_passkeys",
            "iam_recovery_credentials",
            "iam_credentials",
            "iam_mfa_contexts",
            "audit_events",
        ):
            query = f"SELECT row_to_json(t)::text FROM {table} t"
            if table in ("iam_recovery_credentials", "iam_credentials", "iam_mfa_contexts"):
                query += " WHERE NOT consumed AND expires_at>clock_timestamp()"
            value[table] = protect(sorted(s.execute(text(query)).scalars()))
        # A preflight can touch activity, but revocation and epochs must remain atomic.
        value["sessions"] = sorted(
            str(r) for r in s.execute(text("SELECT id,revoked,security_version FROM iam_sessions"))
        )
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


@pytest.mark.parametrize(
    "case", ["source_expired", "context_expired", "reissue", "issuer_logout", "wrong_purpose"]
)
def test_recovery_authority_boundaries(mfa: tuple[Settings, Database, str, str], case: str) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        key = Authenticator()
        enroll(first, token, key)
        login_mfa(first, password, key)
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            ident, _ = provision(first, second, password)
            issued = recovery_request(first, ident)
            raw = link_token(issued.json()["recovery_link"])
            if case == "source_expired":
                with db.session() as s:
                    s.execute(
                        text(
                            "UPDATE iam_recovery_credentials SET expires_at=clock_timestamp() "
                            "WHERE account_id=:a"
                        ),
                        {"a": ident},
                    )
                    s.commit()
                assert recovery_options(second, raw).status_code == 401
                return
            options = recovery_options(second, raw).json()
            if case == "wrong_purpose":
                assert (
                    call(
                        second,
                        "/auth/passkeys/enrollment/options",
                        csrf(second),
                        {"setup_token": raw},
                    ).status_code
                    == 401
                )
                assert recovery_options(second, token).status_code == 401
                return
            if case == "context_expired":
                with db.session() as s:
                    s.execute(
                        text(
                            "UPDATE iam_mfa_contexts SET expires_at=clock_timestamp() "
                            "WHERE account_id=:a AND purpose='recovery'"
                        ),
                        {"a": ident},
                    )
                    assert s.execute(
                        text(
                            "SELECT expires_at>clock_timestamp() FROM iam_recovery_credentials "
                            "WHERE account_id=:a"
                        ),
                        {"a": ident},
                    ).scalar_one()
                    s.commit()
            if case == "reissue":
                reissued = recovery_request(first, ident, reissue=True)
                assert reissued.status_code == 201
                with db.session() as s:
                    metadata = s.execute(
                        text(
                            "SELECT before_key_set_version,after_key_set_version,"
                            "before_recovery_generation,after_recovery_generation "
                            "FROM audit_events WHERE action='recovery_reissue'"
                        )
                    ).one()
                    assert tuple(metadata) == (2, 3, 1, 2)
                assert recovery_options(second, raw).status_code == 401
            if case == "issuer_logout":
                assert call(first, "/auth/logout", csrf(first), {}).status_code == 204
            result = call(
                second,
                "/auth/passkeys/recovery/verify",
                options["csrf_token"],
                {"credential": Authenticator().registration(options["publicKey"])},
            )
            assert result.status_code == (204 if case == "issuer_logout" else 401)
            if case == "reissue":
                newer = recovery_options(second, link_token(reissued.json()["recovery_link"]))
                assert newer.status_code == 200


@pytest.mark.parametrize(
    "action",
    [
        "passkey_delete",
        "account_issue",
        "setup_reissue",
        "recovery_start",
        "recovery_reissue",
        "recovery_complete",
    ],
)
@pytest.mark.parametrize("fault", ["audit", "commit_ack"])
def test_atomic_effects_and_commit_ambiguity(
    mfa: tuple[Settings, Database, str, str],
    monkeypatch: pytest.MonkeyPatch,
    action: str,
    fault: str,
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        key = Authenticator()
        enroll(first, token, key)
        login_mfa(first, password, key)
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            ident, _ = provision(first, second, password)
            if action == "passkey_delete":
                add(first, Authenticator())
                key_state = keys(first)
            if action == "setup_reissue":
                pending = call(
                    first, "/admin/master-accounts", csrf(first), {"login_id": "pending.master"}
                ).json()
            if action in ("recovery_reissue", "recovery_complete"):
                issued = recovery_request(first, ident)
                raw = link_token(issued.json()["recovery_link"])
                if action == "recovery_complete":
                    options = recovery_options(second, raw).json()
            before = snapshot(db)
            append = Audit.append
            commit = Session.commit

            def audit(adapter: Audit, event: Event) -> None:
                if event.action == action:
                    if fault == "audit":
                        raise Rejected(503, "unavailable")
                    adapter.s.info["lose_ack"] = True
                append(adapter, event)

            def lost_ack(session: Session) -> None:
                lose = session.info.pop("lose_ack", False)
                commit(session)
                if lose:
                    raise OperationalError("COMMIT", None, RuntimeError("ack lost"))

            with monkeypatch.context() as patch:
                patch.setattr(Audit, "append", audit)
                patch.setattr(Session, "commit", lost_ack)
                if action == "passkey_delete":
                    status = delete(
                        first, key_state["items"][0]["key_id"], key_state["key_set_version"]
                    )
                elif action == "account_issue":
                    status = call(
                        first, "/admin/master-accounts", csrf(first), {"login_id": "ack.master"}
                    ).status_code
                elif action == "setup_reissue":
                    status = call(
                        first,
                        "/admin/master-accounts/" + pending["account_id"] + "/activation",
                        csrf(first),
                        {"expected_version": 1},
                    ).status_code
                elif action == "recovery_complete":
                    status = call(
                        second,
                        "/auth/passkeys/recovery/verify",
                        options["csrf_token"],
                        {"credential": Authenticator().registration(options["publicKey"])},
                    ).status_code
                else:
                    status = recovery_request(
                        first, ident, reissue=action == "recovery_reissue"
                    ).status_code
            assert status == 503
            after = snapshot(db)
            assert (before == after) == (fault == "audit"), "Business effects violated atomicity"
            if fault == "commit_ack":
                with db.session() as s:
                    assert (
                        s.execute(
                            text("SELECT count(*) FROM audit_events WHERE action=:a"), {"a": action}
                        ).scalar_one()
                        >= 1
                    )
                if action in ("recovery_start", "recovery_reissue"):
                    state = first.get(
                        "/api/v1/admin/accounts/" + ident + "/passkey-recovery"
                    ).json()
                    assert state["recovery_pending"] and "recovery_link" not in state
                    assert recovery_request(first, ident, reissue=True).status_code == 201


def test_recovery_preserves_existing_failure_cooldown(
    mfa: tuple[Settings, Database, str, str],
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        key = Authenticator()
        enroll(first, token, key)
        login_mfa(first, password, key)
        with closing(TestClient(first.app, base_url=ORIGIN)) as target:
            ident, _ = provision(first, target, password)
            assert call(target, "/auth/logout", csrf(target), {}).status_code == 204
            for _ in range(5):
                assert (
                    call(
                        target,
                        "/auth/login",
                        csrf(target),
                        {"login_id": "second.master", "password": "incorrect"},
                    ).status_code
                    == 401
                )
            assert (
                call(
                    target,
                    "/auth/login",
                    csrf(target),
                    {"login_id": "second.master", "password": password},
                ).status_code
                == 429
            )
            issued = recovery_request(first, ident)
            options = recovery_options(target, link_token(issued.json()["recovery_link"])).json()
            assert (
                call(
                    target,
                    "/auth/passkeys/recovery/verify",
                    options["csrf_token"],
                    {"credential": Authenticator().registration(options["publicKey"])},
                ).status_code
                == 204
            )
            assert (
                call(
                    target,
                    "/auth/login",
                    csrf(target),
                    {"login_id": "second.master", "password": password},
                ).status_code
                == 429
            )
