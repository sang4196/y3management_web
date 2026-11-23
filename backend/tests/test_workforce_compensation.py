# ruff: noqa: F811
"""WF4 exact values, current authority, actor receipts and independent state axes."""

from contextlib import closing
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import text

from tests.password_helpers import PrivateResponse, call, login_password
from tests.test_iam import ORIGIN, csrf
from tests.test_iam_trainer import (
    TrainerScene,
    source,
    trainer,  # noqa: F401
)
from tests.test_operator_management import role_headers
from tests.test_workforce import (
    activity,
    scene,  # noqa: F401
)
from tests.test_workforce_home import body as home_body
from tests.test_workforce_home import destination, move
from tests.test_workforce_integrity import branch_actor
from tests.test_workforce_state import change as state_change
from tests.test_workforce_state import request as state_request
from y3management.audit.infrastructure import Audit
from y3management.contracts import Rejected

pytestmark = pytest.mark.postgres


def get(t: TrainerScene, suffix: str = "compensation", client: Any = None) -> Any:
    c = client or t.base.client
    return c.get("/api/v1/admin/trainers/" + t.trainer + "/" + suffix, headers=role_headers(c))


def body(
    t: TrainerScene, rate: int = 50, fixed: str = "9007199254740993", client: Any = None
) -> dict[str, Any]:
    current = get(t, client=client).json()
    return dict(
        operation_id=str(uuid4()),
        rate_percent=rate,
        fixed_amount_won=fixed,
        expected_trainer_version=current["trainer_version"],
        expected_compensation_version=current["compensation_version"],
    )


def change(t: TrainerScene, command: dict[str, Any], client: Any = None) -> Any:
    c = client or t.base.client
    return PrivateResponse(
        c.post(
            "/api/v1/admin/trainers/" + t.trainer + "/compensation",
            headers={**role_headers(c), "Origin": ORIGIN, "X-CSRF-Token": csrf(c)},
            json=command,
        )
    )


def receipt(t: TrainerScene, command: dict[str, Any], client: Any = None) -> Any:
    c = client or t.base.client
    return c.get(
        "/api/v1/admin/trainer-compensation-operations/" + command["operation_id"],
        headers=role_headers(c),
    )


def preserved(t: TrainerScene) -> dict[str, Any]:
    from tests.test_account_lifecycle import lifecycle_fingerprints

    return {
        k: v
        for k, v in lifecycle_fingerprints(t.base.db).items()
        if k
        not in {
            "workforce_trainers",
            "workforce_compensation_operations",
            "audit_compensation_events",
            "iam_sessions",
        }
    }


def test_initial_read_original_history_and_no_general_leak(trainer: TrainerScene) -> None:
    t = trainer
    before = activity(t.base.db)
    current = get(t)
    assert current.status_code == 200
    data = current.json()
    assert data["rate_percent"] == 0 and data["fixed_amount_won"] == "0"
    assert data["compensation_version"] == 1 and data["trainer_version"] == 1
    assert data["initial_base_salary_won"] == "9" * 1024
    assert data["initial_base_salary_start_month"] == "9999-12"
    history = get(t, "compensation-history").json()
    assert history["total"] == 1
    initial = history["items"][0]
    assert initial["before_rate"] is None and initial["before_fixed"] is None
    assert initial["after_rate"] == 0 and initial["after_fixed"] == "0"
    assert initial["initial_base_salary_won"] == data["initial_base_salary_won"]
    with t.base.db.session() as s:
        original = s.execute(
            text(
                "SELECT created_at FROM audit_workforce_initial_events "
                "WHERE event_kind='initial_compensation'"
            )
        ).scalar_one()
        from datetime import datetime

        assert datetime.fromisoformat(initial["recorded_at"]) == original
    for suffix in ["", "/login-account", "/role"]:
        raw = t.base.client.get("/api/v1/admin/trainers/" + t.trainer + suffix)
        assert raw.status_code == 200
        assert "rate_percent" not in raw.text and "base_salary" not in raw.text
    assert activity(t.base.db) == before


