# ruff: noqa: F811
"""Login ID changes: real admission, PostgreSQL races, atomic failures and migration."""

import concurrent.futures
import secrets
import subprocess
import sys
import threading
import time
from dataclasses import replace
from datetime import datetime, timedelta
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import event as sql_event
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from tests.test_iam import ORIGIN, SyntheticSecret, child_env, iam, login  # noqa: F401
from tests.test_iam_s2 import fingerprint_rows
from tests.test_iam_s2b import World, auth, expect, facts, headers, nonce, world  # noqa: F401
from y3management.audit.infrastructure import Audit
from y3management.audit.public import Event
from y3management.contracts import Rejected
from y3management.iam.infrastructure import IAM
from y3management.iam.public import Account, LoginProof, Reservation
from y3management.iam.security import Security

pytestmark = pytest.mark.postgres
OLD = "password.branch"
NEW = "renamed.branch"


def rename(w: World, identifier: str = NEW, version: int = 2) -> httpx.Response:
    response: httpx.Response = w.master.patch(
        f"/api/v1/admin/accounts/{w.ident}/login-id",
        json={"login_id": identifier, "expected_version": version},
        headers=headers(w.master),
    )
    return response


def attempt(w: World, identifier: str, password: str) -> int:
    n, pre = w.service.csrf(None, None)
    n, pre = SyntheticSecret(n), SyntheticSecret(pre) if pre else None
    try:
        w.service.login(identifier, password, pre, n, None)
        return 204
    except Rejected as error:
        return error.status


def account_fingerprint(w: World) -> str:
    with w.db.session() as s:
        return fingerprint_rows(
            list(
                s.execute(
                    text("SELECT id,organization_id,password_hash FROM iam_accounts WHERE id=:a"),
                    {"a": w.ident},
                ).all()
            )
            + list(s.execute(text("SELECT * FROM iam_admin_grants ORDER BY account_id")).all())
        )


def test_rename_sessions_reservations_and_audit(world: World) -> None:
    before = account_fingerprint(world)
    scope = world.branch.get("/api/v1/auth/me").json()
    cookie = auth(world.master)
    response = rename(world, NEW.upper())
    expect(response, 200)
    assert response.json()["login_id"] == NEW
    assert response.json()["version"] == 3
    assert not response.headers.get_list("set-cookie")
    cookie_kept = cookie == auth(world.master)
    assert cookie_kept
    assert account_fingerprint(world) == before
    for client in (world.branch, world.branch_twin):
        expect(client.get("/api/v1/auth/me"), 401)
    expect(world.master.get("/api/v1/auth/me"), 200)
    expect(world.master_twin.get("/api/v1/auth/me"), 200)
    assert attempt(world, OLD, world.branch_password) == 401
    world.branch.cookies.clear()
    login(world.branch, NEW, world.branch_password)
    assert world.branch.get("/api/v1/auth/me").json() == scope
    expect(world.branch.get(f"/api/v1/branches/{world.second_branch}"), 404)
    with world.db.session() as s:
        audited = s.execute(
            text(
                "SELECT before_login_id=:old AND after_login_id=:new AND before_version=2 "
                "AND after_version=3 AND actor_role='MASTER' AND actor_scope='ORGANIZATION' "
                "FROM audit_events WHERE action='login_id_change'"
            ),
            {"old": OLD, "new": NEW},
        ).scalar_one()
        audit_ok = bool(audited)
        reservations = s.execute(
            text("SELECT count(*) FROM iam_login_ids WHERE account_id=:a"), {"a": world.ident}
        ).scalar_one()
        key_fixed = s.execute(
            text("SELECT octet_length(login_budget_key)=32 FROM iam_accounts WHERE id=:a"),
            {"a": world.ident},
        ).scalar_one()
    assert audit_ok and key_fixed
    assert reservations == 2
    expect(rename(world, OLD.upper(), 3), 200)
    assert attempt(world, NEW, world.branch_password) == 401
    assert attempt(world, OLD, world.branch_password) == 204
    for name in (OLD, NEW):
        issued = world.master.post(
            "/api/v1/admin/accounts",
            json={"login_id": name, "branch_id": str(world.branch_id)},
            headers=headers(world.master),
        )
        expect(issued, 409)


