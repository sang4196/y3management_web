# ruff: noqa: F811
"""Operator public provisioning and independent work scope against the owned database."""

from contextlib import closing
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.password_helpers import (  # noqa: F401
    activate,
    call,
    link_token,
    login_password,
    password_app,
    reset_request,
)
from tests.password_helpers import complete as reset_complete
from tests.test_account_lifecycle import mutate
from tests.test_iam import ORIGIN, csrf
from tests.test_iam_trainer import TrainerScene, source, trainer  # noqa: F401
from tests.test_iam_trainer_roles import change
from tests.test_iam_trainer_roles_security import link
from tests.test_workforce import scene  # noqa: F401
from tests.test_workforce_integrity import branch_actor
from tests.test_workforce_state import change as change_state
from tests.test_workforce_state import request as state_request
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres
BASE = "/admin/operator-accounts"


def source_deadline_sql(interval: str) -> str:
    # The source and its credential slot deliberately share one immutable allocation deadline.
    assert interval in ("0 seconds", "3 seconds")
    return f"""WITH parent AS (
        UPDATE iam_security_states SET expires_at=clock_timestamp()+interval '{interval}'
        WHERE id IN (SELECT id FROM iam_operator_setup_credentials)
        RETURNING id,expires_at)
        UPDATE iam_operator_setup_credentials c SET expires_at=p.expires_at
        FROM parent p WHERE c.id=p.id RETURNING c.expires_at"""


def test_current_operator_onboarding(trainer: TrainerScene) -> None:
    t = trainer
    master, recipient = t.base.client, t.recipient
    with closing(branch_actor(t.base, t.password)) as admin:

        def issue(branch: str, identifier: str) -> Any:
            return call(admin, BASE, csrf(admin), {"branch_id": branch, "login_id": identifier})

        assert issue(str(uuid4()), t.login).status_code == 404
        issued = issue(t.base.branch, t.login)
        old = source(issued)
        ident = issued.json()["account_id"]
        path = BASE + "/" + ident
        with t.base.db.engine.begin() as db:
            db.execute(
                text(
                    "UPDATE organization_branches SET active=false, "
                    "row_version=row_version+1 "
                    "WHERE id=:b"
                ),
                {"b": t.base.branch},
            )
        assert issue(t.base.branch, "other.operator").status_code == 409
        current = call(admin, BASE + "/lookup", csrf(admin), {"login_id": t.login}).json()
        assert current["version"] == 1 and "setup_link" not in current
        replacement = source(
            call(master, path + "/initial-setup", csrf(master), {"expected_version": 1})
        )
        assert (
            call(admin, path + "/initial-setup", csrf(admin), {"expected_version": 1}).status_code
            == 409
        )

        def complete(token: str) -> int:
            return int(
                call(
                    recipient,
                    "/auth/operator-credentials/complete",
                    csrf(recipient),
                    {"setup_token": token, "new_password": t.password},
                ).status_code
            )

        assert complete(old) == 400
        assert t.complete(replacement).status_code == 400
        assert complete(replacement) == 204
        assert complete(replacement) == 400
        assert recipient.get("/api/v1/auth/me").status_code == 401
        assert t.signin().status_code == 204
        assert t.signin().status_code == 409
        profile = recipient.get("/api/v1/auth/me").json()
        assert profile["roles"] == [{"role": "OPERATOR", "branch_id": t.base.branch}]
        assert profile["capabilities"] == []
        assert recipient.get("/api/v1/branches").status_code == 403
        assert recipient.get("/api/v1/operator/branches/" + t.base.branch).status_code == 200
        assert recipient.get("/api/v1/operator/branches/" + str(uuid4())).status_code == 404
        assert (
            call(
                recipient,
                BASE,
                csrf(recipient),
                {"branch_id": t.base.branch, "login_id": "invalid.operator"},
            ).status_code
            == 403
        )
        assert change(t, link(t, ident, t.login)).status_code == 200
        assert recipient.get("/api/v1/auth/me").status_code == 401
        assert t.signin().status_code == 204
        assert {r["role"] for r in recipient.get("/api/v1/auth/me").json()["roles"]} == {
            "OPERATOR",
            "TRAINER",
        }
        assert change_state(t, state_request(t, False)).status_code == 200
        assert recipient.get("/api/v1/auth/me").json()["roles"] == profile["roles"]
        new = t.password + " changed"
        assert (
            call(
                recipient,
                "/auth/password",
                csrf(recipient),
                {"current_password": t.password, "new_password": new},
            ).status_code
            == 204
        )
        assert t.signin(password=new).status_code == 204
        assert call(recipient, "/auth/logout", csrf(recipient), {}).status_code == 204

        pending_reset = reset_request(master, ident)
        assert pending_reset.status_code == 201
        assert (
            reset_complete(
                recipient, link_token(pending_reset.json()["reset_link"]), t.password
            ).status_code
            == 204
        )
        assert t.signin().status_code == 204
        life = master.get("/api/v1/admin/account-lifecycle/" + ident).json()
        assert life["admin_scope"] is None and life["operator_scope"]["branch_id"] == t.base.branch
        disabled = mutate(t, life, "status", status="DISABLED")
        assert disabled.status_code == 200
        assert recipient.get("/api/v1/auth/me").status_code == 401
        assert (
            call(
                admin,
                path + "/initial-setup",
                csrf(admin),
                {"expected_version": disabled.json()["version"]},
            ).status_code
            == 409
        )
        restored = mutate(t, disabled.json(), "restore")
        assert restored.status_code == 200 and restored.json()["state"] == "ACTIVE"
        assert t.signin().status_code == 204


