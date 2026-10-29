# ruff: noqa: F811
"""Actual auth validation responses must not echo synthetic sensitive input."""

import hashlib
from typing import Any

import pytest
from sqlalchemy import text

from tests.test_iam import ORIGIN, csrf
from tests.test_iam_mfa import mfa  # noqa: F401
from tests.test_workforce import Scene, scene  # noqa: F401

pytestmark = pytest.mark.postgres


def unchanged_database(scene: Scene) -> str:
    with scene.db.session() as session:
        values = [
            sorted(session.execute(text(f"SELECT row_to_json(t)::text FROM {table} t")).scalars())
            for table in (
                "iam_accounts",
                "iam_sessions",
                "iam_security_states",
                "iam_attempts",
                "iam_reset_credentials",
                "iam_mfa_contexts",
                "audit_events",
            )
        ]
    return hashlib.sha256(repr(values).encode()).hexdigest()


def test_auth_invalid_inputs_never_echo_or_mutate(scene: Scene) -> None:
    marker = "synthetic-private-marker-iam013"
    nonce = csrf(scene.client)
    cases: list[tuple[str, dict[str, Any]]] = [
        (
            "/auth/password-reset/complete",
            {"reset_token": {"secret": marker}, "new_password": marker},
        ),
        ("/auth/password-reset/complete", {"reset_token": marker * 10, "new_password": marker}),
        (
            "/auth/password-reset/complete",
            {"reset_token": "x" * 43, "new_password": marker, "extra": marker},
        ),
        ("/auth/login", {"login_id": "example", "password": {"secret": marker}}),
        ("/auth/password", {"current_password": {"secret": marker}, "new_password": marker}),
        (
            "/auth/trainer-credentials/complete",
            {"setup_token": {"secret": marker}, "new_password": marker},
        ),
        ("/auth/passkeys/enrollment/options", {"setup_token": {"secret": marker}}),
    ]
    before = unchanged_database(scene)
    observations = []
    for path, body in cases:
        response = scene.client.post(
            "/api/v1" + path, headers={"Origin": ORIGIN, "X-CSRF-Token": nonce}, json=body
        )
        observations.append((response.status_code, marker not in response.text))
        assert unchanged_database(scene) == before
    assert all(status == 422 and hidden for status, hidden in observations), observations