@pytest.mark.parametrize(
    "case",
    [
        "noop",
        "stale",
        "stale_noop",
        "csrf",
        "branch",
        "master",
        "missing",
        "disabled",
        "pending",
        "reserved",
        "foreign",
    ],
)
def test_rename_denials_and_noop_preserve_facts(world: World, case: str) -> None:
    target, actor, version, identifier = world.ident, world.master, 2, NEW
    if case in ("pending", "reserved"):
        issued = world.master.post(
            "/api/v1/admin/accounts",
            json={"login_id": "reserved.other", "branch_id": str(world.branch_id)},
            headers=headers(world.master),
        )
        expect(issued, 201)
        if case == "pending":
            target, version = UUID(issued.json()["account_id"]), 1
        else:
            identifier = "reserved.other"
    if case == "disabled":
        world.service.change(auth(world.master), nonce(world.master), target, 2, disable=True)
        version = 3
    if case == "foreign":
        org, target = uuid4(), uuid4()
        with world.db.session() as s:
            s.execute(
                text("INSERT INTO organization_organizations VALUES(:o,'Synthetic')"), {"o": org}
            )
            s.execute(
                text(
                    "INSERT INTO iam_accounts(id,organization_id,login_id,state) "
                    "VALUES(:a,:o,'foreign.account','PENDING_SETUP')"
                ),
                {"a": target, "o": org},
            )
            s.execute(text("INSERT INTO iam_login_ids VALUES('foreign.account',:a)"), {"a": target})
            s.commit()
    if case == "master":
        target = UUID(world.master.get("/api/v1/auth/me").json()["account_id"])
    if case == "missing":
        target = uuid4()
    if case == "branch":
        actor = world.branch
    if case in ("stale", "stale_noop"):
        version = 1
    if case in ("noop", "stale_noop"):
        identifier = OLD.upper()
    h = headers(actor)
    if case == "csrf":
        h["X-CSRF-Token"] = "incorrect"
    before = facts(world.db)
    response = actor.patch(
        f"/api/v1/admin/accounts/{target}/login-id",
        json={"login_id": identifier, "expected_version": version},
        headers=h,
    )
    expected = (
        200
        if case == "noop"
        else 403
        if case in ("csrf", "branch")
        else (404 if case in ("master", "missing", "foreign") else 409)
    )
    expect(response, expected)
    assert facts(world.db) == before


@pytest.mark.parametrize("case", ["audit", "ack"])
def test_rename_atomic_failure(world: World, monkeypatch: pytest.MonkeyPatch, case: str) -> None:
    before = facts(world.db)
    original_append, original_commit = Audit.append, Session.commit

    def append(adapter: Audit, value: Event) -> None:
        original_append(adapter, value)
        if value.action == "login_id_change":
            if case == "audit":
                raise Rejected(503, "unavailable")
            adapter.s.info["rename_ack"] = True

    def commit(s: Session) -> None:
        original_commit(s)
        if s.info.pop("rename_ack", False):
            raise SQLAlchemyError("SYNTHETIC_ACK_LOSS")

    with monkeypatch.context() as patch:
        patch.setattr(Audit, "append", append)
        patch.setattr(Session, "commit", commit)
        response = rename(world)
    expect(response, 503)
    assert not response.headers.get_list("set-cookie")
    if case == "audit":
        assert facts(world.db) == before
        expect(world.branch.get("/api/v1/auth/me"), 200)
    else:
        current = world.master.get(f"/api/v1/admin/accounts/{world.ident}")
        expect(current, 200)
        assert current.json()["login_id"] == NEW
        expect(rename(world), 409)
        expect(world.branch.get("/api/v1/auth/me"), 401)
        assert attempt(world, NEW, world.branch_password) == 204


