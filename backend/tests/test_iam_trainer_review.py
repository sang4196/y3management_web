# ruff: noqa: F811
"""Causal acceptance cases requested by the independent pre-freeze review."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from threading import Event, get_ident
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session

from tests.test_iam import ORIGIN, SyntheticSecret, csrf
from tests.test_iam_mfa import call, mfa  # noqa: F401
from tests.test_iam_trainer import TrainerScene, counts, source, trainer  # noqa: F401
from tests.test_workforce import scene  # noqa: F401
from tests.test_workforce_integrity import branch_actor
from y3management.audit.infrastructure import Audit
from y3management.audit.public import TrainerIdentityEvent
from y3management.config import Settings
from y3management.database import Database
from y3management.iam.security import Security
from y3management.uow import UnitOfWork
from y3management.use_cases import Service

pytestmark = pytest.mark.postgres


@pytest.mark.parametrize("same", [True, False])
def test_stale_preflight_then_other_actor_commit(
    trainer: TrainerScene,
    mfa: tuple[Settings, Database, str, str],
    monkeypatch: pytest.MonkeyPatch,
    same: bool,
) -> None:
    t = trainer
    reached, release = Event(), Event()
    original = Security.allocate
    paused: list[int] = []

    def allocate(self: Security, kind: str, *, collect: bool = True) -> Any:
        if kind == "credential" and not collect and not paused:
            paused.append(get_ident())
            # This is after preflight UoW closed and before any allocation/business lock.
            assert (
                self.s.execute(text("SELECT count(*) FROM iam_trainer_bindings")).scalar_one() == 0
            )
            reached.set()
            assert release.wait(10)
        return original(self, kind, collect=collect)

    with closing(branch_actor(t.base, mfa[2])) as other:
        na, nb = csrf(t.base.client), csrf(other)
        payload = {"operation_id": str(uuid4()), "login_id": t.login}
        path = "/admin/trainers/" + t.trainer + "/login-account"
        monkeypatch.setattr(Security, "allocate", allocate)
        with ThreadPoolExecutor(max_workers=1) as pool:
            first = pool.submit(call, t.base.client, path, na, payload)
            try:
                assert reached.wait(5)
                second = call(
                    other,
                    path,
                    nb,
                    payload if same else {**payload, "login_id": t.login + "_other"},
                )
                assert second.status_code == 201 and counts(t) == (1, 1, 1, 1)
            finally:
                release.set()
            assert first.result(timeout=10).status_code == (200 if same else 409)
        assert counts(t) == (1, 1, 1, 1)


@pytest.mark.parametrize("ack", [False, True])
def test_finish_failure_only_revokes_undelivered_session(
    trainer: TrainerScene,
    monkeypatch: pytest.MonkeyPatch,
    ack: bool,
) -> None:
    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    assert t.signin(password="synthetic wrong password").status_code == 401
    assert t.signin().status_code == 204
    with closing(TestClient(t.base.client.app, base_url=ORIGIN)) as other:
        nonce = csrf(other)
        with t.base.db.session() as s:
            before = {
                row.id: bool(row.revoked)
                for row in s.execute(text("SELECT id,revoked FROM iam_sessions"))
            }
            budget = s.execute(text("SELECT key,cooldown FROM iam_budgets ORDER BY key")).all()
            failures = s.execute(
                text("SELECT count(*) FROM iam_attempts WHERE outcome='failure'")
            ).scalar_one()
        original_finish, original_commit = Security.finish, Session.commit
        finishing = False
        fired = False

        def finish(self: Security, reservation: Any, success: bool) -> None:
            nonlocal finishing, fired
            assert success
            # Business login is already visible from an independent connection.
            with t.base.db.session() as reader:
                assert (
                    reader.execute(text("SELECT count(*) FROM iam_sessions")).scalar_one()
                    == len(before) + 1
                )
            if not ack:
                fired = True
                raise OperationalError("finish", {}, Exception("synthetic finish failure"))
            original_finish(self, reservation, success)
            finishing = True

        def commit(self: Session) -> None:
            nonlocal fired
            original_commit(self)
            if finishing and not fired:
                fired = True
                raise OperationalError("commit", {}, Exception("synthetic finish ack loss"))

        with monkeypatch.context() as patch:
            patch.setattr(Security, "finish", finish)
            patch.setattr(Session, "commit", commit)
            response = call(
                other, "/auth/login", nonce, {"login_id": t.login, "password": t.password}
            )
        assert response.status_code == 503 and fired
        assert "__Host-y3-auth" not in response.response.headers.get("set-cookie", "")
        assert other.get("/api/v1/auth/me").status_code == 401
        with t.base.db.session() as s:
            after = {
                row.id: bool(row.revoked)
                for row in s.execute(text("SELECT id,revoked FROM iam_sessions"))
            }
            assert {key: after[key] for key in before} == before
            added = set(after) - set(before)
            assert len(added) == 1 and all(after[key] for key in added)
            assert (
                s.execute(text("SELECT key,cooldown FROM iam_budgets ORDER BY key")).all() == budget
            )
            assert (
                s.execute(
                    text("SELECT count(*) FROM iam_attempts WHERE outcome='failure'")
                ).scalar_one()
                == failures
            )
            assert s.execute(
                text("SELECT count(*) FROM iam_attempts WHERE outcome='pending'")
            ).scalar_one() == (0 if ack else 1)
            assert (
                s.execute(
                    text("SELECT count(*) FROM audit_trainer_identity_events WHERE kind='login'")
                ).scalar_one()
                == 2
            )
        assert t.recipient.get("/api/v1/auth/me").status_code == 200
        assert t.base.client.get("/api/v1/auth/me").status_code == 200


def test_binding_both_uniqueness_directions_and_foreign_keys(trainer: TrainerScene) -> None:
    t = trainer
    source(t.issue())
    other_trainer = t.base.send(t.base.body()).json()["trainer"]["id"]
    with t.base.db.session() as s:
        org, account = s.execute(
            text("SELECT organization_id,account_id FROM iam_trainer_bindings")
        ).one()
        other_account = s.execute(
            text("SELECT id FROM iam_accounts WHERE login_id='master.test'")
        ).scalar_one()
    foreign_org = uuid4()
    with t.base.db.session() as s:
        s.execute(
            text("INSERT INTO organization_organizations(id,name) VALUES(:i,:n)"),
            {"i": foreign_org, "n": "가상 다른 조직"},
        )
        s.commit()
    cases = [
        (org, other_account, t.trainer, "23505"),  # Trainer unique alone.
        (org, account, other_trainer, "23505"),  # Account PK alone.
        (foreign_org, other_account, other_trainer, "23503"),
        (org, other_account, uuid4(), "23503"),
    ]
    for organization, principal, employee, expected in cases:
        with t.base.db.session() as s, pytest.raises(IntegrityError) as error:
            s.execute(
                text(
                    "INSERT INTO iam_trainer_bindings(account_id,organization_id,trainer_id) "
                    "VALUES(:a,:o,:t)"
                ),
                {"a": principal, "o": organization, "t": employee},
            )
        assert getattr(error.value.orig, "sqlstate", None) == expected
        assert counts(t) == (1, 1, 1, 1)


def test_same_account_inactive_trainer_keeps_admin_uv(
    trainer: TrainerScene,
    mfa: tuple[Settings, Database, str, str],
) -> None:
    t = trainer
    with t.base.db.session() as s:
        s.execute(
            text(
                "INSERT INTO iam_trainer_bindings(account_id,organization_id,trainer_id) "
                "SELECT id,organization_id,:t FROM iam_accounts WHERE login_id='master.test'"
            ),
            {"t": t.trainer},
        )
        s.commit()
    t.active(False)
    me = t.base.client.get("/api/v1/auth/me")
    assert me.status_code == 200 and me.json()["roles"][0]["role"] == "ADMIN"
    assert all(role["role"] != "TRAINER" for role in me.json()["roles"])
    assert t.base.client.get("/api/v1/branches").status_code == 200
    # Genuine password-only session from the retained S1 fixture cannot bypass MFA audience.
    legacy = Service(UnitOfWork(t.base.db, mfa[0].model_copy(update={"iam_mode": "s1_password"})))
    nonce, preauth = legacy.csrf(None, None)
    weak = SyntheticSecret(legacy.login("master.test", mfa[2], preauth, nonce, None))
    for path in ["/auth/me", "/branches"]:
        assert (
            t.recipient.get(
                "/api/v1" + path, headers={"Cookie": "__Host-y3-auth=" + weak}
            ).status_code
            == 401
        )
    r = call(
        t.recipient,
        "/auth/login",
        csrf(t.recipient),
        {"login_id": "master.test", "password": mfa[2]},
    )
    assert r.status_code == 200 and "publicKey" in r.json()
    assert "__Host-y3-auth" not in r.response.headers.get("set-cookie", "")
    assert t.base.client.get("/api/v1/auth/me").status_code == 200


@pytest.mark.parametrize("kind", ["issue", "reissue", "password_change", "logout"])
@pytest.mark.parametrize("absolute", [False, True])
def test_original_actor_deadline_after_audit_without_touch(
    trainer: TrainerScene,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
    absolute: bool,
) -> None:
    t = trainer
    if kind != "issue":
        token = source(t.issue())
    if kind in ("password_change", "logout"):
        assert t.complete(token).status_code == 204 and t.signin().status_code == 204
    client = t.recipient if kind in ("password_change", "logout") else t.base.client
    nonce = csrf(client)
    actor = client.get("/api/v1/auth/me").json()["account_id"]
    with t.base.db.session() as s:
        if absolute:
            s.execute(
                text("""WITH shifted AS (UPDATE iam_security_states
              SET expires_at=clock_timestamp()+interval '2 seconds'
              WHERE id IN (SELECT id FROM iam_sessions WHERE account_id=:a) RETURNING id,expires_at)
              UPDATE iam_sessions s SET expires_at=shifted.expires_at,
              created_at=shifted.expires_at-interval '8 hours',
              last_activity=shifted.expires_at-interval '1 minute'
              FROM shifted WHERE s.id=shifted.id"""),
                {"a": actor},
            )
        else:
            s.execute(
                text(
                    "UPDATE iam_sessions SET created_at=clock_timestamp()-interval '31 minutes',"
                    "last_activity=clock_timestamp()-interval '29 minutes 58 seconds' "
                    "WHERE account_id=:a"
                ),
                {"a": actor},
            )
        s.commit()
        before_sessions = s.execute(
            text("SELECT id,last_activity,revoked FROM iam_sessions ORDER BY id")
        ).all()
        before_accounts = s.execute(
            text("SELECT id,state,row_version,security_version FROM iam_accounts ORDER BY id")
        ).all()
    before = counts(t)
    original = Audit.append_trainer_identity
    observed: list[tuple[bool, bool]] = []

    def deadlines(self: Audit) -> tuple[bool, bool]:
        row = self.s.execute(
            text(
                "SELECT last_activity+interval '30 minutes'>clock_timestamp(),"
                "expires_at>clock_timestamp() FROM iam_sessions WHERE account_id=:a"
            ),
            {"a": actor},
        ).one()
        return bool(row[0]), bool(row[1])

    def delay(self: Audit, value: TrainerIdentityEvent) -> None:
        original(self, value)
        if value.kind == kind:
            observed.append(deadlines(self))
            self.s.execute(text("SELECT pg_sleep(1.1)"))
            self.s.execute(text("SELECT pg_sleep(1.1)"))
            observed.append(deadlines(self))

    monkeypatch.setattr(Audit, "append_trainer_identity", delay)
    if kind == "issue":
        response = call(
            client,
            "/admin/trainers/" + t.trainer + "/login-account",
            nonce,
            {"operation_id": str(uuid4()), "login_id": t.login},
        )
    elif kind == "reissue":
        response = call(
            client,
            "/admin/trainers/" + t.trainer + "/initial-setup",
            nonce,
            {"operation_id": str(uuid4()), "expected_account_version": 1},
        )
    elif kind == "password_change":
        response = call(
            client,
            "/auth/password",
            nonce,
            {"current_password": t.password, "new_password": t.password + " changed"},
        )
    else:
        response = call(client, "/auth/logout", nonce, {})
    assert response.status_code in (401, 403)
    assert observed == [(True, True), (True, False) if absolute else (False, True)]
    assert counts(t) == before
    with t.base.db.session() as s:
        assert (
            s.execute(text("SELECT id,last_activity,revoked FROM iam_sessions ORDER BY id")).all()
            == before_sessions
        )
        assert (
            s.execute(
                text("SELECT id,state,row_version,security_version FROM iam_accounts ORDER BY id")
            ).all()
            == before_accounts
        )


def test_downgrade_waits_for_actual_issue_then_preserves_history(
    trainer: TrainerScene,
    mfa: tuple[Settings, Database, str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import subprocess
    import sys
    import time

    from tests.conftest import qa_register_process, qa_stop_process
    from tests.test_iam import child_env

    t = trainer
    reached, release = Event(), Event()
    holder: list[int] = []
    original = Audit.append_trainer_identity

    def pause(self: Audit, value: TrainerIdentityEvent) -> None:
        original(self, value)
        if value.kind == "issue":
            holder.append(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one())
            reached.set()
            assert release.wait(15)

    monkeypatch.setattr(Audit, "append_trainer_identity", pause)
    appname = "trainer-downgrade-" + uuid4().hex
    env = child_env(mfa[0])
    env["PGAPPNAME"] = appname
    with ThreadPoolExecutor(max_workers=1) as pool:
        issuing = pool.submit(t.issue)
        process = None
        try:
            assert reached.wait(5)
            process = subprocess.Popen(
                [sys.executable, "-m", "alembic", "downgrade", "0010_workforce_initial"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            qa_register_process(process)
            waiting = False
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline and process.poll() is None:
                with t.base.db.session() as reader:
                    waiting = bool(
                        reader.execute(
                            text(
                                "SELECT EXISTS(SELECT 1 FROM pg_stat_activity "
                                "WHERE datname=current_database() "
                                "AND application_name=:n AND wait_event_type='Lock' AND pid<>:h "
                                "AND :h=ANY(pg_blocking_pids(pid)))"
                            ),
                            {"n": appname, "h": holder[0]},
                        ).scalar_one()
                    )
                if waiting:
                    break
                time.sleep(0.02)
            assert waiting
            release.set()
            issued = issuing.result(timeout=10)
            assert issued.status_code == 201
            process.communicate(timeout=10)
            assert process.returncode != 0 and counts(t) == (1, 1, 1, 1)
            with t.base.db.session() as reader:
                assert (
                    reader.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
                    == "0012_iam_trainer_roles"
                )
            assert t.complete(source(issued)).status_code == 204
        finally:
            release.set()
            if process is not None:
                qa_stop_process(process)
