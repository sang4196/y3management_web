"""Durable emergency execution history and bounded purpose-specific credentials."""

from alembic import op

revision = "0008_iam_emergency_recovery"
down_revision = "0007_iam_password_reset"
branch_labels = None
depends_on = None
_ACTIONS = (
    "'bootstrap','branch_create','account_issue','setup_reissue','setup_complete',"
    "'account_disable','scope_change','login','logout','account_restore',"
    "'password_change','login_id_change','passkey_register','passkey_delete',"
    "'recovery_start','recovery_reissue','recovery_complete',"
    "'password_reset_start','password_reset_reissue','password_reset_complete'"
)


def upgrade() -> None:
    op.execute("LOCK TABLE iam_security_control IN ACCESS EXCLUSIVE MODE")
    op.execute("""
    CREATE TABLE iam_emergency_cases (
      id uuid PRIMARY KEY,
      organization_id uuid NOT NULL REFERENCES organization_organizations(id),
      account_id uuid NOT NULL REFERENCES iam_accounts(id),
      factors text NOT NULL CHECK(factors IN ('password','passkey','both')),
      approval_ref varchar(128) NOT NULL, owner_ref varchar(128) NOT NULL,
      executor_ref varchar(128) NOT NULL, executor_uid bigint NOT NULL CHECK(executor_uid>=0),
      checked_at timestamptz NOT NULL, approval_valid_until timestamptz NOT NULL,
      issued_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      expires_at timestamptz NOT NULL, completed_at timestamptz,
      supersedes uuid REFERENCES iam_emergency_cases(id),
      row_version bigint NOT NULL CHECK(row_version>0),
      security_version bigint NOT NULL CHECK(security_version>0),
      key_set_version bigint NOT NULL CHECK(key_set_version>=0),
      reset_generation bigint NOT NULL CHECK(reset_generation>=0),
      recovery_generation bigint NOT NULL CHECK(recovery_generation>=0),
      expected_row_version bigint NOT NULL CHECK(expected_row_version>0),
      expected_security_version bigint NOT NULL CHECK(expected_security_version>0),
      expected_key_set_version bigint NOT NULL CHECK(expected_key_set_version>=0),
      expected_reset_generation bigint NOT NULL CHECK(expected_reset_generation>=0),
      expected_recovery_generation bigint NOT NULL CHECK(expected_recovery_generation>=0),
      expected_password_reset_pending boolean NOT NULL,
      expected_recovery_pending boolean NOT NULL,
      expected_password_ready boolean NOT NULL, expected_key_ready boolean NOT NULL,
      approval_mode text NOT NULL DEFAULT 'manual' CHECK(approval_mode='manual'),
      revocation_scope text NOT NULL DEFAULT 'target_only' CHECK(revocation_scope='target_only'),
      CHECK(checked_at<=issued_at AND approval_valid_until>issued_at),
      CHECK(expires_at>issued_at AND expires_at<=issued_at+interval '30 minutes'),
      UNIQUE(organization_id,approval_ref), UNIQUE(id,account_id,factors));
    CREATE TABLE iam_emergency_credentials (
      id uuid PRIMARY KEY REFERENCES iam_security_states(id) ON DELETE CASCADE,
      case_id uuid NOT NULL UNIQUE,
      factors text NOT NULL CHECK(factors IN ('password','passkey','both')),
      account_id uuid NOT NULL REFERENCES iam_accounts(id),
      digest bytea NOT NULL UNIQUE CHECK(octet_length(digest)=32),
      expires_at timestamptz NOT NULL, consumed boolean NOT NULL DEFAULT false,
      FOREIGN KEY(case_id,account_id,factors) REFERENCES iam_emergency_cases(id,account_id,factors),
      UNIQUE(id,account_id,factors));
    CREATE INDEX ON iam_emergency_credentials(account_id);
    ALTER TABLE iam_security_states DROP CONSTRAINT iam_security_states_kind_check;
    ALTER TABLE iam_security_states ADD CONSTRAINT iam_security_states_kind_check
      CHECK(kind IN ('budget','attempt','preparation','credential','session_slot','mfa',
        'recovery','password_reset','emergency'));
    ALTER TABLE iam_mfa_contexts ADD COLUMN emergency_id uuid
      REFERENCES iam_emergency_credentials(id) ON DELETE CASCADE;
    ALTER TABLE iam_mfa_contexts ADD COLUMN emergency_factors text;
    ALTER TABLE iam_mfa_contexts ADD CONSTRAINT iam_mfa_contexts_emergency_binding
      FOREIGN KEY(emergency_id,account_id,emergency_factors)
      REFERENCES iam_emergency_credentials(id,account_id,factors);
    ALTER TABLE iam_mfa_contexts DROP CONSTRAINT iam_mfa_contexts_purpose_check;
    ALTER TABLE iam_mfa_contexts ADD CONSTRAINT iam_mfa_contexts_purpose_check
      CHECK(purpose IN ('install','setup','add','login','recovery','emergency'));
    ALTER TABLE iam_mfa_contexts DROP CONSTRAINT iam_mfa_contexts_check1;
    ALTER TABLE iam_mfa_contexts ADD CONSTRAINT iam_mfa_contexts_check1 CHECK (
      (purpose='setup' AND source_id IS NOT NULL AND (consumed OR password_hash IS NOT NULL))
      OR (purpose='emergency' AND emergency_factors IS NOT NULL AND
        ((emergency_factors='both' AND (consumed OR password_hash IS NOT NULL))
         OR (emergency_factors='passkey' AND password_hash IS NULL)))
      OR (purpose NOT IN ('setup','emergency') AND password_hash IS NULL));
    ALTER TABLE iam_mfa_contexts ADD CONSTRAINT iam_mfa_contexts_emergency_check CHECK (
      (purpose='emergency' AND emergency_id IS NOT NULL AND source_id IS NULL
       AND recovery_id IS NULL AND session_id IS NULL AND attempt_id IS NULL
       AND budget_key IS NULL AND marker IS NULL)
      OR (purpose<>'emergency' AND emergency_id IS NULL AND emergency_factors IS NULL));
    ALTER TABLE audit_events ADD COLUMN emergency_case_id uuid REFERENCES iam_emergency_cases(id),
      ADD COLUMN emergency_factors text CHECK(emergency_factors IN ('password','passkey','both')),
      ADD COLUMN executor_ref varchar(128),
      ADD COLUMN approval_mode text CHECK(approval_mode='manual');
    ALTER TABLE audit_events DROP CONSTRAINT audit_events_action_check;
    """)
    op.execute(
        "ALTER TABLE audit_events ADD CONSTRAINT audit_events_action_check "
        f"CHECK(action IN ({_ACTIONS},'emergency_issue','emergency_complete'))"
    )
    op.execute("""ALTER TABLE audit_events ADD CONSTRAINT audit_events_emergency_check CHECK (
      (action IN ('emergency_issue','emergency_complete') AND emergency_case_id IS NOT NULL
        AND organization_id IS NOT NULL AND target_id IS NOT NULL
        AND emergency_factors IS NOT NULL AND executor_ref IS NOT NULL
        AND approval_mode IS NOT NULL AND actor_role IS NOT NULL AND actor_scope IS NOT NULL
        AND approval_mode='manual'
        AND ((action='emergency_issue' AND actor_id IS NULL
          AND actor_role='SYSTEM_RECOVERY_OPERATOR' AND actor_scope='EMERGENCY_RECOVERY')
          OR (action='emergency_complete' AND actor_id IS NOT NULL AND actor_id=target_id
            AND actor_role='RECOVERY_RECIPIENT' AND actor_scope='EMERGENCY_RECOVERY')))
      OR (action NOT IN ('emergency_issue','emergency_complete') AND emergency_case_id IS NULL
        AND emergency_factors IS NULL AND executor_ref IS NULL AND approval_mode IS NULL))""")