@pytest.mark.parametrize("failures", [4, 5])
def test_account_budget_survives_rename_and_old_id_attack(world: World, failures: int) -> None:
    for _ in range(failures):
        assert attempt(world, OLD, "synthetic wrong password") == 401
    with world.db.session() as s:
        before = fingerprint_rows(s.execute(text("SELECT * FROM iam_budgets ORDER BY key")).all())
        pending = fingerprint_rows(s.execute(text("SELECT * FROM iam_attempts ORDER BY id")).all())
    expect(rename(world), 200)
    with world.db.session() as s:
        unchanged = before == fingerprint_rows(
            s.execute(text("SELECT * FROM iam_budgets ORDER BY key")).all()
        )
        attempts_kept = pending == fingerprint_rows(
            s.execute(text("SELECT * FROM iam_attempts ORDER BY id")).all()
        )
    assert unchanged and attempts_kept
    if failures == 4:
        assert attempt(world, NEW, "synthetic wrong password") == 401
    assert attempt(world, NEW, world.branch_password) == 429
    for _ in range(5):
        assert attempt(world, OLD, world.branch_password) == 401
    assert attempt(world, OLD, world.branch_password) == 429
    expect(rename(world, OLD, 3), 200)
    assert attempt(world, OLD, world.branch_password) == 429
    with world.db.session() as s:
        distinct = s.execute(
            text("SELECT count(DISTINCT key) FROM iam_attempts WHERE outcome='failure'")
        ).scalar_one()
    assert distinct == 2


def test_old_reserved_attack_does_not_lock_current_account(world: World) -> None:
    expect(rename(world), 200)
    for _ in range(5):
        assert attempt(world, OLD, world.branch_password) == 401
    assert attempt(world, OLD, world.branch_password) == 429
    assert attempt(world, NEW, world.branch_password) == 204


@pytest.mark.parametrize("outcome", ["finish", "cancel", "expire"])
def test_pending_reservation_identity_survives_rename(world: World, outcome: str) -> None:
    with world.service.uow.open() as w:
        reservation = w.security.reserve(OLD)
    with world.db.session() as s:
        before = fingerprint_rows(
            s.execute(text("SELECT * FROM iam_attempts WHERE id=:i"), {"i": reservation.id}).all()
        )
    expect(rename(world), 200)
    with world.db.session() as s:
        unchanged = before == fingerprint_rows(
            s.execute(text("SELECT * FROM iam_attempts WHERE id=:i"), {"i": reservation.id}).all()
        )
    assert unchanged
    if outcome == "expire":
        with world.db.session() as s:
            s.execute(
                text(
                    "UPDATE iam_attempts SET lease_until=clock_timestamp()-interval '1 second' "
                    "WHERE id=:i"
                ),
                {"i": reservation.id},
            )
            s.commit()
        with world.service.uow.open() as w:
            other = w.security.reserve(NEW)
            same_key = other.key == reservation.key
            w.security.cancel(other)
        assert same_key
    else:
        with world.service.uow.open() as w:
            if outcome == "finish":
                w.security.finish(reservation, False)
            else:
                w.security.cancel(reservation)
    with world.db.session() as s:
        result = s.execute(
            text("SELECT outcome FROM iam_attempts WHERE id=:i"), {"i": reservation.id}
        ).scalar_one_or_none()
    assert result == (None if outcome == "cancel" else "failure")


