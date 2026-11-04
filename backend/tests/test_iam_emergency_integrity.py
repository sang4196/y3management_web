# ruff: noqa: F811
"""Emergency isolation, durable history, real crypto races and commit failures."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from threading import Event as Signal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from tests.legacy_helpers import legacy_database, legacy_master  # noqa: F401
from tests.password_helpers import (  # noqa: F401
    activate,
    call,
    login_password,
    password_app,
    provision,
)
from tests.test_iam import ORIGIN, csrf
from tests.test_iam_emergency import facts, issue, operator, request
from y3management.application import create_app
from y3management.audit.infrastructure import Audit
from y3management.audit.public import PasswordEmergencyEvent as Event
from y3management.config import Settings
from y3management.contracts import CommitUncertain, Rejected
from y3management.database import Database
from y3management.iam.emergency import Emergency
from y3management.iam.public import EmergencyPasswordProof, Setup
from y3management.runtime import ProcessGuard

pytestmark = pytest.mark.postgres


def test_permissions_and_causal_reissue(
    password_app: tuple[Settings, Database, str], tmp_path: Path
) -> None:
    settings, db, password = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN):
        service, principal, ident = operator(settings, db, tmp_path / "operator")
        first = request(service, principal, ident)
        with pytest.raises(Rejected):
            issue(service, replace(principal, operations=frozenset({"inspect"})), first)
        execute_only = replace(principal, operations=frozenset({"execute"}))
        issue(service, execute_only, first)
        second = request(service, principal, ident, supersedes=first.operation_id)
        issue(service, execute_only, second)
        # Equal timestamps do not replace causal row versions; bound expiries move together.
        with db.session() as session:
            session.execute(
                text("""WITH baseline AS (
              SELECT min(issued_at) issued,min(checked_at) checked,min(expires_at) expiry
              FROM iam_password_emergency_cases), c AS (
              UPDATE iam_password_emergency_cases SET issued_at=baseline.issued,
              checked_at=baseline.checked,expires_at=baseline.expiry FROM baseline
              RETURNING id,expires_at), p AS (
              UPDATE iam_security_states s SET expires_at=c.expires_at
              FROM iam_password_emergency_credentials e JOIN c ON c.id=e.case_id
              WHERE s.id=e.id RETURNING s.id,s.expires_at)
              UPDATE iam_password_emergency_credentials e SET expires_at=p.expires_at
              FROM p WHERE e.id=p.id""")
            )
            session.commit()
        third = request(service, principal, ident, supersedes=second.operation_id)
        issue(service, execute_only, third)
        assert service.emergency_status(principal, third.operation_id).status == "issued"


def test_other_account_and_c2_unchanged(
    password_app: tuple[Settings, Database, str], tmp_path: Path
) -> None:
    settings, db, password = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        login_password(client, password)
        with closing(TestClient(client.app, base_url=ORIGIN)) as other:
            other_id = provision(client, other, password)
            service, principal, ident = operator(settings, db, tmp_path / "operator")
            req = request(service, principal, ident)
            with db.session() as s:
                # The other account also has expired state. AB5 must not collect it.
                s.execute(
                    text(
                        "UPDATE iam_credentials "
                        "SET expires_at=clock_timestamp()-interval '1 second' "
                        "WHERE account_id=:a"
                    ),
                    {"a": other_id},
                )
                s.commit()

            def snapshot() -> tuple[str, ...]:
                with db.session() as s:
                    values = []
                    for table in (
                        "iam_sessions",
                        "iam_mfa_contexts",
                        "iam_credentials",
                        "iam_recovery_credentials",
                        "iam_reset_credentials",
                        "iam_passkeys",
                    ):
                        values.append(
                            str(
                                s.execute(
                                    text(
                                        f"SELECT md5(COALESCE(string_agg(row_to_json(t)::text,',' "
                                        f"ORDER BY row_to_json(t)::text),'')) FROM {table} t "
                                        "WHERE account_id=:a"
                                    ),
                                    {"a": other_id},
                                ).scalar_one()
                            )
                        )
                    for table in ("iam_budgets", "iam_attempts", "iam_accounts"):
                        condition = " WHERE id=:a" if table == "iam_accounts" else ""
                        values.append(
                            str(
                                s.execute(
                                    text(
                                        f"SELECT md5(COALESCE(string_agg(row_to_json(t)::text,',' "
                                        f"ORDER BY row_to_json(t)::text),'')) FROM {table} t"
                                        + condition
                                    ),
                                    {"a": other_id},
                                ).scalar_one()
                            )
                        )
                    return tuple(values)

            before = snapshot()
            issue(service, principal, req)
            assert snapshot() == before


@pytest.mark.parametrize("failure", ["audit", "db", "ack"])
def test_atomic_issue_failures(
    password_app: tuple[Settings, Database, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    settings, db, password = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN):
        service, principal, ident = operator(settings, db, tmp_path / "operator")
        req = request(service, principal, ident)
        before = facts(db)
        original, commit = Audit.append_password_emergency, Session.commit

        def audit(adapter: Audit, event: Event) -> None:
            if event.action == "issue":
                if failure == "audit":
                    raise Rejected(503, "unavailable")
                if failure == "db":
                    adapter.s.execute(text("SELECT * FROM synthetic_missing_emergency_table"))
                adapter.s.info["emergency_ack"] = True
            original(adapter, event)

        def committed(s: Session) -> None:
            commit(s)
            if s.info.pop("emergency_ack", False):
                raise OperationalError("synthetic ACK loss", {}, RuntimeError("ack lost"))

        with monkeypatch.context() as patch:
            patch.setattr(Audit, "append_password_emergency", audit)
            patch.setattr(Session, "commit", committed)
            with pytest.raises(CommitUncertain if failure == "ack" else Rejected):
                issue(service, principal, req)
        if failure == "ack":
            assert service.emergency_status(principal, req.operation_id).status == "issued"
            assert facts(db)["password_reset_pending"]
            with pytest.raises(Rejected):
                issue(service, principal, req)
        else:
            assert facts(db) == before
            with db.session() as s:
                assert (
                    s.execute(
                        text("SELECT count(*) FROM iam_password_emergency_cases")
                    ).scalar_one()
                    == 0
                )


def test_password_proof_then_reissue_rejects_old_completion(
    password_app: tuple[Settings, Database, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings, db, password = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        service, principal, ident = operator(settings, db, tmp_path / "operator")
        req = request(service, principal, ident)
        raw = issue(service, principal, req)
        nonce = csrf(client)
        verified, release = Signal(), Signal()
        original = Emergency.prepare_password

        def held(adapter: Emergency, token: str, password: str) -> EmergencyPasswordProof:
            proof = original(adapter, token, password)
            verified.set()
            assert release.wait(15)
            return proof

        with monkeypatch.context() as patch, ThreadPoolExecutor(max_workers=1) as pool:
            patch.setattr(Emergency, "prepare_password", held)
            pending = pool.submit(
                call,
                client,
                "/auth/emergency-recovery/password/complete",
                nonce,
                {"emergency_token": raw, "new_password": password},
            )
            try:
                assert verified.wait(10)
                issue(service, principal, request(service, principal, ident, req.operation_id))
            finally:
                release.set()
            assert pending.result(timeout=15).status_code == 401
        assert facts(db)["password_reset_pending"]


def test_gc_preserves_case_and_locked_source(
    password_app: tuple[Settings, Database, str], tmp_path: Path
) -> None:
    from tests.test_iam_emergency_handoff import expire_case

    settings, db, _ = password_app
    service, principal, ident = operator(settings, db, tmp_path / "operator")
    req = request(service, principal, ident)
    issue(service, principal, req)
    expire_case(db, req.operation_id)
    with db.session() as locked:
        locked.execute(text("SELECT id FROM iam_password_emergency_credentials FOR UPDATE")).one()
        with service.uow.open() as work:
            slot = work.security.allocate("preparation")
        assert (
            locked.execute(
                text("SELECT count(*) FROM iam_password_emergency_credentials")
            ).scalar_one()
            == 1
        )
    with service.uow.open() as work:
        work.security.release(slot)
    with db.session() as session:
        assert (
            session.execute(
                text("SELECT count(*) FROM iam_password_emergency_credentials")
            ).scalar_one()
            == 0
        )
        assert (
            session.execute(text("SELECT count(*) FROM iam_password_emergency_cases")).scalar_one()
            == 1
        )
    with pytest.raises(Rejected):
        issue(
            service,
            principal,
            replace(
                request(service, principal, ident, req.operation_id), approval_ref=req.approval_ref
            ),
        )


def test_normal_pending_allows_explicit_password_emergency(
    password_app: tuple[Settings, Database, str],
    tmp_path: Path,
) -> None:
    from tests.password_helpers import reset_request

    settings, db, password = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as first:
        login_password(first, password)
        with closing(TestClient(first.app, base_url=ORIGIN)) as second:
            provision(first, second, password)
            service, principal, ident = operator(settings, db, tmp_path / "operator")
            assert reset_request(second, str(ident)).status_code == 201
            issue(service, principal, request(service, principal, ident))
            assert facts(db)["password_reset_pending"] and not facts(db)["recovery_pending"]


@pytest.mark.parametrize("failure", ["audit", "expired", "purpose"])
def test_password_completion_failure_preserves_pending(
    password_app: tuple[Settings, Database, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    from tests.test_iam_emergency_handoff import expire_case

    settings, db, password = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        login_password(client, password)
        service, principal, ident = operator(settings, db, tmp_path / "operator")
        req = request(service, principal, ident)
        raw = issue(service, principal, req)
        before = facts(db)

        def audit(adapter: Audit, event: Event) -> None:
            raise Rejected(503, "unavailable")

        if failure == "expired":
            expire_case(db, req.operation_id)
        with monkeypatch.context() as patch:
            if failure == "audit":
                patch.setattr(Audit, "append_password_emergency", audit)
            path = (
                "/auth/password-reset/complete"
                if failure == "purpose"
                else "/auth/emergency-recovery/password/complete"
            )
            field = "reset_token" if failure == "purpose" else "emergency_token"
            nonce = csrf(client)
            cookies_before = dict(client.cookies)
            assert "__Host-y3-auth" in cookies_before
            assert "__Host-y3-preauth" in cookies_before
            response = call(client, path, nonce, {field: raw, "new_password": password})
        assert response.status_code == (503 if failure == "audit" else 401)
        assert not response.response.headers.get_list("set-cookie")
        assert dict(client.cookies) == cookies_before
        assert facts(db) == before
        with db.session() as session:
            assert (
                session.execute(
                    text(
                        "SELECT count(*) FROM iam_password_emergency_cases WHERE completed_at "
                        "IS NOT NULL"
                    )
                ).scalar_one()
                == 0
            )


@pytest.mark.parametrize(
    "failure",
    [
        "delivery",
        "ack",
        "close",
        "stdout_write",
        "stdout_flush",
        "db_close",
        "guard_close",
        "ack_stderr",
        "interrupt",
        "system_exit",
    ],
)
def test_cli_actual_commit_unknown_keeps_private_output(
    password_app: tuple[Settings, Database, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    failure: str,
) -> None:
    import json
    import sys
    from dataclasses import asdict

    from y3management import cli

    settings, db, password = password_app
    private = tmp_path / "operator"
    with TestClient(create_app(settings, database=db), base_url=ORIGIN):
        service, principal, ident = operator(settings, db, private)
        req = request(service, principal, ident)
    body = asdict(req)
    body.update(
        environment="test",
        database="y3management_test",
        database_schema=settings.database_schema,
        revocation_scope="target_only",
        manual_checks="owner_authority_original_current_recipient_all_masters_unavailable",
        approval_conditions="issuance_only_no_additional_conditions",
    )
    source, output = private / "request", private / "delivery"
    source.write_text(json.dumps(body, default=str))
    source.chmod(0o600)
    configured = settings.model_copy(
        update={
            "emergency_authority_file": str(private / "authority.json"),
            "emergency_test_authority": True,
        }
    )
    original, commit, deliver = (
        Audit.append_password_emergency,
        Session.commit,
        cli.PrivateRecoveryFile.deliver,
    )
    close = cli.PrivateRecoveryFile.close
    db_close, guard_close = Database.close, ProcessGuard.close

    def audit(adapter: Audit, event: Event) -> None:
        original(adapter, event)
        if event.action == "issue":
            adapter.s.info["emergency_ack"] = True

    def committed(s: Session) -> None:
        commit(s)
        if s.info.pop("emergency_ack", False):
            if failure == "interrupt":
                raise KeyboardInterrupt()
            if failure == "system_exit":
                raise SystemExit(130)
            raise OperationalError("synthetic ACK loss", {}, RuntimeError("ack lost"))

    def delivery(adapter: cli.PrivateRecoveryFile, setup: Setup) -> None:
        deliver(adapter, setup)
        raise OSError("synthetic fsync failure after write")

    def close_failed(adapter: cli.PrivateRecoveryFile, *, remove: bool) -> None:
        close(adapter, remove=remove)
        raise OSError("synthetic close failure")

    def database_close_failed(adapter: Database) -> None:
        db_close(adapter)
        raise OSError("synthetic database close failure")

    def guard_close_failed(adapter: ProcessGuard) -> None:
        guard_close(adapter)
        raise OSError("synthetic guard close failure")

    def broken_stream(*args: object, **kwargs: object) -> None:
        raise BrokenPipeError("synthetic receipt or diagnostic sink failure")

    before = facts(db)
    with monkeypatch.context() as patch:
        patch.setattr(cli, "load_settings", lambda: configured)
        patch.setattr(sys.stdin, "isatty", lambda: True)
        patch.setattr(
            sys,
            "argv",
            [
                "cli",
                "emergency-recovery",
                "execute",
                "--organization-id",
                str(req.organization_id),
                "--confirm-database",
                "y3management_test",
                "--confirm-schema",
                settings.database_schema,
                "--request-file",
                str(source),
                "--output-file",
                str(output),
            ],
        )
        if failure in ("ack", "ack_stderr", "interrupt", "system_exit"):
            patch.setattr(Audit, "append_password_emergency", audit)
            patch.setattr(Session, "commit", committed)
            if failure == "ack_stderr":
                patch.setattr(sys.stderr, "write", broken_stream)
        elif failure == "stdout_write":
            patch.setattr(sys.stdout, "write", broken_stream)
        elif failure == "stdout_flush":
            patch.setattr(sys.stdout, "flush", broken_stream)
        elif failure == "db_close":
            patch.setattr(Database, "close", database_close_failed)
        elif failure == "guard_close":
            patch.setattr(ProcessGuard, "close", guard_close_failed)
        elif failure == "close":
            patch.setattr(cli.PrivateRecoveryFile, "close", close_failed)
        else:
            patch.setattr(cli.PrivateRecoveryFile, "deliver", delivery)
        assert cli.main() == (1 if failure == "delivery" else 2)
    captured = capsys.readouterr()
    assert "#token=" not in captured.out + captured.err
    if failure != "delivery":
        assert output.exists() and output.stat().st_mode & 0o777 == 0o600
        assert service.emergency_status(principal, req.operation_id).status == "issued"
    else:
        assert not output.exists() and facts(db) == before


@pytest.mark.parametrize("legacy_master", ["0008_iam_emergency_recovery"], indirect=True)
def test_migration_roundtrip_and_durable_history_guard(
    legacy_master: tuple[Settings, Database],
) -> None:
    from tests.legacy_helpers import assert_revision_loss_guard, migration_status
    from tests.test_password_transition import fingerprint
    from tests.test_password_transition_legacy import seed_case

    settings, db = legacy_master
    before = fingerprint(db)
    assert migration_status(settings, "downgrade", "0007_iam_password_reset") == 0
    assert migration_status(settings, "upgrade", "0008_iam_emergency_recovery") == 0
    assert fingerprint(db) == before
    seed_case(db)
    before = fingerprint(db)
    assert migration_status(settings, "downgrade", "0007_iam_password_reset") != 0
    assert_revision_loss_guard(db, "0008_iam_emergency_recovery.py", "prevents downgrade")
    assert fingerprint(db) == before


def test_pre_hash_trainer_epoch_change_rejects_proof_but_preserves_source(
    password_app: tuple[Settings, Database, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests.test_iam_trainer import TrainerScene
    from tests.test_iam_trainer_roles import change
    from tests.test_iam_trainer_roles_security import link
    from tests.test_workforce import Scene
    from y3management.iam.passwords import Passwords

    settings, db, password = password_app
    with (
        TestClient(create_app(settings, database=db), base_url=ORIGIN) as recipient,
        closing(TestClient(recipient.app, base_url=ORIGIN)) as actor,
    ):
        login_password(recipient, password)
        ident_text = recipient.get("/api/v1/auth/me").json()["account_id"]
        provision(recipient, actor, password)
        branch = call(actor, "/admin/branches", csrf(actor), {"code": "EPOCH", "name": "가상 지점"})
        assert branch.status_code == 201
        base = Scene(actor, db, branch.json()["id"])
        employee = base.send(base.body())
        assert employee.status_code == 201
        mixed = TrainerScene(
            base, employee.json()["trainer"]["id"], recipient, password, "master.test"
        )
        assert change(mixed, link(mixed, ident_text, "master.test")).status_code == 200
        login_password(recipient, password)
        assert {r["role"] for r in recipient.get("/api/v1/auth/me").json()["roles"]} == {
            "ADMIN",
            "TRAINER",
        }
        service, principal, ident = operator(settings, db, tmp_path / "operator")
        req = request(service, principal, ident)
        raw = issue(service, principal, req)
        nonce = csrf(recipient)
        with db.session() as session:
            before = tuple(
                session.execute(
                    text(
                        "SELECT row_version,security_version,reset_generation,trainer_role_epoch "
                        "FROM iam_accounts WHERE id=:a"
                    ),
                    {"a": ident},
                ).one()
            )
            expiry = session.execute(
                text(
                    "SELECT expires_at FROM iam_password_emergency_credentials WHERE account_id=:a"
                ),
                {"a": ident},
            ).scalar_one()
            source_before = session.execute(
                text(
                    "SELECT md5(row_to_json(e)::text) FROM "
                    "iam_password_emergency_credentials e WHERE account_id=:a"
                ),
                {"a": ident},
            ).scalar_one()
        reached, release = Signal(), Signal()
        create = Passwords.create
        prepare = Emergency.prepare_password
        proof_pids: list[int] = []

        def observed(adapter: Emergency, token: str, value: str) -> EmergencyPasswordProof:
            proof_pids.append(int(adapter.s.execute(text("SELECT pg_backend_pid()")).scalar_one()))
            return prepare(adapter, token, value)

        def held(adapter: Passwords, value: str, login_id: str) -> str:
            # prepare_password has already read target epochs; hashing has not started.
            reached.set()
            assert release.wait(15)
            return create(adapter, value, login_id)

        with monkeypatch.context() as patch, ThreadPoolExecutor(max_workers=1) as pool:
            patch.setattr(Passwords, "create", held)
            patch.setattr(Emergency, "prepare_password", observed)
            completion = pool.submit(
                call,
                recipient,
                "/auth/emergency-recovery/password/complete",
                nonce,
                {"emergency_token": raw, "new_password": password},
            )
            try:
                assert reached.wait(10)
                # Controlled independent epoch-only SQL, not an invented role workflow.
                with db.session() as other:
                    writer_pid = int(other.execute(text("SELECT pg_backend_pid()")).scalar_one())
                    assert len(proof_pids) == 1 and writer_pid != proof_pids[0]
                    other.execute(
                        text(
                            "UPDATE iam_accounts SET trainer_role_epoch=trainer_role_epoch+1 "
                            "WHERE id=:a"
                        ),
                        {"a": ident},
                    )
                    other.execute(
                        text(
                            "UPDATE iam_trainer_role_grants SET role_version=role_version+1 "
                            "WHERE account_id=:a"
                        ),
                        {"a": ident},
                    )
                    other.commit()
            finally:
                release.set()
            assert completion.result(timeout=15).status_code == 401
        with db.session() as session:
            after = tuple(
                session.execute(
                    text(
                        "SELECT row_version,security_version,reset_generation,trainer_role_epoch "
                        "FROM iam_accounts WHERE id=:a"
                    ),
                    {"a": ident},
                ).one()
            )
            assert after == (*before[:3], before[3] + 1)
            assert (
                session.execute(
                    text(
                        "SELECT md5(row_to_json(e)::text) FROM "
                        "iam_password_emergency_credentials e WHERE account_id=:a"
                    ),
                    {"a": ident},
                ).scalar_one()
                == source_before
            )
            assert (
                session.execute(
                    text(
                        "SELECT count(*) FROM audit_password_emergency_events "
                        "WHERE target_id=:a AND action='complete'"
                    ),
                    {"a": ident},
                ).scalar_one()
                == 0
            )
            assert tuple(
                session.execute(
                    text(
                        "SELECT consumed,expires_at FROM "
                        "iam_password_emergency_credentials WHERE account_id=:a"
                    ),
                    {"a": ident},
                ).one()
            ) == (False, expiry)
            assert (
                session.execute(
                    text("SELECT password_reset_pending FROM iam_accounts WHERE id=:a"),
                    {"a": ident},
                ).scalar_one()
                is True
            )
        assert (
            call(
                recipient,
                "/auth/emergency-recovery/password/complete",
                nonce,
                {"emergency_token": raw, "new_password": password},
            ).status_code
            == 204
        )
        with db.session() as session:
            assert tuple(
                session.execute(
                    text(
                        "SELECT consumed,expires_at FROM "
                        "iam_password_emergency_credentials WHERE account_id=:a"
                    ),
                    {"a": ident},
                ).one()
            ) == (True, expiry)

        assert recipient.get("/api/v1/auth/me").status_code == 401
        assert actor.get("/api/v1/auth/me").status_code == 200
        login_password(recipient, password)
