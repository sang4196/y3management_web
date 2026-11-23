# ruff: noqa: F811
"""WF3 current Home authority, actor-bound receipts and preserved identity axes."""

from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import text

from tests.password_helpers import call, password_app  # noqa: F401
from tests.test_iam import ORIGIN, csrf
from tests.test_iam_trainer import TrainerScene, source, trainer  # noqa: F401
from tests.test_iam_trainer_roles import body as role_body
from tests.test_iam_trainer_roles import change as role_change
from tests.test_operator_management import role_headers
from tests.test_workforce import activity, scene  # noqa: F401
from tests.test_workforce_state import change as state_change
from tests.test_workforce_state import request as state_request
from y3management.audit.infrastructure import Audit
from y3management.contracts import Rejected

pytestmark = pytest.mark.postgres


def destination(t: TrainerScene) -> str:
    r = call(
        t.base.client,
        "/admin/branches",
        csrf(t.base.client),
        {"code": "DEST", "name": "가상 목적지"},
    )
    assert r.status_code == 201
    return str(r.json()["id"])


def body(t: TrainerScene, home: str) -> dict[str, Any]:
    version = t.base.client.get("/api/v1/admin/trainers/" + t.trainer).json()["version"]
    return dict(
        operation_id=str(uuid4()), destination_home_branch_id=home, expected_trainer_version=version
    )


def move(t: TrainerScene, command: dict[str, Any]) -> Any:
    return t.base.client.post(
        "/api/v1/admin/trainers/" + t.trainer + "/home",
        headers={
            **role_headers(t.base.client),
            "Origin": ORIGIN,
            "X-CSRF-Token": csrf(t.base.client),
        },
        json=command,
    )


def receipt(t: TrainerScene, command: dict[str, Any]) -> Any:
    return t.base.client.get(
        "/api/v1/admin/trainer-home-operations/" + command["operation_id"],
        headers=role_headers(t.base.client),
    )


def preserved(t: TrainerScene) -> dict[str, Any]:
    with t.base.db.session() as s:
        tables = (
            "iam_accounts",
            "iam_sessions",
            "iam_trainer_bindings",
            "iam_trainer_role_grants",
            "iam_trainer_setup_credentials",
            "iam_reset_credentials",
            "iam_password_emergency_credentials",
            "workforce_initial_snapshots",
            "workforce_registration_operations",
            "workforce_trainer_state_origins",
            "workforce_trainer_state_operations",
            "workforce_trainer_state_transitions",
            "audit_workforce_initial_events",
        )
        result = {
            table: s.execute(text("SELECT * FROM " + table + " ORDER BY 1")).all()
            for table in tables
        }
        result["trainer_values"] = s.execute(
            text("""SELECT id,organization_id,name,phone,
            active,created_at,rate_percent,fixed_amount_won,base_salary_won,
            base_salary_start_month FROM workforce_trainers ORDER BY id""")
        ).all()
        return result


@pytest.mark.parametrize(
    "state",
    [
        "unbound",
        "pending",
        "active",
        "inactive",
        "withdrawn",
        "disabled",
        "reset",
        "restore_disabled",
    ],
)
def test_move_preserves_identity_states(trainer: TrainerScene, state: str) -> None:
    t = trainer
    dest = destination(t)
    token = ""
    if state != "unbound":
        token = source(t.issue())
    if state in {"active", "withdrawn", "disabled", "reset", "restore_disabled"}:
        assert t.complete(token).status_code == 204
        assert t.signin().status_code == 204
    if state == "inactive":
        assert state_change(t, state_request(t, False)).status_code == 200
    if state == "withdrawn":
        assert role_change(t, role_body(t, False)).status_code == 200
    if state == "disabled":
        with t.base.db.session() as s:
            s.execute(
                text("UPDATE iam_accounts SET restore_state=state,state='DISABLED' WHERE id=:i"),
                {"i": t.state()["account_id"]},
            )
            s.commit()
    if state in {"reset", "restore_disabled"}:
        # Use the actual reset workflow; recovery purpose below remains independently stored.
        ident = t.state()["account_id"]
        if state == "reset":
            from tests.password_helpers import call

            account = t.base.client.get(
                "/api/v1/admin/accounts/" + ident + "/password-reset"
            ).json()
            response = call(
                t.base.client,
                "/admin/accounts/" + ident + "/password-reset",
                csrf(t.base.client),
                {
                    "expected_account_version": account["account_version"],
                    "expected_generation": account["generation"],
                    "identity_confirmed": True,
                },
            )
            assert response.status_code == 201
        else:
            # Recovery account state is modeled by original IAM's disabled restore purpose.
            with t.base.db.session() as s:
                s.execute(
                    text(
                        "UPDATE iam_accounts SET restore_state='ACTIVE',state='DISABLED' "
                        "WHERE id=:i"
                    ),
                    {"i": ident},
                )
                s.commit()
    command = body(t, dest)
    before = preserved(t)
    response = move(t, command)
    assert response.status_code == 200
    data = response.json()
    assert data["changed"] and data["committed_home_branch_id"] == dest
    assert data["before_home_branch_id"] == t.base.branch
    assert data["committed_trainer_version"] == command["expected_trainer_version"] + 1
    after = preserved(t)
    # Real successful command touches only the acting session's activity.
    assert {k: v for k, v in before.items() if k != "iam_sessions"} == {
        k: v for k, v in after.items() if k != "iam_sessions"
    }
    if state == "pending":
        assert t.complete(token).status_code == 204
    if state == "active":
        assert t.recipient.get("/api/v1/auth/me").status_code == 200