@pytest.mark.parametrize("scenario", ["unknown", "reserved", "aba", "old_admission", "old_proof"])
def test_admission_rename_barrier(
    world: World, monkeypatch: pytest.MonkeyPatch, scenario: str
) -> None:
    if scenario == "reserved":
        expect(rename(world), 200)
    identifier = NEW if scenario == "unknown" else OLD
    # A cooldown on the real account must not be bypassed by unknown/historic admission.
    if scenario in ("unknown", "reserved"):
        for _ in range(5):
            assert attempt(world, NEW if scenario == "reserved" else OLD, "wrong synthetic") == 401
    admitted, release = threading.Event(), threading.Event()
    captured: list[Reservation] = []
    original_subject, original_verify = IAM.login_subject, IAM.verify_login

    def subject(adapter: IAM, value: str) -> Account | None:
        if scenario != "old_proof":
            admitted.set()
            assert release.wait(10)
        return original_subject(adapter, value)

    def verify(
        adapter: IAM, value: str, password: str, reservation: Reservation
    ) -> LoginProof | None:
        proof = original_verify(adapter, value, password, reservation)
        if scenario == "old_proof":
            admitted.set()
            assert release.wait(10)
        return proof

    original_reserve, original_allocate = Security.reserve, Security.allocate
    allocated_slots: list[UUID] = []

    def allocate(adapter: Security, kind: str) -> UUID:
        ident = original_allocate(adapter, kind)
        if kind == "session_slot":
            allocated_slots.append(ident)
        return ident

    def reserve(adapter: Security, value: str) -> Reservation:
        result = original_reserve(adapter, value)
        captured.append(result)
        return result

    with monkeypatch.context() as patch:
        patch.setattr(IAM, "login_subject", subject)
        patch.setattr(IAM, "verify_login", verify)
        patch.setattr(Security, "reserve", reserve)
        patch.setattr(Security, "allocate", allocate)
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(attempt, world, identifier, world.branch_password)
            try:
                assert admitted.wait(5)
                if scenario == "reserved":
                    expect(rename(world, OLD, 3), 200)
                else:
                    expect(rename(world), 200)
                    if scenario == "aba":
                        expect(rename(world, OLD, 3), 200)
            finally:
                release.set()
            assert pending.result(timeout=5) == (401 if scenario == "old_proof" else 503)
    with world.db.session() as s:
        outcome = s.execute(
            text("SELECT outcome FROM iam_attempts WHERE id=:i"), {"i": captured[0].id}
        ).scalar_one()
        live = s.execute(
            text("SELECT count(*) FROM iam_sessions WHERE account_id=:a AND NOT revoked"),
            {"a": world.ident},
        ).scalar_one()
        orphan_slots = s.execute(
            text("SELECT count(*) FROM iam_security_states WHERE id=ANY(:ids)"),
            {"ids": allocated_slots},
        ).scalar_one()
    assert outcome == ("failure" if scenario == "old_proof" else "pending")
    assert live == 0 and orphan_slots == 0
    if scenario in ("unknown", "reserved"):
        assert attempt(world, OLD if scenario == "reserved" else NEW, world.branch_password) == 429


@pytest.mark.parametrize("field", ["key", "account", "version"])
def test_final_login_requires_actual_admission(world: World, field: str) -> None:
    n, pre = world.service.csrf(None, None)
    n, pre = SyntheticSecret(n), SyntheticSecret(pre) if pre else None
    with world.service.uow.open() as w:
        reservation = w.security.reserve(OLD)
        sid = w.security.allocate("session_slot")
    fake = replace(
        reservation,
        **(
            {"key": b"x" * 32}
            if field == "key"
            else {"account_id": uuid4()}
            if field == "account"
            else {"security_version": 999}
        ),
    )
    before = facts(world.db)
    with pytest.raises(Rejected) as rejected, world.service.uow.open() as w:
        proof = w.iam.verify_login(OLD, world.branch_password, reservation)
        assert proof is not None
        w.iam.login(proof, sid, pre, n, fake)
    assert rejected.value.status == 503
    assert facts(world.db) == before
    with world.service.uow.open() as w:
        w.security.release(sid)


@pytest.mark.parametrize("guard", ["unused", "history", "key_only", "history_only"])
def test_login_id_migration_guards(world: World, guard: str) -> None:
    def migrate(direction: str, target: str) -> int:
        return subprocess.run(
            [sys.executable, "-m", "alembic", direction, target],
            env=child_env(world.settings),
            capture_output=True,
            timeout=30,
        ).returncode

    if guard in ("history", "history_only"):
        expect(rename(world), 200)
        if guard == "history_only":
            # Isolate the audit guard in this disposable schema.
            with world.db.session() as s:
                s.execute(
                    text("UPDATE iam_accounts SET login_budget_key=NULL WHERE id=:a"),
                    {"a": world.ident},
                )
                s.commit()
    elif guard == "key_only":
        # Isolate the nonnull-key guard without management history in this owned test schema.
        with world.db.session() as s:
            s.execute(
                text("UPDATE iam_accounts SET login_budget_key=:k WHERE id=:a"),
                {"k": b"k" * 32, "a": world.ident},
            )
            s.commit()
    before = facts(world.db)
    result = migrate("downgrade", "0003_iam_password")
    if guard == "unused":
        assert result == 0
        assert migrate("upgrade", "head") == 0
    else:
        assert result != 0
    assert facts(world.db) == before
    with world.db.session() as s:
        revision = s.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    assert revision == "0005_iam_mfa"


