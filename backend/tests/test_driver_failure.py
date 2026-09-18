"""Real psycopg failure path; no PostgreSQL service or mock connector."""

import socket
from time import monotonic

from fastapi.testclient import TestClient

from y3management.application import create_app
from y3management.config import Settings


def test_unreachable_database_health() -> None:
    # Reserve without listening: no other service can receive the connection.
    with socket.socket() as reserved:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            reserved.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        reserved.bind(("127.0.0.1", 0))
        port = reserved.getsockname()[1]
        secret = "failure-test-sentinel"
        dsn = f"postgresql+psycopg://y3management_test:{secret}@127.0.0.1:{port}/y3management_test"
        settings = Settings.model_validate(
            {
                "environment": "test",
                "database_url": dsn,
                "readiness_timeout_seconds": 0.5,
                "db_connect_timeout_seconds": 2,
            }
        )
        with TestClient(create_app(settings)) as client:
            assert client.get("/health/live").status_code == 200
            started = monotonic()
            response = client.get("/health/ready")
            assert monotonic() - started < 2
            assert response.status_code == 503
            assert response.json() == {"status": "not_ready"}
            assert all(value not in response.text for value in (secret, dsn, "Traceback"))
            assert client.get("/health/live").status_code == 200
