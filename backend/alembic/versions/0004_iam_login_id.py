"""Preserve account admission identity across Login ID changes."""

from alembic import op

revision = "0004_iam_login_id"
down_revision = "0003_iam_password"
branch_labels = None
depends_on = None

_ACTIONS = (
    "'bootstrap','branch_create','account_issue','setup_reissue','setup_complete',"
    "'account_disable','scope_change','login','logout','account_restore','password_change'"
)


def upgrade() -> None:
    op.execute(
        "ALTER TABLE iam_accounts ADD COLUMN login_budget_key bytea "
        "CONSTRAINT iam_login_budget_key_length CHECK(octet_length(login_budget_key)=32) "
        "CONSTRAINT iam_login_budget_key_unique UNIQUE"
    )
    op.execute("ALTER TABLE audit_events ADD COLUMN before_login_id varchar(64)")
    op.execute("ALTER TABLE audit_events ADD COLUMN after_login_id varchar(64)")
    op.execute("ALTER TABLE audit_events DROP CONSTRAINT audit_events_action_check")
    op.execute(
        "ALTER TABLE audit_events ADD CONSTRAINT audit_events_action_check "
        f"CHECK(action IN ({_ACTIONS},'login_id_change'))"
    )
    op.execute(
        "ALTER TABLE audit_events ADD CONSTRAINT audit_login_id_fields CHECK ("
        "(action='login_id_change' AND before_login_id IS NOT NULL AND after_login_id IS NOT NULL "
        "AND before_login_id ~ '^[a-z0-9][a-z0-9_.-]{2,63}$' "
        "AND after_login_id ~ '^[a-z0-9][a-z0-9_.-]{2,63}$' "
        "AND before_login_id<>after_login_id) OR "
        "(action<>'login_id_change' AND before_login_id IS NULL AND after_login_id IS NULL))"
    )


def downgrade() -> None:
    # Lock before checking: no concurrent writer may add state between the guard and DDL.
    op.execute("LOCK TABLE iam_accounts, audit_events IN ACCESS EXCLUSIVE MODE")
    op.execute(
        "DO $$ BEGIN IF EXISTS (SELECT 1 FROM iam_accounts WHERE login_budget_key IS NOT NULL) "
        "OR EXISTS (SELECT 1 FROM audit_events WHERE action='login_id_change') THEN "
        "RAISE EXCEPTION 'Login ID security state or history prevents downgrade'; "
        "END IF; END $$"
    )
    op.execute("ALTER TABLE audit_events DROP CONSTRAINT audit_login_id_fields")
    op.execute("ALTER TABLE audit_events DROP CONSTRAINT audit_events_action_check")
    op.execute(
        "ALTER TABLE audit_events ADD CONSTRAINT audit_events_action_check "
        f"CHECK(action IN ({_ACTIONS}))"
    )
    op.execute("ALTER TABLE audit_events DROP COLUMN after_login_id, DROP COLUMN before_login_id")
    op.execute("ALTER TABLE iam_accounts DROP COLUMN login_budget_key")
