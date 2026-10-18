# ruff: noqa: F811
"""Forward backfill and independently isolated destructive-downgrade guards."""

import hashlib
import json
import subprocess
import sys
from uuid import uuid4

import pytest
from sqlalchemy import text

from tests.test_iam import child_env
from tests.test_iam_mfa import mfa, protect  # noqa: F401
from y3management.config import Settings
from y3management.database import Database
from y3management.uow import UnitOfWork

pytestmark = pytest.mark.postgres


def fingerprint(db: Database) -> str:
    with db.session() as s:
        data = protect(
            {
                t: sorted(s.execute(text(f"SELECT row_to_json(t)::text FROM {t} t")).scalars())
                for t in (
                    "iam_accounts",
                    "iam_passkeys",
                    "iam_recovery_credentials",
                    "iam_mfa_contexts",
                    "iam_security_states",
                    "audit_events",
                    "alembic_version",
                )
            }
        )
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def migrate(settings: Settings, direction: str, revision: str) -> int:
    result = subprocess.run(
        [sys.executable, "-m", "alembic", direction, revision],
        env=child_env(settings),
        capture_output=True,
        timeout=30,
    )
    return result.returncode


@pytest.mark.parametrize("mfa", [False], indirect=True)
def test_management_empty_roundtrip(mfa: tuple[Settings, Database, str, str]) -> None:
    settings, db, _, _ = mfa
    before = fingerprint(db)
    assert migrate(settings, "downgrade", "0005_iam_mfa") == 0
    assert migrate(settings, "upgrade", "head") == 0
    assert fingerprint(db) == before


@pytest.mark.parametrize(
    "seed",
    [
        "revoked",
        "pending",
        "generation",
        "source",
        "context",
        "parent",
        "delete_audit",
        "start_audit",
        "reissue_audit",
        "complete_audit",
        "metadata",
    ],
)
def test_each_management_downgrade_guard(
    mfa: tuple[Settings, Database, str, str], seed: str
) -> None:
    settings, db, _, _ = mfa
    with db.session() as s:
        account = s.execute(text("SELECT id,organization_id FROM iam_accounts")).one()
        s.execute(text("DELETE FROM iam_security_states WHERE kind='mfa'"))
        if seed == "revoked":
            s.execute(
                text(
                    "INSERT INTO "
                    "iam_passkeys(credential_id,account_id,public_key,sign_count,"
                    "device_type,backed_up,revoked_at) "
                    "VALUES(:k,:a,:k,0,'single_device',false,clock_timestamp())"
                ),
                {"a": account.id, "k": b"synthetic"},
            )
        if seed in ("pending", "generation"):
            s.execute(
                text(
                    "UPDATE iam_accounts SET "
                    + ("recovery_pending=true" if seed == "pending" else "recovery_generation=1")
                )
            )
        if seed == "metadata":
            s.execute(
                text("UPDATE audit_events SET before_key_set_version=0 WHERE action='bootstrap'")
            )
        if seed.endswith("_audit"):
            action = {
                "delete_audit": "passkey_delete",
                "start_audit": "recovery_start",
                "reissue_audit": "recovery_reissue",
                "complete_audit": "recovery_complete",
            }[seed]
            s.execute(
                text(
                    "INSERT INTO audit_events(id,organization_id,action,success,request_id) "
                    "VALUES(:id,:o,:a,true,:id)"
                ),
                {"id": uuid4(), "o": account.organization_id, "a": action},
            )
        s.commit()
    if seed in ("source", "context", "parent"):
        with UnitOfWork(db, settings).open() as w:
            slot = w.security.allocate("recovery")
        if seed != "parent":
            with db.session() as s:
                s.execute(
                    text(
                        "INSERT INTO "
                        "iam_recovery_credentials(id,account_id,digest,row_version,"
                        "generation,expires_at) "
                        "SELECT :id,:a,:d,1,1,expires_at FROM iam_security_states WHERE "
                        "id=:id"
                    ),
                    {"id": slot, "a": account.id, "d": bytes(32)},
                )
                s.commit()
            if seed == "context":
                with UnitOfWork(db, settings).open() as w:
                    context = w.security.allocate("mfa")
                with db.session() as s:
                    s.execute(
                        text(
                            "INSERT INTO "
                            "iam_mfa_contexts(id,digest,csrf,account_id,purpose,security_version,"
                            "row_version,expires_at,recovery_id) "
                            "SELECT :id,:d,'synthetic',:a,'recovery',1,1,expires_at,:source FROM "
                            "iam_security_states WHERE id=:id"
                        ),
                        {"id": context, "d": bytes(32), "a": account.id, "source": slot},
                    )
                    s.commit()
    before = fingerprint(db)
    assert migrate(settings, "downgrade", "0005_iam_mfa") != 0
    assert fingerprint(db) == before


def test_upgrade_backfills_keys_without_changing_facts(
    mfa: tuple[Settings, Database, str, str],
) -> None:
    settings, db, _, _ = mfa
    assert migrate(settings, "downgrade", "0005_iam_mfa") == 0
    with db.session() as s:
        ident = s.execute(text("SELECT id FROM iam_accounts")).scalar_one()
        for key in (b"synthetic-one", b"synthetic-two"):
            s.execute(
                text(
                    "INSERT INTO iam_passkeys(credential_id,account_id,public_key,"
                    "sign_count,device_type,backed_up) VALUES(:k,:a,:k,0,'multi_device',true)"
                ),
                {"k": key, "a": ident},
            )
        before = s.execute(
            text(
                "SELECT md5(string_agg(to_jsonb(k)::text,',' ORDER BY credential_id)) "
                "FROM iam_passkeys k"
            )
        ).scalar_one()
        s.commit()
    assert migrate(settings, "upgrade", "head") == 0
    with db.session() as s:
        after = s.execute(
            text(
                "SELECT md5(string_agg((to_jsonb(k)-'key_id'-'revoked_at')::text,',' "
                "ORDER BY credential_id)) FROM iam_passkeys k"
            )
        ).scalar_one()
        assert before == after, "Backfill changed preexisting key facts"
        assert (
            s.execute(
                text("SELECT key_set_version FROM iam_accounts WHERE id=:a"), {"a": ident}
            ).scalar_one()
            == 2
        )
        assert (
            s.execute(
                text(
                    "SELECT count(*) FROM iam_passkeys WHERE account_id=:a "
                    "AND sign_count=0 AND device_type='multi_device' AND backed_up "
                    "AND revoked_at IS NULL AND credential_id=public_key"
                ),
                {"a": ident},
            ).scalar_one()
            == 2
        )
        assert s.execute(text("SELECT count(DISTINCT key_id) FROM iam_passkeys")).scalar_one() == 2