def test_exact_change_two_versions_noop_and_current_replay(trainer: TrainerScene) -> None:
    t = trainer
    original = preserved(t)
    command = body(t, 100, "9" * 1024)
    first = change(t, command)
    assert first.status_code == 200
    assert first.json()["changed"] and first.json()["committed_compensation_version"] == 2
    assert get(t).json()["trainer_version"] == 1
    assert get(t).json()["fixed_amount_won"] == "9" * 1024
    assert preserved(t) == original
    assert change(t, {**command, "operation_id": str(uuid4())}).status_code == 409
    assert change(t, {**command, "rate_percent": 0}).status_code == 409
    assert state_change(t, state_request(t, False)).status_code == 200
    stale = body(t, 0, "0")
    assert move(t, home_body(t, destination(t))).status_code == 200
    assert change(t, stale).status_code == 409
    assert get(t).json()["compensation_version"] == 2
    second = change(t, body(t, 0, "0"))
    assert second.status_code == 200
    noop = body(t, 0, "0")
    before = activity(t.base.db)
    assert change(t, noop).json()["changed"] is False
    replay = change(t, command)
    assert replay.status_code == 200
    assert replay.json()["committed_compensation_version"] == 2
    assert replay.json()["current_state"]["compensation_version"] == 3
    assert replay.json()["current_state"]["rate_percent"] == 0
    assert receipt(t, command).json() == replay.json()
    assert activity(t.base.db) == before
    history = get(t, "compensation-history?offset=0&limit=2").json()
    assert history["total"] == 3
    assert [x["compensation_version"] for x in history["items"]] == [1, 2]
    page = get(t, "compensation-history?offset=2&limit=2").json()
    assert [x["compensation_version"] for x in page["items"]] == [3]
    assert all(x["initial_base_salary_won"] is None for x in page["items"])


def test_strict_values_transport_and_noop_activity(trainer: TrainerScene) -> None:
    t = trainer
    command = body(t, 0, "0")
    before = activity(t.base.db)
    bad: list[dict[str, Any]] = [
        {"rate_percent": True},
        {"rate_percent": -1},
        {"rate_percent": 101},
        {"rate_percent": 1.5},
        {"fixed_amount_won": None},
        {"fixed_amount_won": "1.1"},
        {"fixed_amount_won": "-1"},
        {"fixed_amount_won": "01"},
        {"base_salary_won": "1"},
    ]
    for mutation in bad:
        r = change(t, {**command, **mutation})
        assert r.status_code == 422
        assert r.json() == {"detail": "invalid_request"}
    path = "/api/v1/admin/trainers/" + t.trainer + "/compensation"
    assert t.base.client.get(path).status_code == 422
    assert t.base.client.get(path, headers={"X-Y3-Expected-Actor": str(uuid4())}).status_code == 409
    assert (
        t.base.client.post(
            path,
            headers={
                **role_headers(t.base.client),
                "Origin": ORIGIN,
                "X-CSRF-Token": "synthetic-wrong",
            },
            json=command,
        ).status_code
        == 403
    )
    assert change(t, command).json()["changed"] is False
    assert change(t, command).json()["changed"] is False
    assert activity(t.base.db) == before
    assert get(t, "compensation-history").json()["total"] == 1
    foreign_org, foreign_branch, foreign_trainer = uuid4(), uuid4(), uuid4()
    with t.base.db.session() as session:
        session.execute(
            text("INSERT INTO organization_organizations(id,name) VALUES(:o,'가상 외부')"),
            {"o": foreign_org},
        )
        session.execute(
            text("""INSERT INTO organization_branches(id,organization_id,code,name)
            VALUES(:b,:o,'FOREIGNCOMP','가상 외부')"""),
            {"b": foreign_branch, "o": foreign_org},
        )
        session.execute(
            text("""INSERT INTO workforce_trainers(id,organization_id,home_branch_id,
            name,phone,active,row_version,rate_percent,fixed_amount_won,base_salary_won,
            base_salary_start_month) VALUES(:i,:o,:b,'가상','가상',true,1,0,0,0,'2026-01-01')"""),
            {"i": foreign_trainer, "o": foreign_org, "b": foreign_branch},
        )
        session.commit()
    for suffix in ("compensation", "compensation-history"):
        assert (
            t.base.client.get(
                "/api/v1/admin/trainers/" + str(foreign_trainer) + "/" + suffix,
                headers=role_headers(t.base.client),
            ).status_code
            == 404
        )
    assert (
        t.base.client.post(
            "/api/v1/admin/trainers/" + str(foreign_trainer) + "/compensation",
            headers={
                **role_headers(t.base.client),
                "Origin": ORIGIN,
                "X-CSRF-Token": csrf(t.base.client),
            },
            json=command,
        ).status_code
        == 404
    )


