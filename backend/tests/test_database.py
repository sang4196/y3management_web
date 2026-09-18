from threading import Event
from time import monotonic
from unittest.mock import Mock

import pytest
from sqlalchemy import text
from sqlalchemy.exc import InvalidRequestError

from y3management.config import Settings
from y3management.database import Database


@pytest.mark.parametrize("fails", [False, True])
def test_sessions_are_independent_and_permanently_closed(settings: Settings, fails: bool) -> None:
    database = Database(settings)
    try:
        with database.session() as first:
            first.begin()  # Logical transaction only, no connection or table.
        assert not first.in_transaction()
        try:
            with database.session() as second:
                assert first is not second
                second.begin()
                if fails:
                    raise ValueError("synthetic failure")
        except ValueError:
            assert fails
        assert not second.in_transaction()
        for closed in (first, second):
            with pytest.raises(InvalidRequestError, match="permanently closed"):
                closed.execute(text("SELECT 1"))
    finally:
        database.close()


@pytest.mark.parametrize("available", [False, True])
def test_probe_result(settings: Settings, monkeypatch: pytest.MonkeyPatch, available: bool) -> None:
    database = Database(settings)
    monkeypatch.setattr(database, "_probe", lambda: available)
    try:
        assert database.is_ready() is available
    finally:
        database.close()
    assert database.is_ready() is False


def test_probe_deadline_and_no_unbounded_queue(
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = settings.model_copy(update={"readiness_timeout_seconds": 0.05})
    database = Database(configuration)
    release = Event()
    finished = Event()
    calls = 0

    def slow_probe() -> bool:
        nonlocal calls
        calls += 1
        try:
            release.wait(timeout=2)
            return True
        finally:
            finished.set()

    monkeypatch.setattr(database, "_probe", slow_probe)
    try:
        start = monotonic()
        assert database.is_ready() is False
        assert database.is_ready() is False
        assert monotonic() - start < 1
        assert calls == 1
    finally:
        release.set()
        assert finished.wait(timeout=2)
        database.close()


def test_driver_failure_is_sanitized(
    settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    database = Database(settings)
    secret = "driver-password-sentinel"
    monkeypatch.setattr(
        database._probe_engine,
        "connect",
        Mock(side_effect=RuntimeError(secret)),
    )
    try:
        assert database.is_ready() is False
        assert secret not in caplog.text
    finally:
        database.close()
