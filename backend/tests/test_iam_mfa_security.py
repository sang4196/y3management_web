# ruff: noqa: F811
"""MFA failure budgets, final authorization, rollback and replay regressions."""

from contextlib import closing
from dataclasses import replace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.test_iam import ORIGIN, SyntheticSecret, csrf
from tests.test_iam_mfa import Authenticator, begin, call, enroll, login_mfa, mfa  # noqa: F401
from y3management.application import create_app
from y3management.audit.infrastructure import Audit
from y3management.audit.public import Event
from y3management.config import Settings
from y3management.contracts import Rejected
from y3management.database import Database
from y3management.iam.mfa import MFA
from y3management.iam.public import RegistrationProof, Reservation
from y3management.iam.security import Security

pytestmark = pytest.mark.postgres


def test_c2_shared_budget_success_does_not_clear(mfa: tuple[Settings, Database, str, str]) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        key = Authenticator()
        enroll(client, token, key)
        for _ in range(2):
            assert (
                call(
                    client,
                    "/auth/login",
                    csrf(client),
                    {"login_id": "master.test", "password": "wrong"},
                ).status_code
                == 401
            )
        login_mfa(client, password, key)
        assert call(client, "/auth/logout", csrf(client), {}).status_code == 204
        for _ in range(3):
            result = begin(client, password)
            assert (
                call(
                    client,
                    "/auth/login/passkey/verify",
                    result["csrf_token"],
                    {"credential": key.assertion(result["publicKey"], uv=False)},
                ).status_code
                == 401
            )
        assert (
            call(
                client,
                "/auth/login",
                csrf(client),
                {"login_id": "master.test", "password": password},
            ).status_code
            == 429
        )
        with db.session() as s:
            assert (
                s.execute(
                    text("SELECT count(*) FROM iam_attempts WHERE outcome='failure'")
                ).scalar_one()
                == 5
            )


