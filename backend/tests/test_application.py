import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from y3management.application import create_app
from y3management.config import Settings


class FakeDatabase:
    def __init__(self, available: bool) -> None:
        self.available = available
        self.calls = 0
        self.closed = False

    def is_ready(self) -> bool:
        self.calls += 1
        return self.available

    def close(self) -> None:
        self.closed = True


@pytest.mark.parametrize("available,status", [(True, 200), (False, 503)])
def test_health_and_lifetime(settings: Settings, available: bool, status: int) -> None:
    database = FakeDatabase(available)
    app = create_app(settings, database=database)
    assert isinstance(app, FastAPI)
    with TestClient(app) as client:
        assert client.get("/health/live").json() == {"status": "alive"}
        assert database.calls == 0
        response = client.get("/health/ready")
        assert response.status_code == status
        assert response.json() == {"status": "ready" if available else "not_ready"}
        assert database.calls == 1
    assert database.closed


def test_errors_are_sanitized(
    settings: Settings,
    caplog: pytest.LogCaptureFixture,
) -> None:
    app = create_app(settings, database=FakeDatabase(True))
    secret = "credential-sentinel"

    @app.get("/test-failure")
    def fail() -> None:
        raise RuntimeError(f"postgresql://user:{secret}@private-db/db")

    @app.get("/test-validation")
    def validate(number: int) -> dict[str, int]:
        return {"number": number}

    with TestClient(app) as client:
        response = client.get("/test-failure", headers={"Authorization": secret})
        assert response.status_code == 500
        assert response.json() == {"detail": "Internal server error"}
        invalid = client.get("/test-validation", params={"number": secret})
        assert invalid.status_code == 422
        assert invalid.json() == {"detail": "Invalid request"}
    application_logs = [r.getMessage() for r in caplog.records if r.name == "y3management"]
    assert "request_failed" in application_logs
    assert all(secret not in message for message in application_logs)
    assert "private-db" not in response.text