def test_two_scopes_source_gc_and_schema_loss_guard(
    trainer: TrainerScene, password_app: tuple[Settings, Database, str]
) -> None:
    from tests.legacy_helpers import assert_revision_loss_guard
    from tests.test_iam_trainer_roles import body
    from y3management.uow import UnitOfWork

    t = trainer
    master = t.base.client
    work_branch = call(
        master, "/admin/branches", csrf(master), {"code": "OP", "name": "운영 지점"}
    ).json()["id"]
    with (
        closing(branch_actor(t.base, t.password)) as home_admin,
        closing(TestClient(master.app, base_url=ORIGIN)) as work_admin,
    ):
        admin = call(
            master,
            "/admin/accounts",
            csrf(master),
            {"login_id": "operator.branch.admin", "branch_id": work_branch},
        )
        activate(work_admin, source(admin), t.password)
        login_password(work_admin, t.password, "operator.branch.admin")
        issued = call(master, BASE, csrf(master), {"login_id": t.login, "branch_id": work_branch})
        original = source(issued)
        ident = issued.json()["account_id"]
        path = BASE + "/" + ident
        assert home_admin.get("/api/v1" + path).status_code == 404
        assert (
            call(
                home_admin, path + "/initial-setup", csrf(home_admin), {"expected_version": 1}
            ).status_code
            == 404
        )
        assert (
            call(
                work_admin, "/admin/accounts/lookup", csrf(work_admin), {"login_id": t.login}
            ).status_code
            == 403
        )
        assert_revision_loss_guard(
            t.base.db, "0016_operator_onboarding.py", "OPERATOR_HISTORY_PRESENT"
        )
        with t.base.db.engine.begin() as db:
            db.execute(
                text(
                    "UPDATE organization_branches SET active=false,row_version=row_version+1 "
                    "WHERE id=:b"
                ),
                {"b": work_branch},
            )
            slot = db.execute(
                text("SELECT id FROM iam_operator_setup_credentials WHERE account_id=:a"),
                {"a": ident},
            ).scalar_one()
            db.execute(
                text(
                    "UPDATE iam_security_states SET created_at=created_at-interval '1 minute' "
                    "WHERE id=:i"
                ),
                {"i": slot},
            )
        uow = UnitOfWork(t.base.db, password_app[0])
        with uow.open() as w:
            w.security.release(slot)
        assert (
            call(
                t.recipient,
                "/auth/operator-credentials/complete",
                csrf(t.recipient),
                {"setup_token": original, "new_password": t.password},
            ).status_code
            == 204
        )
        with t.base.db.session() as holder:
            holder.execute(
                text("SELECT id FROM iam_operator_setup_credentials WHERE id=:i FOR UPDATE"),
                {"i": slot},
            ).one()
            with uow.open() as w:
                w.security.allocate("credential")
            assert holder.execute(
                text("SELECT id FROM iam_security_states WHERE id=:i"), {"i": slot}
            ).first()
        with uow.open() as w:
            w.security.release(slot)
        with t.base.db.session() as db:
            assert not db.execute(
                text("SELECT id FROM iam_security_states WHERE id=:i"), {"i": slot}
            ).first()
            assert (
                db.execute(text("SELECT count(*) FROM audit_operator_account_events")).scalar_one()
                == 2
            )
        request = link(t, ident, t.login)
        role_path = "/admin/trainers/" + t.trainer + "/role"
        assert call(work_admin, role_path, csrf(work_admin), request).status_code == 404
        assert call(home_admin, role_path, csrf(home_admin), request).status_code == 200
        assert t.signin().status_code == 204
        roles = t.recipient.get("/api/v1/auth/me").json()["roles"]
        assert roles == [
            {"role": "OPERATOR", "branch_id": work_branch},
            {"role": "TRAINER", "trainer_id": t.trainer, "home_branch_id": t.base.branch},
        ]
        with closing(TestClient(master.app, base_url=ORIGIN)) as second:
            assert t.signin(second).status_code == 204
            assert change_state(t, state_request(t, False)).status_code == 200
            for client in (t.recipient, second):
                assert client.get("/api/v1/auth/me").json()["roles"] == roles[:1]
            assert change(t, body(t, False)).status_code == 200
            for client in (t.recipient, second):
                assert client.get("/api/v1/auth/me").status_code == 401
        assert t.signin().status_code == 204
        with t.base.db.engine.begin() as db:
            db.execute(
                text(
                    "UPDATE iam_operator_grants SET granted=false,version=version+1 "
                    "WHERE account_id=:a"
                ),
                {"a": ident},
            )
        assert t.recipient.get("/api/v1/auth/me").status_code == 401
        assert t.signin().status_code == 401