def downgrade() -> None:
    op.execute("LOCK TABLE iam_security_control IN ACCESS EXCLUSIVE MODE")
    op.execute(
        "LOCK TABLE iam_accounts,iam_sessions,iam_passkeys,iam_reset_credentials,"
        "iam_emergency_cases,iam_emergency_credentials,iam_mfa_contexts,"
        "iam_security_states,audit_events IN ACCESS EXCLUSIVE MODE"
    )
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM iam_emergency_cases)
      OR EXISTS(SELECT 1 FROM iam_emergency_credentials)
      OR EXISTS(SELECT 1 FROM iam_mfa_contexts WHERE emergency_id IS NOT NULL)
      OR EXISTS(SELECT 1 FROM iam_security_states WHERE kind='emergency')
      OR EXISTS(SELECT 1 FROM audit_events WHERE emergency_case_id IS NOT NULL) THEN
      RAISE EXCEPTION 'Emergency state or history prevents downgrade'; END IF; END $$""")
    op.execute("ALTER TABLE audit_events DROP CONSTRAINT audit_events_emergency_check")
    op.execute(
        "ALTER TABLE audit_events DROP COLUMN emergency_case_id,"
        "DROP COLUMN emergency_factors,DROP COLUMN executor_ref,DROP COLUMN approval_mode"
    )
    op.execute("ALTER TABLE audit_events DROP CONSTRAINT audit_events_action_check")
    op.execute(
        "ALTER TABLE audit_events ADD CONSTRAINT audit_events_action_check "
        f"CHECK(action IN ({_ACTIONS}))"
    )
    op.execute("ALTER TABLE iam_mfa_contexts DROP CONSTRAINT iam_mfa_contexts_emergency_check")
    op.execute("ALTER TABLE iam_mfa_contexts DROP CONSTRAINT iam_mfa_contexts_emergency_binding")
    op.execute("ALTER TABLE iam_mfa_contexts DROP CONSTRAINT iam_mfa_contexts_check1")
    op.execute(
        "ALTER TABLE iam_mfa_contexts DROP COLUMN emergency_id,DROP COLUMN emergency_factors"
    )
    op.execute("ALTER TABLE iam_mfa_contexts DROP CONSTRAINT iam_mfa_contexts_purpose_check")
    op.execute(
        "ALTER TABLE iam_mfa_contexts ADD CONSTRAINT iam_mfa_contexts_purpose_check "
        "CHECK(purpose IN ('install','setup','add','login','recovery'))"
    )
    op.execute("""ALTER TABLE iam_mfa_contexts ADD CONSTRAINT iam_mfa_contexts_check1 CHECK (
      (purpose='setup' AND source_id IS NOT NULL AND (consumed OR password_hash IS NOT NULL))
      OR (purpose<>'setup' AND password_hash IS NULL))""")
    op.execute("DROP TABLE iam_emergency_credentials,iam_emergency_cases")
    op.execute("ALTER TABLE iam_security_states DROP CONSTRAINT iam_security_states_kind_check")
    op.execute(
        "ALTER TABLE iam_security_states ADD CONSTRAINT iam_security_states_kind_check "
        "CHECK(kind IN ('budget','attempt','preparation','credential','session_slot','mfa',"
        "'recovery','password_reset'))"
    )
