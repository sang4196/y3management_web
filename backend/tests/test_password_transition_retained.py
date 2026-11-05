# ruff: noqa: F811
"""Original sessions, staged secrets and C2 facts at an owned-schema cutover."""

import hashlib
import hmac
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from tests.legacy_helpers import legacy_allocation, legacy_database, legacy_master  # noqa: F401
from tests.password_helpers import call
from tests.test_iam import ORIGIN, SyntheticSecret, csrf
from tests.test_password_transition import migrate
from y3management.application import create_app
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres


def test_cutover_retires_authority_preserves_c2_and_never_promotes_staged_hash(
    legacy_master: tuple[Settings, Database],
) -> None:
    settings, db = legacy_master
    raw = SyntheticSecret("synthetic-old-session-token-" + uuid4().hex)
    setup_raw = SyntheticSecret("synthetic-old-setup-token-" + uuid4().hex)
    session_ids = [legacy_allocation(db, "session_slot") for _ in range(2)]
    source = legacy_allocation(db, "credential")
    context = legacy_allocation(db, "mfa")
    budget = legacy_allocation(db, "budget")
    attempt = legacy_allocation(db, "attempt")
    budget_key = hmac.digest(
        settings.iam_key.get_secret_value().encode(), b"legacy.master", "sha256"
    )
    with db.session() as session:
        account = session.execute(
            text("SELECT id,organization_id,login_budget_key FROM iam_accounts")
        ).one()
        pending = uuid4()
        session.execute(
            text(
                "INSERT INTO iam_accounts(id,organization_id,login_id,state) VALUES(:i,:o,"
                "'pending.test','PENDING_SETUP')"
            ),
            {"i": pending, "o": account.organization_id},
        )
        session.execute(text("INSERT INTO iam_login_ids VALUES('pending.test',:i)"), {"i": pending})
        session.execute(
            text("INSERT INTO iam_admin_grants VALUES(:i,:o,'ORGANIZATION',NULL)"),
            {"i": pending, "o": account.organization_id},
        )
        for index, slot in enumerate(session_ids):
            session.execute(
                text(
                    "INSERT INTO iam_sessions(id,account_id,digest,csrf,security_version,"
                    "created_at,last_activity,expires_at,assurance) "
                    "SELECT :i,:a,:d,'synthetic',1,created_at,created_at,expires_at,:v FROM "
                    "iam_security_states WHERE id=:i"
                ),
                {
                    "i": slot,
                    "a": account.id,
                    "d": hashlib.sha256((raw + str(index)).encode()).digest(),
                    "v": "password" if index == 0 else "password_uv",
                },
            )
        session.execute(
            text(
                "INSERT INTO iam_credentials(id,account_id,digest,row_version,expires_at) "
                "SELECT :i,:a,:d,1,expires_at FROM iam_security_states WHERE id=:i"
            ),
            {"i": source, "a": pending, "d": hashlib.sha256(setup_raw.encode()).digest()},
        )
        session.execute(
            text(
                "INSERT INTO iam_mfa_contexts(id,digest,csrf,account_id,purpose,"
                "security_version,row_version,expires_at,source_id,password_hash) "
                "SELECT :i,:d,'synthetic',:a,'setup',1,1,expires_at,:s,'synthetic-staged-hash' "
                "FROM iam_security_states WHERE id=:i"
            ),
            {"i": context, "a": pending, "s": source, "d": uuid4().bytes * 2},
        )
        session.execute(
            text(
                "INSERT INTO iam_budgets(key,state_id,cooldown) VALUES(:k,:i,"
                "clock_timestamp()+interval '15 minutes')"
            ),
            {"i": budget, "k": budget_key},
        )
        session.execute(
            text(
                "INSERT INTO iam_attempts(id,key,outcome,lease_until,stage) VALUES(:i,:k,"
                "'pending',clock_timestamp()+interval '5 minutes','waiting')"
            ),
            {"i": attempt, "k": budget_key},
        )
        session.execute(
            text(
                "INSERT INTO audit_events(id,action,success,request_id) VALUES(:i,'login',false,:i)"
            ),
            {"i": uuid4()},
        )
        for revoked in (False, True):
            session.execute(
                text(
                    "INSERT INTO iam_passkeys(credential_id,account_id,public_key,sign_count,"
                    "device_type,backed_up,revoked_at) "
                    "VALUES(:k,:a,:k,7,'single_device',false,CASE WHEN :r THEN "
                    "clock_timestamp()-interval '1 day' ELSE NULL END)"
                ),
                {"k": uuid4().bytes, "a": account.id, "r": revoked},
            )
        session.commit()
        before = {
            table: list(
                session.execute(
                    text(f"SELECT row_to_json(t)::jsonb FROM {table} t ORDER BY 1::text")
                ).scalars()
            )
            for table in (
                "iam_attempts",
                "iam_budgets",
                "audit_events",
                "iam_passkeys",
                "iam_sessions",
            )
        }
    migrate(settings, "upgrade", "0014_password_only")
    with db.session() as session:
        for table in ("iam_attempts", "iam_budgets", "audit_events"):
            expression = (
                "to_jsonb(t)-'policy_version'" if table == "iam_attempts" else "to_jsonb(t)"
            )
            after = list(
                session.execute(
                    text(f"SELECT {expression} FROM {table} t ORDER BY 1::text")
                ).scalars()
            )
            assert after == before[table]
        keys = list(
            session.execute(
                text("SELECT to_jsonb(t) FROM iam_passkeys t ORDER BY 1::text")
            ).scalars()
        )
        original = {item["key_id"]: item for item in before["iam_passkeys"]}
        for key in keys:
            previous = original[key["key_id"]]
            assert key["revoked_at"] is not None
            if previous["revoked_at"] is not None:
                assert key["revoked_at"] == previous["revoked_at"]
            assert {k: v for k, v in key.items() if k != "revoked_at"} == {
                k: v for k, v in previous.items() if k != "revoked_at"
            }
        rows = list(
            session.execute(
                text("SELECT to_jsonb(t) FROM iam_sessions t ORDER BY 1::text")
            ).scalars()
        )
        original_sessions = {item["id"]: item for item in before["iam_sessions"]}
        for row in rows:
            assert row["revoked"] and row["policy_version"] == 1 and row["login_attempt_id"] is None
            assert {
                k: v
                for k, v in row.items()
                if k not in ("revoked", "policy_version", "login_attempt_id")
            } == {k: v for k, v in original_sessions[row["id"]].items() if k != "revoked"}
        assert tuple(
            session.execute(
                text("SELECT consumed,password_hash FROM iam_mfa_contexts WHERE id=:i"),
                {"i": context},
            ).one()
        ) == (True, None)
        assert tuple(
            session.execute(
                text("SELECT state,password_hash FROM iam_accounts WHERE id=:i"), {"i": pending}
            ).one()
        ) == ("PENDING_SETUP", None)

    def retained_rows(*, at_cutover: bool) -> dict[str, str]:
        # Compare whole rows, including all original columns, without exposing their contents.
        with db.session() as reader:
            tables = (
                reader.execute(
                    text(
                        "SELECT tablename FROM pg_tables WHERE schemaname=current_schema() "
                        "AND tablename <> 'alembic_version' ORDER BY tablename"
                    )
                )
                .scalars()
                .all()
            )
            digests = {}
            for table in tables:
                row = "to_jsonb(t)"
                if at_cutover and table == "iam_sessions":
                    row += " || jsonb_build_object('operator_version', 0)"
                if at_cutover and table == "iam_accounts":
                    row += """ || jsonb_build_object('restore_state',
                        CASE WHEN state='DISABLED' THEN 'ACTIVE' END)"""
                quoted = db.engine.dialect.identifier_preparer.quote(table)
                digests[table] = reader.execute(
                    text(
                        f"SELECT md5(COALESCE(jsonb_agg(r ORDER BY r)::text,'[]')) "
                        f"FROM (SELECT {row} AS r FROM {quoted} t) retained"
                    )
                ).scalar_one()
            return digests

    expected = retained_rows(at_cutover=True)
    with db.session() as session:
        assert session.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == (
            "0014_password_only"
        )
        assert set(session.execute(text("SELECT id FROM iam_sessions")).scalars()) == set(
            session_ids
        )
    migrate(settings, "upgrade", "head")
    new_tables = {
        "iam_operator_grants",
        "iam_operator_setup_credentials",
        "audit_operator_account_events",
    }
    with db.session() as session:
        assert session.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == (
            "0016_operator_onboarding"
        )
        versions = session.execute(text("SELECT id, operator_version FROM iam_sessions")).all()
        assert {ident: version for ident, version in versions} == {
            ident: 0 for ident in session_ids
        }
        for table in new_tables:
            assert session.execute(text(f"SELECT count(*) FROM {table}")).scalar_one() == 0
    empty = hashlib.md5(b"[]", usedforsecurity=False).hexdigest()
    assert retained_rows(at_cutover=False) == {**expected, **dict.fromkeys(new_tables, empty)}
    with TestClient(create_app(settings, database=db), base_url=ORIGIN) as client:
        for index in range(2):
            client.cookies.set("__Host-y3-auth", raw + str(index))
            assert client.get("/api/v1/auth/me").status_code == 401
        client.cookies.clear()
        assert (
            call(
                client,
                "/auth/credentials/complete",
                csrf(client),
                {"setup_token": setup_raw, "new_password": "synthetic invalid"},
            ).status_code
            == 400
        )