def test_operator_audit_and_proof_rollback(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch
) -> None:
    from y3management.audit.infrastructure import Audit
    from y3management.audit.public import OperatorAccountEvent
    from y3management.iam.passwords import Passwords

    t = trainer
    master = t.base.client
    issued = call(master, BASE, csrf(master), {"login_id": t.login, "branch_id": t.base.branch})
    token = source(issued)
    ident = issued.json()["account_id"]
    path = BASE + "/" + ident
    append = Audit.append_operator

    def invalidate(adapter: Audit, event: OperatorAccountEvent) -> None:
        append(adapter, event)
        if event.kind == "setup_complete":
            adapter.s.execute(text(source_deadline_sql("0 seconds")))
        if event.kind == "login":
            adapter.s.execute(
                text("UPDATE iam_accounts SET password_hash='different' WHERE id=:a"), {"a": ident}
            )

    def complete() -> int:
        return int(
            call(
                t.recipient,
                "/auth/operator-credentials/complete",
                csrf(t.recipient),
                {"setup_token": token, "new_password": t.password},
            ).status_code
        )

    with monkeypatch.context() as patch:
        patch.setattr(Audit, "append_operator", invalidate)
        assert complete() == 400
    assert master.get("/api/v1" + path).json()["version"] == 1
    assert complete() == 204
    with monkeypatch.context() as patch:
        patch.setattr(Audit, "append_operator", invalidate)
        assert t.signin().status_code == 401
    verify = Passwords.verify

    def aba(passwords: Passwords, value: str, encoded: str | None) -> tuple[bool, str | None]:
        result = verify(passwords, value, encoded)
        with t.base.db.engine.begin() as db:
            for granted in (False, True):
                db.execute(
                    text(
                        "UPDATE iam_operator_grants SET granted=:g,version=version+1 "
                        "WHERE account_id=:a"
                    ),
                    {"g": granted, "a": ident},
                )
        return result

    with monkeypatch.context() as patch:
        patch.setattr(Passwords, "verify", aba)
        assert t.signin().status_code == 401

    def rehash(passwords: Passwords, value: str, encoded: str | None) -> tuple[bool, str | None]:
        valid, _ = verify(passwords, value, encoded)
        return valid, passwords.create(value, t.login)

    with monkeypatch.context() as patch:
        patch.setattr(Passwords, "verify", rehash)
        assert t.signin().status_code == 204