def test_current_home_authority_and_original_actor_receipt(
    trainer: TrainerScene, password_app: Any
) -> None:
    from fastapi.testclient import TestClient

    from tests.password_helpers import activate

    t = trainer
    dest = destination(t)
    with closing(branch_actor(t.base, password_app[2])) as old:
        command = body(t, 25, "0", old)
        assert change(t, command, old).status_code == 200
        assert move(t, home_body(t, dest)).status_code == 200
        for suffix in ["compensation", "compensation-history"]:
            assert get(t, suffix, old).status_code == 404
        assert receipt(t, command, old).status_code == 404
        assert change(t, command, old).status_code == 404
    issued = call(
        t.base.client,
        "/admin/accounts",
        csrf(t.base.client),
        {"login_id": "new.comp.admin", "branch_id": dest},
    )
    with closing(TestClient(t.base.client.app, base_url=ORIGIN)) as new:
        activate(new, issued.json()["setup_link"].split("#token=")[1], password_app[2])
        login_password(new, password_app[2], "new.comp.admin")
        assert get(t, client=new).status_code == 200
        history = get(t, "compensation-history", new).json()
        assert history["items"][1]["target_home"] == t.base.branch
        assert receipt(t, command, new).status_code == 404
        assert change(t, body(t, 30, "0", new), new).status_code == 200


@pytest.mark.parametrize("kind", ["master", "branch"])
def test_independent_admin_self_scope_and_trainer_denial(
    trainer: TrainerScene, password_app: Any, kind: str
) -> None:
    from tests.test_iam_trainer_roles import change as grant
    from tests.test_iam_trainer_roles_security import link

    t = trainer
    if kind == "branch":
        client = branch_actor(t.base, password_app[2])
        identifier = "workforce.branch"
    else:
        client = t.base.client
        identifier = "master.test"
    try:
        ident = client.get("/api/v1/auth/me").json()["account_id"]
        assert grant(t, link(t, ident, identifier)).status_code == 200
        login_password(client, password_app[2], identifier)
        assert state_change(t, state_request(t, False)).status_code == 200
        before = preserved(t)
        assert change(t, body(t, 1, "1", client), client).status_code == 200
        assert preserved(t) == before
        assert client.get("/api/v1/auth/me").status_code == 200
    finally:
        if kind == "branch":
            client.close()


def test_pending_source_unaffected_and_trainer_only_denied(trainer: TrainerScene) -> None:
    t = trainer
    token = source(t.issue())
    before = preserved(t)
    assert change(t, body(t)).status_code == 200
    assert preserved(t) == before
    assert t.complete(token).status_code == 204 and t.signin().status_code == 204
    for suffix in ["compensation", "compensation-history"]:
        assert get(t, suffix, t.recipient).status_code == 401
    assert change(t, body(t), t.recipient).status_code == 401
    from tests.test_operator_management import candidate, command

    assert command(t, candidate(t, t.login).json()).status_code == 200
    assert t.signin().status_code == 204
    assert get(t, client=t.recipient).status_code == 403
    before = preserved(t)
    assert change(t, body(t, 60, "2")).status_code == 200
    assert preserved(t) == before
    assert t.recipient.get("/api/v1/auth/me").status_code == 200


def test_required_audit_rolls_back_all_compensation(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch
) -> None:
    t = trainer
    command = body(t)
    before = activity(t.base.db)

    def fail(*args: Any) -> None:
        raise Rejected(503, "unavailable")

    monkeypatch.setattr(Audit, "append_compensation", fail)
    assert change(t, command).status_code == 503
    assert get(t).json()["compensation_version"] == 1
    assert get(t, "compensation-history").json()["total"] == 1
    assert receipt(t, command).status_code == 404
    assert activity(t.base.db) == before


