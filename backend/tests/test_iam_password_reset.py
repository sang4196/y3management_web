# ruff: noqa: F811
"""Purpose-bound password reset through actual provisioned MFA administrators."""

import hashlib
import json
import secrets
from contextlib import closing
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from tests.test_iam import ORIGIN, SyntheticSecret, csrf
from tests.test_iam_mfa import (  # noqa: F401
    Authenticator,
    begin,
    call,
    enroll,
    login_mfa,
    mfa,
    protect,
)
from tests.test_iam_mfa_management import add, keys, link_token, recovery_options, recovery_request
from tests.test_iam_mfa_management_races import provision
from y3management.application import create_app
from y3management.audit.infrastructure import Audit
from y3management.audit.public import Event
from y3management.config import Settings
from y3management.contracts import Rejected
from y3management.database import Database

pytestmark = pytest.mark.postgres


def reset_request(client: TestClient, ident: str, *, reissue: bool = False) -> Any:
    state = client.get("/api/v1/admin/accounts/" + ident + "/password-reset")
    assert state.status_code == 200
    data = state.json()
    return call(
        client,
        "/admin/accounts/" + ident + "/password-reset" + ("/reissue" if reissue else ""),
        csrf(client),
        {
            "expected_account_version": data["account_version"],
            "expected_generation": data["generation"],
            "identity_confirmed": True,
        },
    )


def complete(client: TestClient, raw: str, password: str) -> Any:
    return call(
        client,
        "/auth/password-reset/complete",
        csrf(client),
        {"reset_token": raw, "new_password": password},
    )


def fingerprint(db: Database) -> str:
    with db.session() as s:
        data = protect(
            {
                t: sorted(s.execute(text(f"SELECT row_to_json(t)::text FROM {t} t")).scalars())
                for t in (
                    "iam_accounts",
                    "iam_passkeys",
                    "iam_admin_grants",
                    "iam_login_ids",
                    "iam_reset_credentials",
                    "audit_events",
                )
            }
        )
        data["sessions"] = sorted(
            str(r) for r in s.execute(text("SELECT id,revoked,security_version FROM iam_sessions"))
        )
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


