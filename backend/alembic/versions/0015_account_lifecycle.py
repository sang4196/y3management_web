"""Preserve the destination of a disabled account without reconstructing history."""

from sqlalchemy import text

from alembic import op

revision = "0015_account_lifecycle"
down_revision = "0014_password_only"
branch_labels = None
depends_on = None

_PENDING = "(password_hash IS NULL AND NOT password_reset_pending)"
_READY = """((password_reset_pending AND password_hash IS NULL AND reset_generation>0)
             OR (NOT password_reset_pending AND password_hash IS NOT NULL))"""
_OLD = f"""((state='PENDING_SETUP' AND {_PENDING})
        OR (state IN ('ACTIVE','DISABLED') AND {_READY}))"""
_NEW = f"""((state='PENDING_SETUP' AND restore_state IS NULL AND {_PENDING})
        OR (state='ACTIVE' AND restore_state IS NULL AND {_READY})
        OR (state='DISABLED' AND restore_state IS NOT NULL AND
            ((restore_state='PENDING_SETUP' AND {_PENDING})
             OR (restore_state='ACTIVE' AND {_READY}))))"""


def _preflight(expected: str, readiness: str) -> None:
    bind = op.get_bind()
    op.execute("""LOCK TABLE alembic_version, iam_installation, iam_policy_transitions,
               iam_accounts, audit_events IN ACCESS EXCLUSIVE MODE""")
    if list(bind.execute(text("SELECT version_num FROM alembic_version")).scalars()) != [expected]:
        raise ValueError("LIFECYCLE_SCHEMA_MISMATCH")
    constraint = "iam_accounts_check" if expected == down_revision else "iam_account_lifecycle"
    if not bind.execute(
        text("""SELECT EXISTS(SELECT 1 FROM pg_constraint
            WHERE conrelid='iam_accounts'::regclass AND conname=:name
            AND contype='c' AND convalidated)"""),
        {"name": constraint},
    ).scalar_one():
        raise ValueError("LIFECYCLE_SCHEMA_MISMATCH")
    destination = bind.execute(
        text("""SELECT data_type,is_nullable FROM information_schema.columns
            WHERE table_schema=current_schema() AND table_name='iam_accounts'
            AND column_name='restore_state'""")
    ).all()
    if destination != ([] if expected == down_revision else [("text", "YES")]):
        raise ValueError("LIFECYCLE_SCHEMA_MISMATCH")
    if not bind.execute(
        text("""SELECT EXISTS(SELECT 1 FROM iam_installation i
        JOIN iam_policy_transitions p ON i.policy_transition_id=p.id WHERE i.id=1
        AND i.auth_policy_version=2 AND p.from_version=1 AND p.to_version=2
        AND p.target_schema_revision='0014_password_only')""")
    ).scalar_one():
        raise ValueError("LIFECYCLE_POLICY_MISMATCH")
    if bind.execute(
        text(f"SELECT EXISTS(SELECT 1 FROM iam_accounts WHERE ({readiness}) IS NOT TRUE)")
    ).scalar_one():
        raise ValueError("LIFECYCLE_INVALID_READINESS")
    if bind.execute(
        text("""SELECT EXISTS(SELECT 1 FROM audit_events WHERE success AND
        ((action='account_disable' AND before_state='PENDING_SETUP' AND after_state='DISABLED')
         OR (action='account_restore' AND before_state='DISABLED'
            AND after_state='PENDING_SETUP')))""")
    ).scalar_one():
        raise ValueError("LIFECYCLE_PENDING_HISTORY")


def upgrade() -> None:
    _preflight(down_revision, _OLD)
    op.execute("ALTER TABLE iam_accounts ADD COLUMN restore_state text")
    op.execute("UPDATE iam_accounts SET restore_state='ACTIVE' WHERE state='DISABLED'")
    op.execute(f"""ALTER TABLE iam_accounts DROP CONSTRAINT iam_accounts_check,
               ADD CONSTRAINT iam_account_lifecycle CHECK ({_NEW})""")


def downgrade() -> None:
    _preflight(revision, _NEW)
    if (
        op.get_bind()
        .execute(
            text("""SELECT EXISTS(SELECT 1 FROM iam_accounts
            WHERE restore_state='PENDING_SETUP')""")
        )
        .scalar_one()
    ):
        raise ValueError("LIFECYCLE_PENDING_DESTINATION")
    op.execute(f"""ALTER TABLE iam_accounts DROP CONSTRAINT iam_account_lifecycle,
               DROP COLUMN restore_state, ADD CONSTRAINT iam_accounts_check CHECK ({_OLD})""")