def test_noop_replay_current_receipt_and_shared_state_version(trainer: TrainerScene) -> None:
    t = trainer
    dest = destination(t)
    with t.base.db.session() as s:
        s.execute(
            text("UPDATE organization_branches SET active=false WHERE id=:b"), {"b": t.base.branch}
        )
        s.commit()
    noop = body(t, t.base.branch)
    before = activity(t.base.db)
    assert move(t, noop).json()["changed"] is False
    assert move(t, noop).json()["changed"] is False
    assert activity(t.base.db) == before
    stale_state = state_request(t, False)
    command = body(t, dest)
    first = move(t, command)
    assert first.status_code == 200
    assert state_change(t, stale_state).status_code == 409
    assert move(t, {**command, "operation_id": str(uuid4())}).status_code == 409
    assert move(t, {**command, "destination_home_branch_id": t.base.branch}).status_code == 409
    assert state_change(t, state_request(t, False)).status_code == 200
    before = activity(t.base.db)
    replay = move(t, command)
    assert replay.status_code == 200
    assert replay.json()["committed_trainer_version"] == first.json()["committed_trainer_version"]
    assert (
        replay.json()["current_state"]["version"] == first.json()["committed_trainer_version"] + 1
    )
    assert receipt(t, command).json() == replay.json()
    assert activity(t.base.db) == before
    with t.base.db.session() as s:
        for table in ("workforce_trainer_home_transitions", "audit_trainer_home_events"):
            assert s.execute(text("SELECT count(*) FROM " + table)).scalar_one() == 1


def test_transport_authority_and_audit_atomicity(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch
) -> None:
    t = trainer
    dest = destination(t)
    command = body(t, dest)
    path = "/api/v1/admin/trainers/" + t.trainer + "/home"
    assert (
        t.base.client.post(
            path, headers={"Origin": ORIGIN, "X-CSRF-Token": csrf(t.base.client)}, json=command
        ).status_code
        == 422
    )
    assert (
        t.base.client.post(
            path,
            headers={
                "Origin": ORIGIN,
                "X-CSRF-Token": csrf(t.base.client),
                "X-Y3-Expected-Actor": str(uuid4()),
            },
            json=command,
        ).status_code
        == 409
    )

    assert (
        t.base.client.post(
            path,
            headers={
                **role_headers(t.base.client),
                "Origin": ORIGIN,
                "X-CSRF-Token": "synthetic-invalid",
            },
            json=command,
        ).status_code
        == 403
    )

    def fail(*args: Any) -> None:
        raise Rejected(503, "unavailable")

    monkeypatch.setattr(Audit, "append_trainer_home", fail)
    before = activity(t.base.db)
    assert move(t, command).status_code == 503
    assert body(t, dest)["expected_trainer_version"] == command["expected_trainer_version"]
    assert receipt(t, command).status_code == 404
    assert activity(t.base.db) == before