@pytest.mark.parametrize("competitor", ["disable", "scope", "password", "claim", "rename"])
def test_rename_orders_competing_pg_connections(
    world: World, monkeypatch: pytest.MonkeyPatch, competitor: str
) -> None:
    held, release, entered = threading.Event(), threading.Event(), threading.Event()
    holders: list[int] = []
    waiters: list[int] = []
    ma, mn, ba, bn = (
        auth(world.master),
        nonce(world.master),
        auth(world.branch),
        nonce(world.branch),
    )
    new_password = SyntheticSecret("가상 경합 새 암호 " + secrets.token_urlsafe(24))
    original = Audit.append

    def append(adapter: Audit, value: Event) -> None:
        original(adapter, value)
        if value.action == "login_id_change":
            holders.append(adapter.s.execute(text("SELECT pg_backend_pid()")).scalar_one())
            held.set()
            assert release.wait(10)

    def observe(
        connection: Connection,
        cursor: object,
        statement: str,
        parameters: object,
        context: object,
        many: bool,
    ) -> None:
        if threading.current_thread().name.startswith("s2c-waiter") and (
            "FOR UPDATE" in statement or "FOR SHARE" in statement
        ):
            driver = connection.connection.driver_connection
            assert driver is not None
            waiters.append(driver.info.backend_pid)
            entered.set()

    def compete() -> int:
        try:
            if competitor == "password":
                world.service.change_password(ba, bn, world.branch_password, new_password)
            elif competitor == "claim":
                world.service.issue(ma, mn, NEW, world.branch_id)
            elif competitor == "rename":
                world.service.change_login_id(ma, mn, world.ident, 2, "concurrent.name")
            else:
                world.service.change(
                    ma,
                    mn,
                    world.ident,
                    2,
                    world.second_branch if competitor == "scope" else None,
                    disable=competitor == "disable",
                )
            return 200
        except Rejected as error:
            return error.status

    with monkeypatch.context() as patch:
        patch.setattr(Audit, "append", append)
        sql_event.listen(world.db.engine, "before_cursor_execute", observe)
        try:
            with (
                concurrent.futures.ThreadPoolExecutor(max_workers=1) as first_pool,
                concurrent.futures.ThreadPoolExecutor(
                    max_workers=1, thread_name_prefix="s2c-waiter"
                ) as second_pool,
            ):
                first = first_pool.submit(
                    world.service.change_login_id, ma, mn, world.ident, 2, NEW
                )
                try:
                    assert held.wait(5)
                    second = second_pool.submit(compete)
                    assert entered.wait(5)
                    blocked = False
                    deadline = time.monotonic() + 3
                    while time.monotonic() < deadline:
                        with world.db.session() as s:
                            blocked = (
                                holders[0]
                                in s.execute(
                                    text("SELECT pg_blocking_pids(:p)"), {"p": waiters[-1]}
                                ).scalar_one()
                            )
                        if blocked:
                            break
                        time.sleep(0.01)
                    assert blocked and not second.done()
                finally:
                    release.set()
                first.result(timeout=5)
                assert second.result(timeout=5) == (401 if competitor == "password" else 409)
        finally:
            release.set()
            sql_event.remove(world.db.engine, "before_cursor_execute", observe)