def test_waiting_is_bounded_and_counts_toward_admission(
    mfa: tuple[Settings, Database, str, str],
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        enroll(client, token, Authenticator())
        for _ in range(5):
            begin(client, password)
        assert (
            call(
                client,
                "/auth/login",
                csrf(client),
                {"login_id": "master.test", "password": password},
            ).status_code
            == 429
        )
        with db.session() as s:
            assert (
                s.execute(
                    text(
                        "SELECT count(*) FROM iam_attempts WHERE stage='waiting' "
                        "AND outcome='pending' "
                        "AND lease_until>clock_timestamp()+interval '4 minutes'"
                    )
                ).scalar_one()
                == 5
            )
            s.execute(
                text("UPDATE iam_attempts SET lease_until=clock_timestamp()-interval '1 second'")
            )
            s.commit()
        assert (
            call(
                client,
                "/auth/login",
                csrf(client),
                {"login_id": "master.test", "password": password},
            ).status_code
            == 429
        )
        with db.session() as s:
            assert (
                s.execute(
                    text("SELECT count(*) FROM iam_attempts WHERE outcome='failure'")
                ).scalar_one()
                == 5
            )


@pytest.mark.parametrize("failure", ["audit", "finish", "finish_ack", "cleanup"])
def test_failed_final_delivery_never_returns_cookie(
    mfa: tuple[Settings, Database, str, str], monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        key = Authenticator()
        enroll(client, token, key)
        login_mfa(client, password, key)
        preserved = SyntheticSecret(client.cookies.get("__Host-y3-auth") or "")
        with db.session() as s:
            original_id = s.execute(text("SELECT id FROM iam_sessions")).scalar_one()
        client.cookies.clear()
        result = begin(client, password)
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

        def fail_cleanup(adapter: MFA, sid: Any) -> None:
            raise Rejected(503, "unavailable")

        with monkeypatch.context() as patch:
            if failure == "audit":
                patch.setattr(Audit, "append", audit)
            else:
                patch.setattr(Security, "finish", fail_finish)
            if failure == "cleanup":
                patch.setattr(MFA, "revoke_undelivered", fail_cleanup)
            response = call(
                client,
                "/auth/login/passkey/verify",
                result["csrf_token"],
                {"credential": key.assertion(result["publicKey"])},
            )
        assert response.status_code == 503
        assert "__Host-y3-auth" not in client.cookies
        with db.session() as s:
            sessions = s.execute(
                text("SELECT id,revoked FROM iam_sessions WHERE id<>:id"), {"id": original_id}
            ).all()
            assert len(sessions) == (0 if failure == "audit" else 1)
            if failure not in ("audit", "cleanup"):
                assert sessions[0].revoked
            if failure == "cleanup":
                assert response.json()["detail"] == "mfa_cleanup_deferred"
                # Reproduce retained undelivered state, then clean only this owned run's session.
                s.execute(
                    text("UPDATE iam_sessions SET revoked=true WHERE id=:id"),
                    {"id": sessions[0].id},
                )
                s.commit()
        assert (
            client.get(
                "/api/v1/auth/me", headers={"Cookie": "__Host-y3-auth=" + preserved}
            ).status_code
            == 200
        )
        assert (
            call(
                client,
                "/auth/login/passkey/verify",
                result["csrf_token"],
                {"credential": key.assertion(result["publicKey"])},
            ).status_code
            == 401
        )


@pytest.mark.parametrize("where", ["start", "final"])
def test_actual_budget_key_binding(
    mfa: tuple[Settings, Database, str, str], monkeypatch: pytest.MonkeyPatch, where: str
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        key = Authenticator()
        enroll(client, token, key)
        if where == "start":
            reserve = Security.reserve

            def altered(adapter: Security, identifier: str) -> Reservation:
                normal = reserve(adapter, identifier)
                foreign = reserve(adapter, "unassigned.test")
                return replace(
                    foreign, account_id=normal.account_id, security_version=normal.security_version
                )

            with monkeypatch.context() as patch:
                patch.setattr(Security, "reserve", altered)
                result = call(
                    client,
                    "/auth/login",
                    csrf(client),
                    {"login_id": "master.test", "password": password},
                )
        else:
            options = begin(client, password)
            with db.session() as s:
                s.execute(text("UPDATE iam_accounts SET login_budget_key=:k"), {"k": bytes(32)})
                s.commit()
            result = call(
                client,
                "/auth/login/passkey/verify",
                options["csrf_token"],
                {"credential": key.assertion(options["publicKey"])},
            )
        assert result.status_code == 503
        with db.session() as s:
            assert s.execute(text("SELECT count(*) FROM iam_sessions")).scalar_one() == 0


@pytest.mark.parametrize("expiry", ["idle", "absolute", "revoked"])
def test_add_key_final_expiry_and_purpose_binding(
    mfa: tuple[Settings, Database, str, str], monkeypatch: pytest.MonkeyPatch, expiry: str
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        key = Authenticator()
        enroll(client, token, key)
        login_mfa(client, password, key)
        options = call(client, "/auth/passkeys/options", csrf(client), {}).json()
        payload = Authenticator().registration(options["publicKey"])
        assert (
            call(
                client,
                "/auth/passkeys/enrollment/verify",
                options["csrf_token"],
                {"credential": payload},
            ).status_code
            == 401
        )
        from tests.test_iam_mfa_install import fingerprint

        verify = MFA.verify_registration
        expected = ""

        def slow_verify(
            adapter: MFA, raw: str | None, nonce: str | None, body: str
        ) -> RegistrationProof:
            nonlocal expected
            proof = verify(adapter, raw, nonce, body)
            # A separate connection changes ONLY the actor's session after crypto verification.
            # The account and 5-minute ceremony remain valid in all three cases.
            with db.session() as session:
                if expiry == "idle":
                    session.execute(
                        text(
                            "UPDATE iam_sessions SET "
                            "created_at=clock_timestamp()-interval '32 minutes',"
                            "last_activity=clock_timestamp()-interval '31 minutes'"
                        )
                    )
                elif expiry == "absolute":
                    session.execute(
                        text(
                            "WITH shifted AS (UPDATE iam_security_states SET "
                            "expires_at=clock_timestamp()-interval '1 second' "
                            "WHERE kind='session_slot' RETURNING id,expires_at) "
                            "UPDATE iam_sessions s SET expires_at=shifted.expires_at,"
                            "created_at=shifted.expires_at-interval '8 hours',"
                            "last_activity=shifted.expires_at-interval '1 minute' "
                            "FROM shifted WHERE s.id=shifted.id"
                        )
                    )
                else:
                    session.execute(text("UPDATE iam_sessions SET revoked=true"))
                session.commit()
            expected = fingerprint(db)
            return proof

        with monkeypatch.context() as patch:
            patch.setattr(MFA, "verify_registration", slow_verify)
            assert (
                call(
                    client, "/auth/passkeys/verify", options["csrf_token"], {"credential": payload}
                ).status_code
                == 401
            )
        assert expected and fingerprint(db) == expected
        with db.session() as s:
            assert (
                s.execute(
                    text(
                        "SELECT count(*) FROM iam_mfa_contexts "
                        "WHERE purpose='add' AND NOT consumed AND expires_at>clock_timestamp()"
                    )
                ).scalar_one()
                == 1
            )


def test_registration_replay_and_uv(mfa: tuple[Settings, Database, str, str]) -> None:
    settings, db, _, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        options = call(
            client, "/auth/passkeys/enrollment/options", csrf(client), {"setup_token": token}
        ).json()
        key = Authenticator()
        assert (
            call(
                client,
                "/auth/passkeys/enrollment/verify",
                options["csrf_token"],
                {"credential": key.registration(options["publicKey"], uv=False)},
            ).status_code
            == 401
        )
        raw_cookie = SyntheticSecret(client.cookies.get("__Host-y3-ceremony") or "")
        payload = key.registration(options["publicKey"])
        assert (
            call(
                client,
                "/auth/passkeys/enrollment/verify",
                options["csrf_token"],
                {"credential": payload},
            ).status_code
            == 204
        )
        # Replay the original cookie rather than a cleared browser cookie.
        client.cookies.set("__Host-y3-ceremony", raw_cookie or "")
        assert (
            call(
                client,
                "/auth/passkeys/enrollment/verify",
                options["csrf_token"],
                {"credential": payload},
            ).status_code
            == 401
        )


def test_onboarding_reissue_revokes_staged_password(
    mfa: tuple[Settings, Database, str, str],
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as master:
        key = Authenticator()
        enroll(master, token, key)
        login_mfa(master, password, key)
        branch = call(master, "/admin/branches", csrf(master), {"code": "A", "name": "A"}).json()
        issued = call(
            master,
            "/admin/accounts",
            csrf(master),
            {"login_id": "branch.test", "branch_id": branch["id"]},
        ).json()
        with closing(TestClient(master.app, base_url=ORIGIN)) as client:
            result = call(
                client,
                "/auth/passkeys/enrollment/options",
                csrf(client),
                {"setup_token": issued["setup_link"].split("#token=")[1], "new_password": password},
            ).json()
            with db.session() as s:
                assert s.execute(
                    text(
                        "SELECT password_hash IS NULL FROM iam_accounts "
                        "WHERE login_id='branch.test'"
                    )
                ).scalar_one()
            assert (
                call(
                    master,
                    "/admin/accounts/" + issued["account_id"] + "/activation",
                    csrf(master),
                    {"expected_version": issued["version"]},
                ).status_code
                == 201
            )
            assert (
                call(
                    client,
                    "/auth/passkeys/enrollment/verify",
                    result["csrf_token"],
                    {"credential": Authenticator().registration(result["publicKey"])},
                ).status_code
                == 401
            )
            assert client.get("/api/v1/auth/me").status_code == 401


def test_failed_login_audit_principal_and_unknown(mfa: tuple[Settings, Database, str, str]) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        key = Authenticator()
        enroll(client, token, key)
        for name in ("master.test", "unknown.test"):
            assert (
                call(
                    client, "/auth/login", csrf(client), {"login_id": name, "password": "wrong"}
                ).status_code
                == 401
            )
        result = begin(client, password)
        assert (
            call(
                client,
                "/auth/login/passkey/verify",
                result["csrf_token"],
                {"credential": key.assertion(result["publicKey"], uv=False)},
            ).status_code
            == 401
        )
        with db.session() as s:
            account = s.execute(text("SELECT id,organization_id FROM iam_accounts")).one()
            events = s.execute(
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


def test_no_key_or_password_only_session_fallback(mfa: tuple[Settings, Database, str, str]) -> None:
    from y3management.uow import UnitOfWork
    from y3management.use_cases import Service

    settings, db, password, _ = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        assert (
            call(
                client,
                "/auth/login",
                csrf(client),
                {"login_id": "master.test", "password": password},
            ).status_code
            == 401
        )
        legacy = Service(UnitOfWork(db, settings.model_copy(update={"iam_mode": "s1_password"})))
        nonce, preauth = legacy.csrf(None, None)
        weak = SyntheticSecret(legacy.login("master.test", password, preauth, nonce, None))
        assert (
            client.get("/api/v1/auth/me", headers={"Cookie": "__Host-y3-auth=" + weak}).status_code
            == 401
        )
        assert (
            client.get("/api/v1/branches", headers={"Cookie": "__Host-y3-auth=" + weak}).status_code
            == 401
        )
        with db.session() as s:
            assert (
                s.execute(
                    text("SELECT count(*) FROM iam_sessions WHERE assurance='password_uv'")
                ).scalar_one()
                == 0
            )


def test_bounded_context_capacity_and_orphan_gc(mfa: tuple[Settings, Database, str, str]) -> None:
    from y3management.uow import UnitOfWork

    settings, db, _, _ = mfa
    limited = UnitOfWork(db, settings.model_copy(update={"security_state_capacity": 64}))
    for _ in range(63):
        with limited.open() as w:
            w.security.allocate("mfa")
    with pytest.raises(Rejected) as rejected, limited.open() as w:
        w.security.allocate("mfa")
    assert rejected.value.status == 503
    with db.session() as s:
        assert s.execute(text("SELECT count(*) FROM iam_mfa_contexts")).scalar_one() == 1
        s.execute(
            text(
                "UPDATE iam_security_states SET created_at=clock_timestamp()-interval '31 seconds'"
            )
        )
        s.commit()
    with limited.open() as w:
        w.security.allocate("mfa")
    with db.session() as s:
        assert s.execute(text("SELECT count(*) FROM iam_mfa_contexts")).scalar_one() == 1
        assert (
            s.execute(
                text("SELECT count(*) FROM iam_security_states WHERE kind='mfa'")
            ).scalar_one()
            == 2
        )


@pytest.mark.parametrize("action", ["setup_complete", "passkey_register"])
def test_setup_key_and_audits_roll_back_together(
    mfa: tuple[Settings, Database, str, str], monkeypatch: pytest.MonkeyPatch, action: str
) -> None:
    from tests.test_iam_mfa_install import fingerprint

    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as master:
        key = Authenticator()
        enroll(master, token, key)
        login_mfa(master, password, key)
        branch = call(master, "/admin/branches", csrf(master), {"code": "A", "name": "A"}).json()
        issued = call(
            master,
            "/admin/accounts",
            csrf(master),
            {"login_id": "branch.test", "branch_id": branch["id"]},
        ).json()
        with closing(TestClient(master.app, base_url=ORIGIN)) as client:
            options = call(
                client,
                "/auth/passkeys/enrollment/options",
                csrf(client),
                {"setup_token": issued["setup_link"].split("#token=")[1], "new_password": password},
            ).json()
            payload = Authenticator().registration(options["publicKey"])
            before = fingerprint(db)
            append = Audit.append

            def fail(adapter: Audit, event: Event) -> None:
                if event.action == action:
                    raise Rejected(503, "unavailable")
                append(adapter, event)

            with monkeypatch.context() as patch:
                patch.setattr(Audit, "append", fail)
                assert (
                    call(
                        client,
                        "/auth/passkeys/enrollment/verify",
                        options["csrf_token"],
                        {"credential": payload},
                    ).status_code
                    == 503
                )
            assert fingerprint(db) == before
            assert (
                call(
                    client,
                    "/auth/passkeys/enrollment/verify",
                    options["csrf_token"],
                    {"credential": payload},
                ).status_code
                == 204
            )


def test_synced_zero_counter_and_backup_state(mfa: tuple[Settings, Database, str, str]) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        key = Authenticator()
        result = call(
            client, "/auth/passkeys/enrollment/options", csrf(client), {"setup_token": token}
        ).json()
        assert (
            call(
                client,
                "/auth/passkeys/enrollment/verify",
                result["csrf_token"],
                {"credential": key.registration(result["publicKey"], flags=0x4D)},
            ).status_code
            == 204
        )
        for flags in (0x1D, 0x0D):
            options = begin(client, password)
            key.counter = -1  # A synced test authenticator reporting zero.
            assert (
                call(
                    client,
                    "/auth/login/passkey/verify",
                    options["csrf_token"],
                    {"credential": key.assertion(options["publicKey"], flags=flags)},
                ).status_code
                == 204
            )
            with db.session() as s:
                row = s.execute(
                    text("SELECT sign_count,device_type,backed_up FROM iam_passkeys")
                ).one()
                assert tuple(row) == (0, "multi_device", bool(flags & 0x10))
            assert call(client, "/auth/logout", csrf(client), {}).status_code == 204


def test_nonadvancing_counter_and_duplicate_key_rejected(
    mfa: tuple[Settings, Database, str, str],
) -> None:
    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        key = Authenticator()
        enroll(client, token, key)
        login_mfa(client, password, key)
        options = call(client, "/auth/passkeys/options", csrf(client), {}).json()
        assert (
            call(
                client,
                "/auth/passkeys/verify",
                options["csrf_token"],
                {"credential": key.registration(options["publicKey"])},
            ).status_code
            == 409
        )
        assert call(client, "/auth/logout", csrf(client), {}).status_code == 204
        options = begin(client, password)
        key.counter = 0
        assert (
            call(
                client,
                "/auth/login/passkey/verify",
                options["csrf_token"],
                {"credential": key.assertion(options["publicKey"])},
            ).status_code
            == 401
        )
        with db.session() as s:
            assert s.execute(text("SELECT sign_count FROM iam_passkeys")).scalar_one() == 1


def test_reverse_purpose_other_actor_and_real_credential_owner(
    mfa: tuple[Settings, Database, str, str],
) -> None:
    from tests.test_iam_mfa_install import fingerprint

    settings, db, password, token = mfa
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as master:
        master_key = Authenticator()
        enroll(master, token, master_key)
        login_mfa(master, password, master_key)
        branch = call(master, "/admin/branches", csrf(master), {"code": "A", "name": "A"}).json()
        issued = call(
            master,
            "/admin/accounts",
            csrf(master),
            {"login_id": "branch.test", "branch_id": branch["id"]},
        ).json()
        with closing(TestClient(master.app, base_url=ORIGIN)) as client:
            options = call(
                client,
                "/auth/passkeys/enrollment/options",
                csrf(client),
                {"setup_token": issued["setup_link"].split("#token=")[1], "new_password": password},
            ).json()
            key = Authenticator()
            payload = key.registration(options["publicKey"])
            # A normal Master cannot turn another account's setup into SELF additional registration.
            header = SyntheticSecret(
                "__Host-y3-auth="
                + str(master.cookies.get("__Host-y3-auth"))
                + "; __Host-y3-ceremony="
                + str(client.cookies.get("__Host-y3-ceremony"))
            )
            before = fingerprint(db)
            assert (
                master.post(
                    "/api/v1/auth/passkeys/verify",
                    json={"credential": payload},
                    headers={
                        "Origin": ORIGIN,
                        "X-CSRF-Token": options["csrf_token"],
                        "Cookie": header,
                    },
                ).status_code
                == 401
            )
            assert fingerprint(db) == before
            assert (
                call(
                    client,
                    "/auth/passkeys/enrollment/verify",
                    options["csrf_token"],
                    {"credential": payload},
                ).status_code
                == 204
            )
            login_mfa(client, password, key, "branch.test")
            options = call(master, "/auth/passkeys/options", csrf(master), {}).json()
            payload = Authenticator().registration(options["publicKey"])
            header = SyntheticSecret(
                "__Host-y3-auth="
                + str(client.cookies.get("__Host-y3-auth"))
                + "; __Host-y3-ceremony="
                + str(master.cookies.get("__Host-y3-ceremony"))
            )
            before = fingerprint(db)
            assert (
                client.post(
                    "/api/v1/auth/passkeys/verify",
                    json={"credential": payload},
                    headers={
                        "Origin": ORIGIN,
                        "X-CSRF-Token": options["csrf_token"],
                        "Cookie": header,
                    },
                ).status_code
                == 401
            )
            assert fingerprint(db) == before
            assert call(client, "/auth/logout", csrf(client), {}).status_code == 204
            options = begin(client, password, "branch.test")
            assert (
                call(
                    client,
                    "/auth/login/passkey/verify",
                    options["csrf_token"],
                    {"credential": master_key.assertion(options["publicKey"], user=key.user)},
                ).status_code
                == 401
            )