@pytest.mark.parametrize("absolute", [False, True])
def test_compensation_final_actor_original_deadline(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch, absolute: bool
) -> None:
    from y3management.iam.public import Authentication
    from y3management.iam.roles import TrainerRoles

    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    assert t.signin().status_code == 204
    payload = body(t)
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
        "/api/v1/admin/trainers/" + t.trainer + "/compensation",
        headers={**role_headers(t.base.client), "Origin": ORIGIN, "X-CSRF-Token": nonce},
        json=payload,
    )
    assert response.status_code == 401
    assert observations[0] == (True, True)
    assert observations[1][1 if absolute else 0] is False
    with t.base.db.session() as s:
        assert s.execute(text("SELECT active FROM workforce_trainers")).scalar_one()
        assert (
            s.execute(text("SELECT count(*) FROM workforce_compensation_operations")).scalar_one()
            == 0
        )
        assert s.execute(text("SELECT count(*) FROM audit_trainer_state_events")).scalar_one() == 0
        assert s.execute(session_query, {"t": t.trainer}).all() == target_sessions

    assert t.recipient.get("/api/v1/auth/me").status_code == 200


def test_committed_ack_reconciles_without_overwriting_current(
    trainer: TrainerScene, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sqlalchemy.exc import OperationalError
    from sqlalchemy.orm import Session

    t = trainer
    command = body(t)
    commit = Session.commit
    fired = False

    def uncertain(self: Session) -> None:
        nonlocal fired
        fail = (
            not fired
            and self.execute(
                text(
                    "SELECT EXISTS(SELECT FROM workforce_compensation_operations "
                    "WHERE operation_id=:i)"
                ),
                {"i": command["operation_id"]},
            ).scalar_one()
        )
        commit(self)
        if fail:
            fired = True
            raise OperationalError("synthetic committed ACK loss", {}, RuntimeError())

    with monkeypatch.context() as patch:
        patch.setattr(Session, "commit", uncertain)
        assert change(t, command).status_code == 503
    assert fired and receipt(t, command).json()["committed_compensation_version"] == 2
    assert change(t, body(t, 60, "2")).status_code == 200
    before = activity(t.base.db)
    replay = change(t, command)
    assert replay.status_code == 200
    assert replay.json()["committed_rate_percent"] == 50
    assert replay.json()["current_state"]["rate_percent"] == 60
    assert activity(t.base.db) == before


def test_actual_global_gate_serializes_current_cas(
    trainer: TrainerScene, password_app: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from sqlalchemy import event as sa_event

    from tests.test_workforce_integrity import observe_waiter, wait_for_owned_block

    t = trainer
    command = body(t)
    reached, release = Event(), Event()
    holders = []
    original = Audit.append_compensation

    def paused(self: Audit, *args: Any) -> None:
        original(self, *args)
        holders.append(self.s.execute(text("SELECT pg_backend_pid()")).scalar_one())
        reached.set()
        assert release.wait(15)

    with closing(branch_actor(t.base, password_app[2])) as ba:
        headers_a = {
            **role_headers(t.base.client),
            "Origin": ORIGIN,
            "X-CSRF-Token": csrf(t.base.client),
        }
        headers_b = {**role_headers(ba), "Origin": ORIGIN, "X-CSRF-Token": csrf(ba)}
        monkeypatch.setattr(Audit, "append_compensation", paused)
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(
                t.base.client.post,
                "/api/v1/admin/trainers/" + t.trainer + "/compensation",
                headers=headers_a,
                json=command,
            )
            capture = None
            try:
                assert reached.wait(5)
                waiters: list[int] = []
                capture = observe_waiter(t.base.db, waiters)
                second = pool.submit(
                    ba.post,
                    "/api/v1/admin/trainers/" + t.trainer + "/compensation",
                    headers=headers_b,
                    json={**command, "operation_id": str(uuid4())},
                )
                wait_for_owned_block(t.base.db, holders[0], waiters)
            finally:
                release.set()
                if capture is not None:
                    sa_event.remove(t.base.db.engine, "before_cursor_execute", capture)
            assert first.result(timeout=10).status_code == 200
            assert second.result(timeout=10).status_code == 409
    assert get(t).json()["compensation_version"] == 2
    assert get(t, "compensation-history").json()["total"] == 2