def test_current_home_w0_and_account_authority(trainer: TrainerScene, password_app: Any) -> None:
    from contextlib import closing

    from tests.test_workforce_integrity import branch_actor

    t = trainer
    dest = destination(t)
    original = t.base.body()
    r = t.base.send(original)
    ident = r.json()["trainer"]["id"]
    state_command = state_request(t, False)
    assert state_change(t, state_command).status_code == 200
    command = body(t, dest)
    with closing(branch_actor(t.base, password_app[2])) as old:
        assert old.get("/api/v1/admin/trainers/" + t.trainer).status_code == 200
        assert (
            old.post(
                "/api/v1/admin/trainers/" + t.trainer + "/home",
                headers={**role_headers(old), "Origin": ORIGIN, "X-CSRF-Token": csrf(old)},
                json=command,
            ).status_code
            == 403
        )
        assert move(t, command).status_code == 200
        assert old.get("/api/v1/admin/trainers/" + t.trainer).status_code == 404
        assert old.get("/api/v1/admin/trainers/" + t.trainer + "/login-account").status_code == 404
        assert (
            old.get(
                "/api/v1/admin/trainer-state-operations/" + state_command["operation_id"]
            ).status_code
            == 404
        )
    # Move the second Trainer whose registration command is retained exactly.
    target = TrainerScene(t.base, ident, t.recipient, t.password, t.login)
    assert move(target, body(target, dest)).status_code == 200
    assert t.base.send(original).json()["trainer"]["home_branch_id"] == dest
    assert t.base.send({**original, "home_branch_id": dest}).status_code == 409
    from fastapi.testclient import TestClient

    from tests.password_helpers import activate, login_password

    issued = call(
        t.base.client,
        "/admin/accounts",
        csrf(t.base.client),
        {"login_id": "new.home.admin", "branch_id": dest},
    )
    with closing(TestClient(t.base.client.app, base_url=ORIGIN)) as new:
        activate(new, issued.json()["setup_link"].split("#token=")[1], password_app[2])
        login_password(new, password_app[2], "new.home.admin")
        response = call(new, "/admin/trainers", csrf(new), original)
        assert response.status_code == 200 and response.json()["trainer"]["home_branch_id"] == dest
        assert (
            new.get("/api/v1/admin/trainer-registrations/" + original["operation_id"]).status_code
            == 200
        )
        assert new.get("/api/v1/admin/trainers/" + t.trainer + "/login-account").status_code == 200
        assert (
            new.get(
                "/api/v1/admin/trainer-state-operations/" + state_command["operation_id"]
            ).status_code
            == 200
        )


def test_receipt_is_original_actor_bound(trainer: TrainerScene, password_app: Any) -> None:
    from contextlib import closing

    from fastapi.testclient import TestClient

    from tests.password_helpers import provision

    t = trainer
    dest = destination(t)
    command = body(t, dest)
    assert move(t, command).status_code == 200
    with closing(TestClient(t.base.client.app, base_url=ORIGIN)) as other:
        provision(t.base.client, other, password_app[2])
        response = other.get(
            "/api/v1/admin/trainer-home-operations/" + command["operation_id"],
            headers=role_headers(other),
        )
        assert response.status_code == 404
        response = other.post(
            "/api/v1/admin/trainers/" + t.trainer + "/home",
            headers={**role_headers(other), "Origin": ORIGIN, "X-CSRF-Token": csrf(other)},
            json=command,
        )
        assert response.status_code in (404, 409)


def test_inactive_foreign_destination_and_expired_source(trainer: TrainerScene) -> None:
    t = trainer
    dest = destination(t)
    token = source(t.issue())
    with t.base.db.session() as s:
        s.execute(text("UPDATE organization_branches SET active=false WHERE id=:b"), {"b": dest})
        s.execute(
            text(
                "UPDATE iam_trainer_setup_credentials SET "
                "expires_at=clock_timestamp()-interval '1 second'"
            )
        )
        s.commit()
    command = body(t, dest)
    assert move(t, command).status_code == 409
    assert move(t, {**command, "destination_home_branch_id": str(uuid4())}).status_code == 404
    with t.base.db.session() as s:
        s.execute(text("UPDATE organization_branches SET active=true WHERE id=:b"), {"b": dest})
        s.commit()
    assert move(t, command).status_code == 200
    assert t.complete(token).status_code == 400
    assert t.state()["state"] == "PENDING_SETUP"


