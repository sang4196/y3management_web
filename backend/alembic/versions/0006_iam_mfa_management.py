"""Passkey revocation and purpose-separated bounded recovery authority."""

from alembic import op

revision = "0006_iam_mfa_management"
down_revision = "0005_iam_mfa"
branch_labels = None
depends_on = None
_ACTIONS = (
    "'bootstrap','branch_create','account_issue','setup_reissue','setup_complete',"
    "'account_disable','scope_change','login','logout','account_restore',"
    "'password_change','login_id_change','passkey_register'"
)


def upgrade() -> None:
    # Stop short security allocation/GC before taking business-table DDL locks.
    op.execute("LOCK TABLE iam_security_control IN ACCESS EXCLUSIVE MODE")
    op.execute("""
    ALTER TABLE iam_accounts
      ADD COLUMN key_set_version bigint NOT NULL DEFAULT 0 CHECK(key_set_version>=0),
      ADD COLUMN recovery_pending boolean NOT NULL DEFAULT false,
      ADD COLUMN recovery_generation bigint NOT NULL DEFAULT 0 CHECK(recovery_generation>=0);
    ALTER TABLE iam_passkeys
      ADD COLUMN key_id uuid NOT NULL DEFAULT gen_random_uuid() UNIQUE,
      ADD COLUMN revoked_at timestamptz;
    UPDATE iam_accounts a SET key_set_version=(SELECT count(*) FROM iam_passkeys k
      WHERE k.account_id=a.id);
    ALTER TABLE iam_security_states DROP CONSTRAINT iam_security_states_kind_check;
    ALTER TABLE iam_security_states ADD CONSTRAINT iam_security_states_kind_check
      CHECK(kind IN ('budget','attempt','preparation','credential',
        'session_slot','mfa','recovery'));
    CREATE TABLE iam_recovery_credentials (
      id uuid PRIMARY KEY REFERENCES iam_security_states(id) ON DELETE CASCADE,
      account_id uuid NOT NULL REFERENCES iam_accounts(id),
      digest bytea NOT NULL UNIQUE CHECK(octet_length(digest)=32),
      row_version bigint NOT NULL, generation bigint NOT NULL CHECK(generation>0),
      expires_at timestamptz NOT NULL, consumed boolean NOT NULL DEFAULT false);
    CREATE INDEX ON iam_recovery_credentials(account_id);
    ALTER TABLE iam_mfa_contexts ADD COLUMN recovery_id uuid
      REFERENCES iam_recovery_credentials(id) ON DELETE CASCADE;
    ALTER TABLE iam_mfa_contexts DROP CONSTRAINT iam_mfa_contexts_purpose_check;
    ALTER TABLE iam_mfa_contexts ADD CONSTRAINT iam_mfa_contexts_purpose_check
      CHECK(purpose IN ('install','setup','add','login','recovery'));
    ALTER TABLE iam_mfa_contexts ADD CONSTRAINT iam_mfa_contexts_recovery_check
      CHECK ((purpose='recovery' AND recovery_id IS NOT NULL AND source_id IS NULL)
        OR (purpose<>'recovery' AND recovery_id IS NULL));
    ALTER TABLE audit_events
      ADD COLUMN key_id uuid,
      ADD COLUMN before_key_set_version bigint CHECK(before_key_set_version>=0),
      ADD COLUMN after_key_set_version bigint CHECK(after_key_set_version>=0),
      ADD COLUMN before_recovery_generation bigint CHECK(before_recovery_generation>=0),
      ADD COLUMN after_recovery_generation bigint CHECK(after_recovery_generation>=0);
    ALTER TABLE audit_events DROP CONSTRAINT audit_events_action_check;
    """)
    op.execute(
        "ALTER TABLE audit_events ADD CONSTRAINT audit_events_action_check "
        f"CHECK(action IN ({_ACTIONS},'passkey_delete','recovery_start',"
        "'recovery_reissue','recovery_complete'))"
    )


def downgrade() -> None:
    op.execute("LOCK TABLE iam_security_control IN ACCESS EXCLUSIVE MODE")
    op.execute(
        "LOCK TABLE iam_accounts,iam_sessions,iam_passkeys,iam_mfa_contexts,"
        "iam_recovery_credentials,audit_events,iam_security_states,"
        "iam_security_control IN ACCESS EXCLUSIVE MODE"
    )
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM iam_passkeys WHERE revoked_at IS NOT NULL)
      OR EXISTS(SELECT 1 FROM iam_accounts WHERE recovery_pending OR recovery_generation>0)
      OR EXISTS(SELECT 1 FROM iam_recovery_credentials)
      OR EXISTS(SELECT 1 FROM iam_mfa_contexts WHERE purpose='recovery')
      OR EXISTS(SELECT 1 FROM iam_security_states WHERE kind='recovery')
      OR EXISTS(SELECT 1 FROM audit_events WHERE key_id IS NOT NULL
        OR before_key_set_version IS NOT NULL OR after_key_set_version IS NOT NULL
        OR before_recovery_generation IS NOT NULL OR after_recovery_generation IS NOT NULL)
      OR EXISTS(SELECT 1 FROM audit_events WHERE action IN
        ('passkey_delete','recovery_start','recovery_reissue','recovery_complete')) THEN
      RAISE EXCEPTION 'MFA management state or history prevents downgrade'; END IF; END $$""")
    op.execute("ALTER TABLE iam_mfa_contexts DROP CONSTRAINT iam_mfa_contexts_recovery_check")
    op.execute("ALTER TABLE iam_mfa_contexts DROP COLUMN recovery_id")
    op.execute("ALTER TABLE iam_mfa_contexts DROP CONSTRAINT iam_mfa_contexts_purpose_check")
    op.execute(
        "ALTER TABLE iam_mfa_contexts ADD CONSTRAINT iam_mfa_contexts_purpose_check "
        "CHECK(purpose IN ('install','setup','add','login'))"
    )
    op.execute("DROP TABLE iam_recovery_credentials")
    op.execute("ALTER TABLE iam_security_states DROP CONSTRAINT iam_security_states_kind_check")
    op.execute(
        "ALTER TABLE iam_security_states ADD CONSTRAINT iam_security_states_kind_check "
        "CHECK(kind IN ('budget','attempt','preparation','credential','session_slot','mfa'))"
    )
    op.execute("ALTER TABLE iam_passkeys DROP COLUMN key_id,DROP COLUMN revoked_at")
    op.execute(
        "ALTER TABLE iam_accounts DROP COLUMN key_set_version,"
        "DROP COLUMN recovery_pending,DROP COLUMN recovery_generation"
    )
    op.execute(
        "ALTER TABLE audit_events DROP COLUMN key_id,DROP COLUMN before_key_set_version,"
        "DROP COLUMN after_key_set_version,DROP COLUMN before_recovery_generation,"
        "DROP COLUMN after_recovery_generation"
    )
    op.execute("ALTER TABLE audit_events DROP CONSTRAINT audit_events_action_check")
    op.execute(
        f"ALTER TABLE audit_events ADD CONSTRAINT audit_events_action_check "
        f"CHECK(action IN ({_ACTIONS}))"
    )