def test_login_commits_before_rename_late_finish_keeps_revocation(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    held, release = threading.Event(), threading.Event()
    original = Security.finish

    def finish(adapter: Security, reservation: Reservation, success: bool) -> None:
        if success and reservation.account_id == world.ident:
            held.set()
            assert release.wait(10)
        original(adapter, reservation, success)

    with monkeypatch.context() as patch:
        patch.setattr(Security, "finish", finish)
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            pending = pool.submit(attempt, world, OLD, world.branch_password)
            try:
                assert held.wait(5)
                expect(rename(world), 200)
            finally:
                release.set()
            assert pending.result(timeout=5) == 204
    with world.db.session() as s:
        live = s.execute(
            text("SELECT count(*) FROM iam_sessions WHERE account_id=:a AND NOT revoked"),
            {"a": world.ident},
        ).scalar_one()
    assert live == 0


def test_fixed_key_disabled_restore_gc_and_capacity(world: World) -> None:
    expect(rename(world), 200)
    with world.service.uow.open() as w:
        anchor = w.security.reserve(NEW)
        w.security.finish(anchor, False)
    world.service.change(auth(world.master), nonce(world.master), world.ident, 3, disable=True)
    with world.service.uow.open() as w:
        disabled = w.security.reserve(NEW)
        equal = anchor.key == disabled.key
        w.security.cancel(disabled)
    assert equal
    world.service.restore(auth(world.master), nonce(world.master), world.ident, 4)
    with world.service.uow.open() as w:
        restored = w.security.reserve(NEW)
        equal = anchor.key == restored.key
        w.security.cancel(restored)
    assert equal
    # Drive only this owned account's ephemeral state beyond its existing lifetime.
    with world.db.session() as s:
        s.execute(
            text(
                "UPDATE iam_security_states SET expires_at=clock_timestamp()-interval '1 second' "
                "WHERE id IN (SELECT id FROM iam_attempts WHERE key=:k) "
                "OR id IN (SELECT state_id FROM iam_budgets WHERE key=:k)"
            ),
            {"k": anchor.key},
        )
        s.commit()
    with world.service.uow.open() as w:
        regenerated = w.security.reserve(NEW)
        equal = regenerated.key == anchor.key
        w.security.cancel(regenerated)
    assert equal
    with world.db.session() as s:
        before = fingerprint_rows(s.execute(text("SELECT * FROM iam_budgets ORDER BY key")).all())
    with pytest.raises(Rejected) as denied, world.db.session() as s:
        Security(s, world.settings.iam_key.get_secret_value(), 0, 128).reserve("capacity.probe")
    assert denied.value.status == 503
    with world.db.session() as s:
        after = fingerprint_rows(s.execute(text("SELECT * FROM iam_budgets ORDER BY key")).all())
    assert after == before


def test_new_name_anonymous_cooldown_does_not_become_account_budget(world: World) -> None:
    for _ in range(5):
        assert attempt(world, NEW, "wrong synthetic") == 401
    assert attempt(world, NEW, world.branch_password) == 429
    expect(rename(world), 200)
    assert attempt(world, NEW, world.branch_password) == 204


def test_unknown_admission_wrong_password_never_audits_new_principal(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = IAM.login_subject

    def subject(adapter: IAM, value: str) -> Account | None:
        expect(rename(world), 200)
        return original(adapter, value)

    with monkeypatch.context() as patch:
        patch.setattr(IAM, "login_subject", subject)
        status = attempt(world, NEW, "incorrect synthetic")
    assert status == 503
    with world.db.session() as s:
        failures = s.execute(
            text("SELECT count(*) FROM audit_events WHERE action='login' AND NOT success")
        ).scalar_one()
        pending = s.execute(
            text("SELECT count(*) FROM iam_attempts WHERE outcome='pending'")
        ).scalar_one()
    assert failures == 0 and pending == 1


def test_noop_in_cooldown_preserves_every_fact(world: World) -> None:
    for _ in range(5):
        assert attempt(world, OLD, "incorrect synthetic") == 401
    before = facts(world.db)
    expect(rename(world, OLD.upper()), 200)
    assert facts(world.db) == before


def test_subject_snapshot_then_rename_does_not_misattribute_failure(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = IAM.login_subject

    def subject(adapter: IAM, identifier: str) -> Account | None:
        result = original(adapter, identifier)
        expect(rename(world), 200)
        return result

    with monkeypatch.context() as patch:
        patch.setattr(IAM, "login_subject", subject)
        status = attempt(world, OLD, "incorrect synthetic")
    assert status == 503
    with world.db.session() as s:
        failed_audits = s.execute(
            text("SELECT count(*) FROM audit_events WHERE action='login' AND NOT success")
        ).scalar_one()
        pending = s.execute(
            text("SELECT count(*) FROM iam_attempts WHERE outcome='pending'")
        ).scalar_one()
    assert failed_audits == 0 and pending == 1


@pytest.mark.parametrize("constraint", ["length", "unique"])
def test_budget_key_storage_constraints(world: World, constraint: str) -> None:
    from sqlalchemy.exc import IntegrityError

    expect(rename(world), 200)
    before = facts(world.db)
    with pytest.raises(IntegrityError), world.db.session() as s:
        if constraint == "length":
            s.execute(
                text("UPDATE iam_accounts SET login_budget_key=:k WHERE id=:a"),
                {"k": b"short", "a": world.ident},
            )
        else:
            s.execute(
                text(
                    "UPDATE iam_accounts SET login_budget_key="
                    "(SELECT login_budget_key FROM iam_accounts WHERE id=:a) "
                    "WHERE login_id='master.test'"
                ),
                {"a": world.ident},
            )
        s.commit()
    assert facts(world.db) == before


def actor_activity_invariants(w: World, session_id: UUID, account_id: UUID) -> list[str]:
    with w.db.session() as s:
        return [
            fingerprint_rows(s.execute(text(query), {"sid": session_id, "aid": account_id}).all())
            for query in (
                "SELECT id,account_id,digest,csrf,security_version,created_at,expires_at,revoked "
                "FROM iam_sessions WHERE id=:sid",
                "SELECT * FROM iam_sessions WHERE account_id=:aid AND id<>:sid ORDER BY id",
                "SELECT * FROM iam_accounts WHERE id=:aid",
            )
        ]


def test_actual_rename_refreshes_only_current_near_idle_actor(world: World) -> None:
    with world.service.uow.open() as w:
        current = w.iam.authenticate(auth(world.master), touch=False)
    session_id, account_id = current.session_id, current.caller.account_id
    del current  # Authentication includes a CSRF value; keep only IDs in assertion locals.
    with world.db.session() as s:
        s.execute(
            text(
                "UPDATE iam_sessions SET created_at=clock_timestamp()-interval '30 minutes',"
                "last_activity=clock_timestamp()-interval '29 minutes' WHERE id=:sid"
            ),
            {"sid": session_id},
        )
        s.commit()
        started = s.execute(text("SELECT clock_timestamp()")).scalar_one()
    before = actor_activity_invariants(world, session_id, account_id)
    expect(rename(world), 200)
    with world.db.session() as s:
        advanced = bool(
            s.execute(
                text("SELECT last_activity>=:started FROM iam_sessions WHERE id=:sid"),
                {"started": started, "sid": session_id},
            ).scalar_one()
        )
    preserved = before == actor_activity_invariants(world, session_id, account_id)
    assert advanced, "Successful management must refresh the current actor session"
    assert preserved, "Absolute expiry, other actor sessions and actor account must stay unchanged"
    expect(world.master.get("/api/v1/auth/me"), 200)
    expect(world.master_twin.get("/api/v1/auth/me"), 200)


@pytest.mark.parametrize("expiry", ["idle", "absolute"])
def test_final_actor_expiry_rolls_back_entire_rename(
    world: World, monkeypatch: pytest.MonkeyPatch, expiry: str
) -> None:
    token, csrf = auth(world.master), nonce(world.master)
    with world.service.uow.open() as w:
        current = w.iam.authenticate(token, touch=False)
    session_id = current.session_id
    del current
    with world.db.session() as s:
        deadline: datetime = s.execute(
            text("SELECT expires_at FROM iam_sessions WHERE id=:sid"), {"sid": session_id}
        ).scalar_one()
        if expiry == "absolute":
            # Model activity near absolute expiry, then advance only the verifier's clock.
            s.execute(
                text(
                    "UPDATE iam_sessions SET last_activity=expires_at-interval '1 minute' "
                    "WHERE id=:sid"
                ),
                {"sid": session_id},
            )
            s.commit()
    before = facts(world.db)
    original_now = IAM.now
    reads = 0

    def now(adapter: IAM) -> datetime:
        nonlocal reads
        reads += 1
        if expiry == "absolute":
            return deadline + (timedelta(seconds=1) if reads == 2 else -timedelta(seconds=30))
        return original_now(adapter) + (timedelta(minutes=31) if reads == 2 else timedelta())

    with monkeypatch.context() as patch:
        patch.setattr(IAM, "now", now)
        with pytest.raises(Rejected) as rejected:
            world.service.change_login_id(token, csrf, world.ident, 2, NEW)
    assert rejected.value.status == 401
    assert reads == 2, "Denial must come from the final reauthentication"
    assert facts(world.db) == before, "Expiry must roll back rename, revocation, audit and activity"
