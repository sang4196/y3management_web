"""Allow atomic audit of authenticated self-service password changes."""

from alembic import op

revision = "0003_iam_password"
down_revision = "0002_iam_restore"
branch_labels = None
depends_on = None

_ACTIONS = (
    "'bootstrap','branch_create','account_issue','setup_reissue','setup_complete',"
    "'account_disable','scope_change','login','logout','account_restore'"
)


def upgrade() -> None:
    op.execute("ALTER TABLE audit_events DROP CONSTRAINT audit_events_action_check")
    op.execute(
        "ALTER TABLE audit_events ADD CONSTRAINT audit_events_action_check "
        f"CHECK(action IN ({_ACTIONS},'password_change'))"
    )


def downgrade() -> None:
    # Preserve password-change audit: incompatible history rejects the entire downgrade.
    op.execute("ALTER TABLE audit_events DROP CONSTRAINT audit_events_action_check")
    op.execute(
        "ALTER TABLE audit_events ADD CONSTRAINT audit_events_action_check "
        f"CHECK(action IN ({_ACTIONS}))"
    )
