"""Startup policy validation runs inside one synchronous worker and releases guards on failure."""

import threading

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.test_iam import ORIGIN
from y3management.application import create_app
from y3management.config import Settings
from y3management.database import Database
from y3management.iam.infrastructure import IAM
from y3management.iam.public import PolicyStamp
from y3management.runtime import ProcessGuard

pytestmark = pytest.mark.postgres


def test_startup_policy_uses_worker_and_failed_marker_releases_guard(
    password_app: tuple[Settings, Database, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings, db, _ = password_app
    init, policy = ProcessGuard.__init__, IAM.policy
    guard_threads: list[int] = []
    policy_threads: list[int] = []

    def guarded(self: ProcessGuard, configuration: Settings) -> None:
        guard_threads.append(threading.get_ident())
        init(self, configuration)

    def checked(self: IAM) -> PolicyStamp:
        policy_threads.append(threading.get_ident())
        return policy(self)

    with monkeypatch.context() as patch:
        patch.setattr(ProcessGuard, "__init__", guarded)
        patch.setattr(IAM, "policy", checked)
        with TestClient(create_app(settings, database=db), base_url=ORIGIN):
            assert policy_threads and guard_threads
            assert len(set(policy_threads)) == 1
            assert policy_threads[0] != guard_threads[0]
    with db.session() as session:
        session.execute(text("UPDATE iam_policy_transitions SET target_schema_revision='invalid'"))
        session.commit()
    with pytest.raises(ValueError, match="APPLICATION_STARTUP_FAILED"):
        with TestClient(create_app(settings, database=db), base_url=ORIGIN):
            pytest.fail("Invalid marker started the application")
    guard = ProcessGuard(settings)
    guard.close()


def test_initial_password_and_source_roll_back_on_audit_failure(
    password_app: tuple[Settings, Database, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    from contextlib import closing

    from tests.password_helpers import call, link_token, login_password
    from tests.test_iam import csrf
    from tests.test_password_transition import fingerprint
    from y3management.audit.infrastructure import Audit
    from y3management.audit.public import Event
    from y3management.contracts import Rejected

    settings, db, password = password_app
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as actor:
        login_password(actor, password)
        issued = call(actor, "/admin/master-accounts", csrf(actor), {"login_id": "pending.master"})
        assert issued.status_code == 201
        token = link_token(issued.json()["setup_link"])
        with closing(TestClient(actor.app, base_url=ORIGIN)) as recipient:
            nonce = csrf(recipient)
            before = fingerprint(db)
            append = Audit.append
            reached = False

            def fail(adapter: Audit, event: Event) -> None:
                nonlocal reached
                if event.action == "setup_complete":
                    reached = True
                    raise Rejected(503, "unavailable")
                append(adapter, event)

            with monkeypatch.context() as patch:
                patch.setattr(Audit, "append", fail)
                response = call(
                    recipient,
                    "/auth/credentials/complete",
                    nonce,
                    {"setup_token": token, "new_password": password},
                )
            assert reached and response.status_code == 503
            assert fingerprint(db) == before
            assert "__Host-y3-auth" not in recipient.cookies
            assert (
                call(
                    recipient,
                    "/auth/credentials/complete",
                    nonce,
                    {"setup_token": token, "new_password": password},
                ).status_code
                == 204
            )
            assert "__Host-y3-auth" not in recipient.cookies
            login_password(recipient, password, "pending.master")
