"""Allow atomic audit of normal Branch Admin account restoration."""

from alembic import op

revision = "0002_iam_restore"
down_revision = "0001_iam_s1"
branch_labels = None
depends_on = None

_ACTIONS = (
    "'bootstrap','branch_create','account_issue','setup_reissue','setup_complete',"
    "'account_disable','scope_change','login','logout'"
)


def upgrade() -> None:
    op.execute("ALTER TABLE audit_events DROP CONSTRAINT audit_events_action_check")
    op.execute(
        "ALTER TABLE audit_events ADD CONSTRAINT audit_events_action_check "
        f"CHECK(action IN ({_ACTIONS},'account_restore'))"
    )


def downgrade() -> None:
    # Existing restore audit makes this downgrade fail atomically. Never erase audit to downgrade.
    op.execute("ALTER TABLE audit_events DROP CONSTRAINT audit_events_action_check")
    op.execute(
        "ALTER TABLE audit_events ADD CONSTRAINT audit_events_action_check "
        f"CHECK(action IN ({_ACTIONS}))"
    )