@pytest.mark.parametrize("master_target", [True, False])
def test_reset_preserves_keys_and_scope_revokes_password_sessions_and_proofs(
    mfa: tuple[Settings, Database, str, str],
    master_target: bool,
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        actor_key = Authenticator()
        enroll(first, token, actor_key)
        login_mfa(first, password, actor_key)
        with (
            closing(TestClient(first.app, base_url=ORIGIN)) as second,
            closing(TestClient(first.app, base_url=ORIGIN)) as third,
        ):
            if master_target:
                ident, key = provision(first, second, password)
                identifier = "second.master"
            else:
                branch = call(
                    first, "/admin/branches", csrf(first), {"code": "A", "name": "A"}
                ).json()
                issued = call(
                    first,
                    "/admin/accounts",
                    csrf(first),
                    {"login_id": "target.test", "branch_id": branch["id"]},
                ).json()
                ident, identifier, key = issued["account_id"], "target.test", Authenticator()
                enroll(second, link_token(issued["setup_link"]), key, password)
                login_mfa(second, password, key, identifier)
            another = Authenticator()
            add(second, another)
            login_mfa(third, password, another, identifier)
            before_keys, before_me = keys(second), second.get("/api/v1/auth/me").json()
            pending_add = call(second, "/auth/passkeys/options", csrf(second), {}).json()
            with closing(TestClient(first.app, base_url=ORIGIN)) as pending_client:
                pending_login = begin(pending_client, password, identifier)
                issued = reset_request(first, ident)
                assert issued.status_code == 201
                raw = link_token(issued.json()["reset_link"])
                assert second.get("/api/v1/auth/me").status_code == 401
                assert third.get("/api/v1/auth/me").status_code == 401
                assert (
                    call(
                        second,
                        "/auth/passkeys/verify",
                        pending_add["csrf_token"],
                        {"credential": Authenticator().registration(pending_add["publicKey"])},
                    ).status_code
                    == 401
                )
                assert (
                    call(
                        pending_client,
                        "/auth/login/passkey/verify",
                        pending_login["csrf_token"],
                        {"credential": key.assertion(pending_login["publicKey"])},
                    ).status_code
                    == 401
                )
            assert (
                call(
                    second,
                    "/auth/login",
                    csrf(second),
                    {"login_id": identifier, "password": password},
                ).status_code
                == 401
            )
            with db.session() as s:
                row = s.execute(
                    text(
                        "SELECT password_hash IS NULL,password_reset_pending,state FROM "
                        "iam_accounts WHERE id=:a"
                    ),
                    {"a": ident},
                ).one()
                assert tuple(row) == (True, True, "ACTIVE")
                ttl = s.execute(
                    text(
                        "SELECT EXTRACT(EPOCH FROM (r.expires_at-s.created_at)) FROM "
                        "iam_reset_credentials r JOIN iam_security_states s ON "
                        "s.id=r.id WHERE r.account_id=:a"
                    ),
                    {"a": ident},
                ).scalar_one()
                assert 1790 <= ttl <= 1800
            new_password = SyntheticSecret("새 비밀번호 검증 " + secrets.token_urlsafe(24))
            assert complete(second, raw, new_password).status_code == 204
            assert "__Host-y3-auth" not in second.cookies
            assert second.get("/api/v1/auth/me").status_code == 401
            assert complete(second, raw, new_password).status_code == 401
            login_mfa(second, new_password, key, identifier)
            assert keys(second) == before_keys
            assert second.get("/api/v1/auth/me").json() == before_me
            with db.session() as s:
                rows = s.execute(
                    text(
                        "SELECT before_reset_generation,after_reset_generation,"
                        "before_password_ready,after_password_ready FROM "
                        "audit_events WHERE action IN ('password_reset_start',"
                        "'password_reset_complete') ORDER BY happened_at"
                    )
                ).all()
                assert [tuple(r) for r in rows] == [(0, 1, True, False), (1, 1, False, True)]


@pytest.mark.parametrize(
    "case", ["reissue", "expiry", "purpose", "issuer_logout", "policy", "same_password", "overlap"]
)
def test_reset_authority_boundaries(mfa: tuple[Settings, Database, str, str], case: str) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        key = Authenticator()
        enroll(first, token, key)
        login_mfa(first, password, key)
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            ident, _ = provision(first, second, password)
            issued = reset_request(first, ident)
            assert issued.status_code == 201
            raw = link_token(issued.json()["reset_link"])
            if case == "expiry":
                with db.session() as s:
                    s.execute(
                        text(
                            "UPDATE iam_reset_credentials SET "
                            "expires_at=clock_timestamp() WHERE account_id=:a"
                        ),
                        {"a": ident},
                    )
                    s.commit()
                assert complete(second, raw, password).status_code == 401
                with db.session() as s:
                    assert s.execute(
                        text(
                            "SELECT password_reset_pending AND password_hash IS NULL FROM "
                            "iam_accounts WHERE id=:a"
                        ),
                        {"a": ident},
                    ).scalar_one()
                return
            if case == "reissue":
                replaced = reset_request(first, ident, reissue=True)
                assert replaced.status_code == 201
                assert complete(second, raw, password).status_code == 401
                raw = link_token(replaced.json()["reset_link"])
            if case == "purpose":
                assert recovery_options(second, raw).status_code == 401
                assert (
                    call(
                        second,
                        "/auth/passkeys/enrollment/options",
                        csrf(second),
                        {"setup_token": raw, "new_password": password},
                    ).status_code
                    == 400
                )
            if case == "issuer_logout":
                assert call(first, "/auth/logout", csrf(first), {}).status_code == 204
            if case == "policy":
                assert complete(second, raw, "short").status_code == 422
            if case == "overlap":
                assert recovery_request(first, ident).status_code == 409
            # Existing password policy permits reuse: no new history/reuse prohibition.
            assert complete(second, raw, password).status_code == 204
            assert second.get("/api/v1/auth/me").status_code == 401
            if case == "overlap":
                # Both factors lost: restricted reset then recovery, no intermediate login.
                recovery = recovery_request(first, ident)
                assert recovery.status_code == 201
                assert reset_request(first, ident).status_code == 409
                options = recovery_options(
                    second, link_token(recovery.json()["recovery_link"])
                ).json()
                fresh = Authenticator()
                assert (
                    call(
                        second,
                        "/auth/passkeys/recovery/verify",
                        options["csrf_token"],
                        {"credential": fresh.registration(options["publicKey"])},
                    ).status_code
                    == 204
                )
                assert reset_request(first, ident).status_code == 201


@pytest.mark.parametrize("action", ["start", "reissue", "complete"])
@pytest.mark.parametrize("failure", ["audit", "ack"])
def test_reset_atomicity(
    mfa: tuple[Settings, Database, str, str],
    monkeypatch: pytest.MonkeyPatch,
    action: str,
    failure: str,
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        key = Authenticator()
        enroll(first, token, key)
        login_mfa(first, password, key)
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            ident, _ = provision(first, second, password)
            raw = SyntheticSecret("")
            if action != "start":
                raw = link_token(reset_request(first, ident).json()["reset_link"])
            # Prepare request outside fault injection so activity/status read commits cannot fail.
            nonce = csrf(second if action == "complete" else first)
            state = first.get("/api/v1/admin/accounts/" + ident + "/password-reset").json()
            before = fingerprint(db)
            original, commit = Audit.append, Session.commit

            def append(adapter: Audit, event: Event) -> None:
                if event.action == "password_reset_" + action:
                    if failure == "audit":
                        raise Rejected(503, "unavailable")
                    adapter.s.info["reset_ack"] = True
                original(adapter, event)

            def committed(s: Session) -> None:
                commit(s)
                if s.info.pop("reset_ack", False):
                    raise OperationalError(
                        "synthetic commit acknowledgement loss", {}, RuntimeError("ack lost")
                    )

            with monkeypatch.context() as patch:
                patch.setattr(Audit, "append", append)
                patch.setattr(Session, "commit", committed)
                if action == "complete":
                    response = call(
                        second,
                        "/auth/password-reset/complete",
                        nonce,
                        {"reset_token": raw, "new_password": password},
                    )
                else:
                    response = call(
                        first,
                        "/admin/accounts/"
                        + ident
                        + "/password-reset"
                        + ("/reissue" if action == "reissue" else ""),
                        nonce,
                        {
                            "expected_account_version": state["account_version"],
                            "expected_generation": state["generation"],
                            "identity_confirmed": True,
                        },
                    )
            assert response.status_code == 503
            if failure == "audit":
                assert fingerprint(db) == before
            else:
                assert response.json()["detail"] == "commit_outcome_unknown"
                with db.session() as s:
                    assert (
                        s.execute(
                            text("SELECT count(*) FROM audit_events WHERE action=:x"),
                            {"x": "password_reset_" + action},
                        ).scalar_one()
                        == 1
                    )
                    assert s.execute(
                        text("SELECT password_reset_pending FROM iam_accounts WHERE id=:a"),
                        {"a": ident},
                    ).scalar_one() == (action != "complete")