@pytest.mark.parametrize("flow", ["issue", "complete"])
def test_operator_required_audit_lock_crosses_original_deadline(
    trainer: TrainerScene, flow: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from time import monotonic

    from tests.test_admin_actor_clock import expire_soon
    from tests.test_workforce_integrity import wait_for_owned_block
    from y3management.audit.infrastructure import Audit
    from y3management.audit.public import OperatorAccountEvent

    t = trainer
    db = t.base.db
    master = t.base.client
    actor_id = master.get("/api/v1/auth/me").json()["account_id"]
    body = {"login_id": t.login, "branch_id": t.base.branch}
    client = master
    path = BASE
    if flow == "complete":
        token = source(call(master, BASE, csrf(master), body))
        path = "/auth/operator-credentials/complete"
        client = t.recipient
        body = {"setup_token": token, "new_password": t.password}
    nonce = csrf(client)
    if flow == "issue":
        expire_soon(db, actor_id, "idle")
    with db.engine.begin() as conn:
        if flow == "complete":
            deadline = conn.execute(text(source_deadline_sql("3 seconds"))).scalar_one()
        else:
            deadline = conn.execute(
                text("""SELECT last_activity+interval '30 minutes'
                FROM iam_sessions WHERE account_id=:a AND NOT revoked"""),
                {"a": actor_id},
            ).scalar_one()
    append = Audit.append_operator
    waiters: list[int] = []
    ready = Event()

    def wait_at_audit(adapter: Audit, event: OperatorAccountEvent) -> None:
        while True:
            remaining = (
                deadline - adapter.s.execute(text("SELECT clock_timestamp()")).scalar_one()
            ).total_seconds()
            if remaining <= 0.7:
                assert remaining > 0
                break
            adapter.s.execute(text("SELECT pg_sleep(0.05)"))
        waiters.append(adapter.s.execute(text("SELECT pg_backend_pid()")).scalar_one())
        ready.set()
        append(adapter, event)

    monkeypatch.setattr(Audit, "append_operator", wait_at_audit)
    with ThreadPoolExecutor(max_workers=1) as pool:
        with db.session() as holder:
            holder.execute(text("LOCK TABLE audit_operator_account_events IN SHARE MODE"))
            pid = holder.execute(text("SELECT pg_backend_pid()")).scalar_one()
            task = pool.submit(call, client, path, nonce, body)
            assert ready.wait(5)
            wait_for_owned_block(db, pid, waiters)
            assert holder.execute(text("SELECT clock_timestamp()")).scalar_one() < deadline
            limit = monotonic() + 2
            while holder.execute(text("SELECT clock_timestamp()")).scalar_one() < deadline:
                assert monotonic() < limit
                holder.execute(text("SELECT pg_sleep(0.02)"))
            assert (
                pid
                in holder.execute(
                    text("SELECT pg_blocking_pids(:p)"), {"p": waiters[0]}
                ).scalar_one()
            )
            assert not task.done()
        assert task.result(timeout=5).status_code == (401 if flow == "issue" else 400)
    with db.session() as reader:
        assert reader.execute(
            text("SELECT count(*) FROM audit_operator_account_events")
        ).scalar_one() == int(flow == "complete")
        assert reader.execute(text("SELECT count(*) FROM iam_operator_grants")).scalar_one() == int(
            flow == "complete"
        )
        if flow == "complete":
            assert (
                reader.execute(
                    text("SELECT consumed FROM iam_operator_setup_credentials")
                ).scalar_one()
                is False
            )
            assert (
                reader.execute(
                    text("SELECT state FROM iam_accounts WHERE login_id=:l"), {"l": t.login}
                ).scalar_one()
                == "PENDING_SETUP"
            )


def test_current_branch_admin_after_issuer_moves_and_expired_gc(
    trainer: TrainerScene,
    password_app: tuple[Settings, Database, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from sqlalchemy.exc import IntegrityError

    from y3management.audit.infrastructure import Audit
    from y3management.audit.public import OperatorAccountEvent
    from y3management.uow import UnitOfWork

    t = trainer
    db = t.base.db
    master = t.base.client
    home = t.base.branch
    other = call(
        master, "/admin/branches", csrf(master), {"code": "OTHER", "name": "다른 지점"}
    ).json()["id"]
    body = {"login_id": t.login, "branch_id": home}
    with (
        closing(branch_actor(t.base, t.password)) as issuer,
        closing(TestClient(master.app, base_url=ORIGIN)) as replacement,
    ):
        issued = call(issuer, BASE, csrf(issuer), body)
        ident = issued.json()["account_id"]
        source(issued)
        path = BASE + "/" + ident
        initial = call(
            master,
            "/admin/accounts",
            csrf(master),
            {"login_id": "remaining.admin", "branch_id": home},
        )
        activate(replacement, source(initial), t.password)
        login_password(replacement, t.password, "remaining.admin")
        actor = issuer.get("/api/v1/auth/me").json()["account_id"]
        changed = master.patch(
            "/api/v1/admin/accounts/" + actor + "/access",
            json={"expected_version": 2, "branch_id": other},
            headers={"Origin": ORIGIN, "X-CSRF-Token": csrf(master)},
        )
        assert changed.status_code == 200
        issuer.cookies.clear()
        login_password(issuer, t.password, "workforce.branch")
        assert issuer.get("/api/v1" + path).status_code == 404
        assert (
            call(issuer, path + "/initial-setup", csrf(issuer), {"expected_version": 1}).status_code
            == 404
        )
        with db.engine.begin() as conn:
            conn.execute(
                text("UPDATE organization_branches SET active=false WHERE id=:b"), {"b": home}
            )
            conn.execute(text(source_deadline_sql("0 seconds")))
        with UnitOfWork(db, password_app[0]).open() as work:
            work.security.allocate("credential")
        with db.session() as reader:
            assert (
                reader.execute(
                    text("SELECT count(*) FROM iam_operator_setup_credentials")
                ).scalar_one()
                == 0
            )
        for sql in (
            "INSERT INTO iam_operator_grants SELECT * FROM iam_operator_grants",
            "UPDATE iam_operator_grants SET version=version+1,branch_id=gen_random_uuid()",
            "UPDATE audit_operator_account_events SET organization_id=gen_random_uuid()",
            "UPDATE audit_operator_account_events SET after_version=0",
        ):
            with db.engine.begin() as conn, pytest.raises(IntegrityError):
                conn.execute(text(sql))
        foreign_org, foreign_branch = uuid4(), uuid4()
        with db.engine.begin() as conn:
            conn.execute(
                text("INSERT INTO organization_organizations VALUES(:o,'가상 조직')"),
                {"o": foreign_org},
            )
            conn.execute(
                text("""INSERT INTO organization_branches(id,organization_id,code,name)
                VALUES(:b,:o,'FOREIGN','가상 지점')"""),
                {"b": foreign_branch, "o": foreign_org},
            )
        assert (
            call(
                master,
                BASE,
                csrf(master),
                {"login_id": "foreign.operator", "branch_id": str(foreign_branch)},
            ).status_code
            == 404
        )
        append = Audit.append_operator

        def fail_audit(adapter: Audit, event: OperatorAccountEvent) -> None:
            append(adapter, event)
            # A real audit CHECK failure must undo the new source and version.
            adapter.s.execute(
                text(
                    "UPDATE audit_operator_account_events SET actor_role='INVALID' "
                    "WHERE account_id=:a"
                ),
                {"a": ident},
            )

        with monkeypatch.context() as patch:
            patch.setattr(Audit, "append_operator", fail_audit)
            assert (
                call(
                    replacement, path + "/initial-setup", csrf(replacement), {"expected_version": 1}
                ).status_code
                == 409
            )
        row = master.get("/api/v1" + path).json()
        assert row["version"] == 1 and "setup_link" not in row
        new_source = source(
            call(replacement, path + "/initial-setup", csrf(replacement), {"expected_version": 1})
        )
        assert (
            call(
                t.recipient,
                "/auth/operator-credentials/complete",
                csrf(t.recipient),
                {"setup_token": new_source, "new_password": t.password},
            ).status_code
            == 204
        )


def test_migration_waits_for_operator_issue(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch
) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from alembic.config import Config
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from alembic.script import ScriptDirectory

    from tests.test_workforce_integrity import wait_for_owned_block
    from y3management.audit.infrastructure import Audit
    from y3management.audit.public import OperatorAccountEvent

    t = trainer
    client = t.base.client
    reached, release = Event(), Event()
    writers: list[int] = []
    waiters: list[int] = []
    append = Audit.append_operator

    def pause(adapter: Audit, event: OperatorAccountEvent) -> None:
        append(adapter, event)
        writers.append(adapter.s.execute(text("SELECT pg_backend_pid()")).scalar_one())
        reached.set()
        assert release.wait(12)

    def database_guard() -> None:
        script = ScriptDirectory.from_config(Config("alembic.ini")).get_revision(
            "0016_operator_onboarding"
        )
        assert script is not None
        # Observe the actual revision independently of the CLI's process exclusion.
        with t.base.db.engine.connect() as conn:
            waiters.append(conn.execute(text("SELECT pg_backend_pid()")).scalar_one())
            with Operations.context(MigrationContext.configure(conn)):
                with pytest.raises(ValueError, match="OPERATOR_HISTORY_PRESENT"):
                    script.module.downgrade()

    monkeypatch.setattr(Audit, "append_operator", pause)
    with ThreadPoolExecutor(max_workers=2) as pool:
        issue = pool.submit(
            call, client, BASE, csrf(client), {"login_id": t.login, "branch_id": t.base.branch}
        )
        try:
            assert reached.wait(5)
            downgrade = pool.submit(database_guard)
            wait_for_owned_block(t.base.db, writers[0], waiters)
            with t.base.db.session() as reader:
                statement = reader.execute(
                    text("SELECT query FROM pg_stat_activity WHERE pid=:pid"), {"pid": waiters[0]}
                ).scalar_one()
                assert "iam_installation" in statement
        finally:
            release.set()
        assert issue.result(timeout=10).status_code == 201
        downgrade.result(timeout=10)
    with t.base.db.session() as reader:
        assert (
            reader.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            == "0016_operator_onboarding"
        )
        assert (
            reader.execute(text("SELECT count(*) FROM audit_operator_account_events")).scalar_one()
            == 1
        )


def test_prepared_operator_reset_c3_and_lifecycle_rename(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch
) -> None:
    from y3management.iam.infrastructure import IAM
    from y3management.iam.password_reset import PasswordReset
    from y3management.iam.public import LoginProof, ResetProof

    t = trainer
    master = t.base.client
    recipient = t.recipient
    issued = call(master, BASE, csrf(master), {"login_id": t.login, "branch_id": t.base.branch})
    token = source(issued)
    ident = issued.json()["account_id"]
    # Rename cancels the original link and permanently reserves the prior ID.
    renamed = mutate(t, issued.json(), "login-id", login_id="renamed.operator")
    assert renamed.status_code == 200
    assert (
        call(
            master, BASE, csrf(master), {"login_id": t.login, "branch_id": t.base.branch}
        ).status_code
        == 409
    )
    assert (
        call(
            recipient,
            "/auth/operator-credentials/complete",
            csrf(recipient),
            {"setup_token": token, "new_password": t.password},
        ).status_code
        == 400
    )
    issued = call(
        master,
        BASE + "/" + ident + "/initial-setup",
        csrf(master),
        {"expected_version": renamed.json()["version"]},
    )
    assert (
        call(
            recipient,
            "/auth/operator-credentials/complete",
            csrf(recipient),
            {"setup_token": source(issued), "new_password": t.password},
        ).status_code
        == 204
    )
    assert t.signin().status_code == 401
    login_password(recipient, t.password, "renamed.operator")

    def advance_grant() -> None:
        with t.base.db.engine.begin() as conn:
            conn.execute(
                text("UPDATE iam_operator_grants SET version=version+1 WHERE account_id=:a"),
                {"a": ident},
            )

    prepare = IAM.prepare_password_change

    def stale_c3(adapter: IAM, account: UUID, current: str, password: str) -> LoginProof:
        proof = prepare(adapter, account, current, password)
        advance_grant()
        return proof

    with monkeypatch.context() as patch:
        patch.setattr(IAM, "prepare_password_change", stale_c3)
        assert (
            call(
                recipient,
                "/auth/password",
                csrf(recipient),
                {"current_password": t.password, "new_password": t.password + " changed"},
            ).status_code
            == 401
        )
    login_password(recipient, t.password, "renamed.operator")
    raw = link_token(reset_request(master, ident).json()["reset_link"])
    reset_prepare = PasswordReset.prepare_reset

    def stale_reset(adapter: PasswordReset, token: str, password: str) -> ResetProof:
        proof = reset_prepare(adapter, token, password)
        advance_grant()
        return proof

    with monkeypatch.context() as patch:
        patch.setattr(PasswordReset, "prepare_reset", stale_reset)
        assert reset_complete(recipient, raw, t.password).status_code == 401
    assert reset_complete(recipient, raw, t.password).status_code == 204
    login_password(recipient, t.password, "renamed.operator")


@pytest.mark.parametrize("first", ["cleanup", "migration"])
def test_downgrade_serializes_trainer_issue_cleanup(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch, first: str
) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event, get_ident

    from sqlalchemy import event
    from sqlalchemy.engine import Connection
    from sqlalchemy.orm import Session

    from tests.legacy_helpers import password_downgrade_guard
    from tests.test_iam_trainer import counts
    from tests.test_workforce_integrity import wait_for_owned_block
    from y3management.audit.infrastructure import Audit
    from y3management.audit.public import TrainerIdentityEvent
    from y3management.iam.security import Security

    db = trainer.base.db
    audit_written, committed, cleanup_policy, cleanup_admitted = (Event() for _ in range(4))
    gate_requested, gate_held = Event(), Event()
    resume_writer, start_gate, resume_gate, resume_cleanup = (Event() for _ in range(4))
    pids: dict[str, int] = {}
    writer_threads: list[int] = []
    append = Audit.append_trainer_identity
    release = Security.release

    def audit(self: Audit, value: TrainerIdentityEvent) -> None:
        append(self, value)
        if value.kind == "issue":
            writer_threads.append(get_ident())
            pids["writer"] = self.s.execute(text("SELECT pg_backend_pid()")).scalar_one()
            audit_written.set()
            assert resume_writer.wait(10)

    def after_commit(session: Session) -> None:
        if get_ident() in writer_threads:
            committed.set()

    gate = "LOCK TABLE iam_installation IN ACCESS EXCLUSIVE MODE"

    def before(
        conn: Connection, cursor: Any, sql: str, params: Any, context: Any, many: bool
    ) -> None:
        driver = conn.connection.driver_connection
        assert driver is not None
        if sql.strip() == gate:
            pids["migration"] = driver.info.backend_pid
            gate_requested.set()
            assert start_gate.wait(10)
        elif (
            get_ident() in writer_threads and committed.is_set() and "FROM iam_installation" in sql
        ):
            pids["cleanup"] = driver.info.backend_pid
            cleanup_policy.set()

    def after(
        conn: Connection, cursor: Any, sql: str, params: Any, context: Any, many: bool
    ) -> None:
        if sql.strip() == gate:
            gate_held.set()
            assert resume_gate.wait(10)

    def cleanup(self: Security, ident: UUID, *, collect: bool = True) -> None:
        if get_ident() in writer_threads:
            assert committed.is_set() and cleanup_policy.is_set()
            cleanup_admitted.set()
            assert resume_cleanup.wait(10)
        release(self, ident, collect=collect)

    monkeypatch.setattr(Audit, "append_trainer_identity", audit)
    monkeypatch.setattr(Security, "release", cleanup)
    event.listen(Session, "after_commit", after_commit)
    event.listen(db.engine, "before_cursor_execute", before)
    event.listen(db.engine, "after_cursor_execute", after)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            issue = pool.submit(trainer.issue)
            try:
                assert audit_written.wait(5)
                migrate = pool.submit(password_downgrade_guard, db, "trainer-gate-" + uuid4().hex)
                assert gate_requested.wait(5)
                if first == "cleanup":
                    resume_writer.set()
                    assert cleanup_admitted.wait(5)
                    start_gate.set()
                    wait_for_owned_block(db, pids["cleanup"], [pids["migration"]])
                    with db.session() as observer:
                        assert not observer.execute(
                            text("""SELECT EXISTS(SELECT FROM pg_locks l
                                JOIN pg_class c ON c.oid=l.relation WHERE l.pid=:pid
                                AND l.granted AND l.mode='AccessExclusiveLock'
                                AND c.relname IN ('iam_sessions','iam_operator_grants',
                                'iam_operator_setup_credentials','audit_operator_account_events'))"""),
                            {"pid": pids["migration"]},
                        ).scalar_one()
                else:
                    start_gate.set()
                    wait_for_owned_block(db, pids["writer"], [pids["migration"]])
                    resume_writer.set()
                    assert gate_held.wait(5) and cleanup_policy.wait(5)
                    wait_for_owned_block(db, pids["migration"], [pids["cleanup"]])
                    assert not cleanup_admitted.is_set()
            finally:
                for barrier in (resume_writer, start_gate, resume_gate, resume_cleanup):
                    barrier.set()
            issued = issue.result(timeout=10)
            assert issued.status_code == 201
            assert migrate.result(timeout=10) == "PASSWORD_DOWNGRADE_REQUIRES_GLOBAL_EMPTY"
            assert cleanup_admitted.is_set()
    finally:
        event.remove(db.engine, "after_cursor_execute", after)
        event.remove(db.engine, "before_cursor_execute", before)
        event.remove(Session, "after_commit", after_commit)
    assert counts(trainer) == (1, 1, 1, 1)
    with db.session() as reader:
        assert reader.scalar(text("SELECT version_num FROM alembic_version")) == (
            "0016_operator_onboarding"
        )
    credential = source(issued)
    assert trainer.complete(credential).status_code == 204
    assert trainer.complete(credential).status_code == 400
