# ruff: noqa: F811
"""Server mode separates retained S1 semantics from Trainer MFA-mode orchestration."""

from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.test_iam import ORIGIN, SyntheticSecret, csrf, iam  # noqa: F401
from tests.test_iam_mfa import call, mfa  # noqa: F401
from tests.test_iam_trainer import TrainerScene, source, trainer  # noqa: F401
from tests.test_workforce import scene  # noqa: F401
from y3management.application import create_app
from y3management.config import Settings
from y3management.contracts import Rejected
from y3management.database import Database
from y3management.iam.passwords import Passwords
from y3management.iam.security import Security
from y3management.uow import UnitOfWork
from y3management.use_cases import Service

pytestmark = pytest.mark.postgres


def count_admission(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    calls = {"verify": 0, "reserve": 0}
    original_verify, original_reserve = Passwords.verify, Security.reserve

    def verify(self: Passwords, value: str, encoded: str | None) -> tuple[bool, str | None]:
        calls["verify"] += 1
        return original_verify(self, value, encoded)

    def reserve(self: Security, identifier: str) -> Any:
        calls["reserve"] += 1
        return original_reserve(self, identifier)

    monkeypatch.setattr(Passwords, "verify", verify)
    monkeypatch.setattr(Security, "reserve", reserve)
    return calls


@pytest.mark.parametrize("http", [True, False])
def test_s1_retained_path_has_one_admission(
    iam: tuple[Settings, Database, str],
    monkeypatch: pytest.MonkeyPatch,
    http: bool,
) -> None:
    settings, db, password = iam
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        service = Service(UnitOfWork(db, settings))
        nonce, preauth = service.csrf(None, None)
        if http:
            nonce = csrf(client)
        calls = count_admission(monkeypatch)
        if http:
            assert (
                call(
                    client, "/auth/login", nonce, {"login_id": "master.test", "password": password}
                ).status_code
                == 204
            )
            assert client.get("/api/v1/auth/me").status_code == 200
        else:
            token = SyntheticSecret(service.login("master.test", password, preauth, nonce, None))
            assert service.me(token).master
        assert calls == {"verify": 1, "reserve": 1}


def test_s1_cannot_bypass_trainer_current_fact_path(
    trainer: TrainerScene,
    mfa: tuple[Settings, Database, str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    legacy = Service(UnitOfWork(t.base.db, mfa[0].model_copy(update={"iam_mode": "s1_password"})))
    nonce, preauth = legacy.csrf(None, None)
    calls = count_admission(monkeypatch)
    with pytest.raises(Rejected) as rejected:
        legacy.login(t.login, t.password, preauth, nonce, None)
    assert rejected.value.status == 401 and calls == {"verify": 1, "reserve": 1}
    with t.base.db.session() as s:
        assert (
            s.execute(
                text(
                    "SELECT count(*) FROM iam_sessions s JOIN iam_trainer_bindings b "
                    "ON b.account_id=s.account_id"
                )
            ).scalar_one()
            == 0
        )


@pytest.mark.parametrize("mfa_wrapper", [True, False])
def test_direct_mfa_mode_wrappers_do_not_reenter_or_create_unreturned_session(
    trainer: TrainerScene,
    mfa: tuple[Settings, Database, str, str],
    monkeypatch: pytest.MonkeyPatch,
    mfa_wrapper: bool,
) -> None:
    t = trainer
    assert t.complete(source(t.issue())).status_code == 204
    service = Service(UnitOfWork(t.base.db, mfa[0]))
    nonce, preauth = service.csrf(None, None)
    calls = count_admission(monkeypatch)
    if mfa_wrapper:
        with pytest.raises(Rejected) as rejected:
            service.begin_mfa_login(t.login, t.password, preauth, nonce, None)
        assert rejected.value.status == 403
    else:
        token = SyntheticSecret(service.login(t.login, t.password, preauth, nonce, None))
        caller, fact = service.principal(token)
        assert not caller.master and fact is not None and str(fact.trainer_id) == t.trainer
    assert calls == {"verify": 1, "reserve": 1}
    with t.base.db.session() as s:
        assert s.execute(
            text(
                "SELECT count(*) FROM iam_sessions s JOIN iam_trainer_bindings b "
                "ON b.account_id=s.account_id WHERE NOT s.revoked"
            )
        ).scalar_one() == (0 if mfa_wrapper else 1)