@pytest.mark.parametrize("kind", ["home", "state"])
def test_serialized_commands_observe_move_and_stale_version(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from tests.test_workforce_integrity import observe_waiter, wait_for_owned_block

    t = trainer
    dest = destination(t)
    command = body(t, dest)
    stale = state_request(t, False)
    reached, release = Event(), Event()
    holders = []
    original = Audit.append_trainer_home

    def pause(self: Audit, *args: Any) -> None:
        original(self, *args)
        holders.append(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one())
        reached.set()
        assert release.wait(15)

    monkeypatch.setattr(Audit, "append_trainer_home", pause)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(move, t, command)
        capture = None
        try:
            assert reached.wait(5)
            waiters: list[int] = []
            capture = observe_waiter(t.base.db, waiters)
            second = (
                pool.submit(move, t, command)
                if kind == "home"
                else pool.submit(state_change, t, stale)
            )
            wait_for_owned_block(t.base.db, holders[0], waiters)
        finally:
            release.set()
            if capture is not None:
                from sqlalchemy import event as sa_event

                sa_event.remove(t.base.db.engine, "before_cursor_execute", capture)
        assert first.result(timeout=10).status_code == 200
        assert second.result(timeout=10).status_code == (200 if kind == "home" else 409)
    with t.base.db.session() as s:
        assert s.execute(text("SELECT count(*) FROM audit_trainer_home_events")).scalar_one() == 1


@pytest.mark.parametrize("absolute", [False, True])
def test_home_final_actor_read_crosses_original_deadline(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch, absolute: bool
) -> None:
    from y3management.iam.public import Authentication
    from y3management.iam.roles import TrainerRoles

    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    assert t.signin().status_code == 204
    payload = body(t, destination(t))
    nonce = csrf(t.base.client)
    actor = t.base.client.get("/api/v1/auth/me").json()["account_id"]
    with t.base.db.session() as s:
        session_query = text(
            "SELECT id,revoked FROM iam_sessions WHERE account_id="
            "(SELECT account_id FROM iam_trainer_bindings WHERE trainer_id=:t) ORDER BY id"
        )
        target_sessions = s.execute(session_query, {"t": t.trainer}).all()
        assert target_sessions and all(not row.revoked for row in target_sessions)
        if absolute:
            s.execute(
                text("""WITH shifted AS (UPDATE iam_security_states
                SET expires_at=clock_timestamp()+interval '2 seconds'
                WHERE id IN (SELECT id FROM iam_sessions WHERE account_id=:a)
                RETURNING id,expires_at)
                UPDATE iam_sessions s SET expires_at=shifted.expires_at,
                created_at=shifted.expires_at-interval '8 hours',
                last_activity=shifted.expires_at-interval '1 minute'
                FROM shifted WHERE s.id=shifted.id"""),
                {"a": actor},
            )
        else:
            s.execute(
                text(
                    "UPDATE iam_sessions SET "
                    "created_at=clock_timestamp()-interval '31 minutes',"
                    "last_activity=clock_timestamp()-interval '29 minutes 58 seconds' "
                    "WHERE account_id=:a"
                ),
                {"a": actor},
            )
        s.commit()
    original = TrainerRoles.stable_actor
    observations: list[tuple[bool, bool]] = []
    reads = 0

    def delayed(self: TrainerRoles, authentication: Authentication) -> bytes:
        nonlocal reads
        reads += 1
        value = original(self, authentication)
        if reads == 2:
            query = text(
                "SELECT last_activity+interval '30 minutes'>clock_timestamp(),"
                "expires_at>clock_timestamp() FROM iam_sessions WHERE id=:i"
            )
            row = self.s.execute(query, {"i": authentication.session_id}).one()
            observations.append((bool(row[0]), bool(row[1])))
            self.s.execute(text("SELECT pg_sleep(1.1)"))
            self.s.execute(text("SELECT pg_sleep(1.1)"))
            row = self.s.execute(query, {"i": authentication.session_id}).one()
            observations.append((bool(row[0]), bool(row[1])))
        return value

    monkeypatch.setattr(TrainerRoles, "stable_actor", delayed)
    response = t.base.client.post(
        "/api/v1/admin/trainers/" + t.trainer + "/home",
        headers={**role_headers(t.base.client), "Origin": ORIGIN, "X-CSRF-Token": nonce},
        json=payload,
    )
    assert response.status_code == 401
    assert observations[0] == (True, True)
    assert observations[1][1 if absolute else 0] is False
    with t.base.db.session() as s:
        assert s.execute(text("SELECT active FROM workforce_trainers")).scalar_one()
        assert (
            s.execute(text("SELECT count(*) FROM workforce_trainer_home_operations")).scalar_one()
            == 0
        )
        assert s.execute(text("SELECT count(*) FROM audit_trainer_state_events")).scalar_one() == 0
        assert s.execute(session_query, {"t": t.trainer}).all() == target_sessions

    assert t.recipient.get("/api/v1/auth/me").status_code == 200


def test_binding_created_while_home_waits_rejects_stale_hint(
    trainer: TrainerScene, password_app: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from contextlib import closing
    from threading import Event, get_ident

    from sqlalchemy import event as sa_event

    from tests.test_workforce_integrity import branch_actor, observe_waiter, wait_for_owned_block
    from y3management.iam.infrastructure import IAM

    t = trainer
    dest = destination(t)
    command = body(t, dest)
    before_update, continue_home, issued, release_issue = Event(), Event(), Event(), Event()
    home_thread: list[int] = []
    holders = []
    authenticate = IAM.authenticate
    append = Audit.append_trainer_identity
    home_authentications = 0

    def paused_authenticate(self: IAM, *args: Any, **kw: Any) -> Any:
        nonlocal home_authentications
        if home_thread and get_ident() == home_thread[0]:
            home_authentications += 1
            if home_authentications == 2:
                # Actual IAM globally serializes final UoWs at installation FOR UPDATE.
                # Pause before that gate; never bypass it to manufacture a Trainer-only race.
                before_update.set()
                assert continue_home.wait(15)
        return authenticate(self, *args, **kw)

    def paused_issue(self: Audit, *args: Any) -> None:
        append(self, *args)
        holders.append(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one())
        issued.set()
        assert release_issue.wait(15)

    from y3management.use_cases import Service

    service_home = Service.change_trainer_home

    def marked_home(self: Service, *args: Any, **kwargs: Any) -> Any:
        home_thread.append(get_ident())
        return service_home(self, *args, **kwargs)

    with closing(branch_actor(t.base, password_app[2])) as ba:
        branch_nonce = csrf(ba)
        monkeypatch.setattr(Service, "change_trainer_home", marked_home)
        monkeypatch.setattr(IAM, "authenticate", paused_authenticate)
        monkeypatch.setattr(Audit, "append_trainer_identity", paused_issue)
        with ThreadPoolExecutor(max_workers=2) as pool:
            home = pool.submit(move, t, command)
            capture = None
            try:
                assert before_update.wait(5)
                issuance = pool.submit(
                    call,
                    ba,
                    "/admin/trainers/" + t.trainer + "/login-account",
                    branch_nonce,
                    {"operation_id": str(uuid4()), "login_id": t.login},
                )
                assert issued.wait(5)
                waiters: list[int] = []
                capture = observe_waiter(t.base.db, waiters)
                continue_home.set()
                wait_for_owned_block(t.base.db, holders[0], waiters)
            finally:
                continue_home.set()
                release_issue.set()
                if capture is not None:
                    sa_event.remove(t.base.db.engine, "before_cursor_execute", capture)
            assert issuance.result(timeout=10).status_code == 201
            assert home.result(timeout=10).status_code == 409
    assert receipt(t, command).status_code == 404
    original = preserved(t)
    assert move(t, command).status_code == 200
    assert {k: v for k, v in preserved(t).items() if k != "iam_sessions"} == {
        k: v for k, v in original.items() if k != "iam_sessions"
    }


def test_emergency_original_source_and_independent_master_scope_survive_move(
    trainer: TrainerScene, password_app: Any, tmp_path: Any
) -> None:
    from contextlib import closing

    from fastapi.testclient import TestClient

    from tests.password_helpers import login_password, provision
    from tests.test_iam_emergency import issue, operator
    from tests.test_iam_emergency import request as emergency_request
    from tests.test_iam_trainer_roles_security import link

    t = trainer
    dest = destination(t)
    master = t.base.client.get("/api/v1/auth/me").json()["account_id"]
    with closing(TestClient(t.base.client.app, base_url=ORIGIN)) as other:
        provision(t.base.client, other, password_app[2])
        assert role_change(t, link(t, master, "master.test")).status_code == 200
        login_password(t.base.client, password_app[2])
        service, principal, target = operator(password_app[0], t.base.db, tmp_path / "operator")
        token = issue(service, principal, emergency_request(service, principal, target))
        command = body_for_other(other, t.trainer, dest)
        before = preserved(t)
        response = other.post(
            "/api/v1/admin/trainers/" + t.trainer + "/home",
            headers={**role_headers(other), "Origin": ORIGIN, "X-CSRF-Token": csrf(other)},
            json=command,
        )
        assert response.status_code == 200
        assert {k: v for k, v in before.items() if k != "iam_sessions"} == {
            k: v for k, v in preserved(t).items() if k != "iam_sessions"
        }
        response = call(
            t.recipient,
            "/auth/emergency-recovery/password/complete",
            csrf(t.recipient),
            {"emergency_token": token, "new_password": t.password},
        )
        assert response.status_code == 204
        login_password(t.base.client, t.password)
        roles = t.base.client.get("/api/v1/auth/me").json()["roles"]
        assert any(r["role"] == "ADMIN" and r["scope"] == "ORGANIZATION" for r in roles)
        assert any(r["role"] == "TRAINER" for r in roles)


def body_for_other(client: Any, trainer_id: str, home: str) -> dict[str, Any]:
    current = client.get("/api/v1/admin/trainers/" + trainer_id).json()
    return {
        "operation_id": str(uuid4()),
        "destination_home_branch_id": home,
        "expected_trainer_version": current["version"],
    }
