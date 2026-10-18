"""Purpose-separated administrator password reset; preserve keys and history."""

from alembic import op

revision = "0007_iam_password_reset"
down_revision = "0006_iam_mfa_management"
branch_labels = None
depends_on = None
_ACTIONS = (
    "'bootstrap','branch_create','account_issue','setup_reissue','setup_complete',"
    "'account_disable','scope_change','login','logout','account_restore',"
    "'password_change','login_id_change','passkey_register','passkey_delete',"
    "'recovery_start','recovery_reissue','recovery_complete'"
)


def upgrade() -> None:
    op.execute("LOCK TABLE iam_security_control IN ACCESS EXCLUSIVE MODE")
    op.execute("""
    ALTER TABLE iam_accounts
      ADD COLUMN password_reset_pending boolean NOT NULL DEFAULT false,
      ADD COLUMN reset_generation bigint NOT NULL DEFAULT 0 CHECK(reset_generation>=0);
    ALTER TABLE iam_accounts DROP CONSTRAINT iam_accounts_check;
    ALTER TABLE iam_accounts ADD CONSTRAINT iam_accounts_check CHECK (
      (state='PENDING_SETUP' AND password_hash IS NULL AND NOT password_reset_pending)
      OR (state IN ('ACTIVE','DISABLED') AND
        ((password_reset_pending AND password_hash IS NULL AND reset_generation>0)
         OR (NOT password_reset_pending AND password_hash IS NOT NULL))));
    ALTER TABLE iam_security_states DROP CONSTRAINT iam_security_states_kind_check;
    ALTER TABLE iam_security_states ADD CONSTRAINT iam_security_states_kind_check
      CHECK(kind IN ('budget','attempt','preparation','credential','session_slot','mfa',
        'recovery','password_reset'));
    CREATE TABLE iam_reset_credentials (
      id uuid PRIMARY KEY REFERENCES iam_security_states(id) ON DELETE CASCADE,
      account_id uuid NOT NULL REFERENCES iam_accounts(id),
      digest bytea NOT NULL UNIQUE CHECK(octet_length(digest)=32),
      row_version bigint NOT NULL CHECK(row_version>0),
      security_version bigint NOT NULL CHECK(security_version>0),
      generation bigint NOT NULL CHECK(generation>0),
      expires_at timestamptz NOT NULL, consumed boolean NOT NULL DEFAULT false);
    CREATE INDEX ON iam_reset_credentials(account_id);
    ALTER TABLE audit_events
      ADD COLUMN before_reset_generation bigint CHECK(before_reset_generation>=0),
      ADD COLUMN after_reset_generation bigint CHECK(after_reset_generation>=0),
      ADD COLUMN before_password_ready boolean,
      ADD COLUMN after_password_ready boolean;
    ALTER TABLE audit_events DROP CONSTRAINT audit_events_action_check;
    """)
    op.execute(
        "ALTER TABLE audit_events ADD CONSTRAINT audit_events_action_check "
        f"CHECK(action IN ({_ACTIONS},'password_reset_start','password_reset_reissue',"
        "'password_reset_complete'))"
    )


def downgrade() -> None:
    op.execute("LOCK TABLE iam_security_control IN ACCESS EXCLUSIVE MODE")
    op.execute(
        "LOCK TABLE iam_accounts,iam_sessions,iam_reset_credentials,audit_events,"
        "iam_security_states IN ACCESS EXCLUSIVE MODE"
    )
    op.execute("""DO $$ BEGIN IF
      EXISTS(SELECT 1 FROM iam_accounts WHERE password_reset_pending OR reset_generation>0)
      OR EXISTS(SELECT 1 FROM iam_reset_credentials)
      OR EXISTS(SELECT 1 FROM iam_security_states WHERE kind='password_reset')
      OR EXISTS(SELECT 1 FROM audit_events WHERE before_reset_generation IS NOT NULL
        OR after_reset_generation IS NOT NULL OR before_password_ready IS NOT NULL
        OR after_password_ready IS NOT NULL OR action IN
        ('password_reset_start','password_reset_reissue','password_reset_complete')) THEN
      RAISE EXCEPTION 'Password reset state or history prevents downgrade'; END IF; END $$""")
    op.execute("DROP TABLE iam_reset_credentials")
    op.execute("ALTER TABLE iam_security_states DROP CONSTRAINT iam_security_states_kind_check")
    op.execute(
        "ALTER TABLE iam_security_states ADD CONSTRAINT iam_security_states_kind_check "
        "CHECK(kind IN "
        "('budget','attempt','preparation','credential','session_slot','mfa','recovery'))"
    )
    op.execute("ALTER TABLE iam_accounts DROP CONSTRAINT iam_accounts_check")
    op.execute(
        "ALTER TABLE iam_accounts ADD CONSTRAINT iam_accounts_check "
        "CHECK((state='PENDING_SETUP' AND password_hash IS NULL) "
        "OR (state IN ('ACTIVE','DISABLED') AND password_hash IS NOT NULL))"
    )
    op.execute(
        "ALTER TABLE iam_accounts DROP COLUMN password_reset_pending,DROP COLUMN reset_generation"
    )
    op.execute(
        "ALTER TABLE audit_events DROP COLUMN before_reset_generation,"
        "DROP COLUMN after_reset_generation,DROP COLUMN before_password_ready,"
        "DROP COLUMN after_password_ready"
    )
    op.execute("ALTER TABLE audit_events DROP CONSTRAINT audit_events_action_check")
    op.execute(
        "ALTER TABLE audit_events ADD CONSTRAINT audit_events_action_check "
        f"CHECK(action IN ({_ACTIONS}))"
    )
