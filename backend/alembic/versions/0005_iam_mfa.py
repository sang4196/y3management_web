"""Bounded MFA ceremonies and independently recorded authentication assurance."""

from alembic import op

revision = "0005_iam_mfa"
down_revision = "0004_iam_login_id"
branch_labels = None
depends_on = None
_ACTIONS = (
    "'bootstrap','branch_create','account_issue','setup_reissue','setup_com"
    "plete','account_disable','scope_change','login','logout','account_rest"
    "ore','password_change','login_id_change'"
)


def upgrade() -> None:
    op.execute("""
    ALTER TABLE iam_sessions ADD COLUMN assurance text NOT NULL DEFAULT 'password'
      CHECK(assurance IN ('password','password_uv'));
    ALTER TABLE iam_attempts ADD COLUMN stage text NOT NULL DEFAULT 'password'
      CHECK(stage IN ('password','waiting','verifying'));
    ALTER TABLE iam_security_states DROP CONSTRAINT iam_security_states_kind_check;
    ALTER TABLE iam_security_states ADD CONSTRAINT iam_security_states_kind_check
      CHECK(kind IN ('budget','attempt','preparation','credential','session_slot','mfa'));
    CREATE TABLE iam_passkeys (
      credential_id bytea PRIMARY KEY CHECK(octet_length(credential_id) BETWEEN 1 AND 1024),
      account_id uuid NOT NULL REFERENCES iam_accounts(id), public_key bytea NOT NULL,
      sign_count bigint NOT NULL CHECK(sign_count>=0), device_type text NOT NULL
        CHECK(device_type IN ('single_device','multi_device')), backed_up boolean NOT NULL,
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      CHECK(NOT backed_up OR device_type='multi_device'));
    CREATE INDEX ON iam_passkeys(account_id);
    CREATE TABLE iam_mfa_contexts (
      id uuid PRIMARY KEY REFERENCES iam_security_states(id) ON DELETE CASCADE,
      digest bytea NOT NULL UNIQUE CHECK(octet_length(digest)=32), csrf text NOT NULL,
      account_id uuid NOT NULL REFERENCES iam_accounts(id),
      purpose text NOT NULL CHECK(purpose IN ('install','setup','add','login')),
      security_version bigint NOT NULL CHECK(security_version>0), row_version bigint NOT NULL,
      expires_at timestamptz NOT NULL, consumed boolean NOT NULL DEFAULT false,
      challenge bytea, password_hash text, marker bytea,
      source_id uuid REFERENCES iam_credentials(id) ON DELETE CASCADE,
      session_id uuid REFERENCES iam_sessions(id) ON DELETE CASCADE,
      attempt_id uuid REFERENCES iam_attempts(id) ON DELETE CASCADE,
      budget_key bytea,
      CHECK ((purpose='login' AND attempt_id IS NOT NULL AND budget_key IS NOT NULL
         AND marker IS NOT NULL) OR (purpose<>'login' AND attempt_id IS NULL)),
      CHECK ((purpose='setup' AND source_id IS NOT NULL AND (consumed OR password_hash IS NOT NULL))
         OR (purpose<>'setup' AND password_hash IS NULL)),
      CHECK ((purpose='add' AND session_id IS NOT NULL) OR
         (purpose<>'add' AND session_id IS NULL)));
    CREATE INDEX ON iam_mfa_contexts(account_id);
    ALTER TABLE audit_events DROP CONSTRAINT audit_events_action_check;
    """)
    op.execute(
        f"ALTER TABLE audit_events ADD CONSTRAINT "
        f"audit_events_action_check CHECK(action IN ({_ACTIONS},'passkey_register'))"
    )


def downgrade() -> None:
    op.execute(
        "LOCK TABLE "
        "iam_accounts,iam_sessions,iam_passkeys,iam_mfa_contexts,"
        "iam_attempts,audit_events,iam_security_states,"
        "iam_security_control IN ACCESS EXCLUSIVE MODE"
    )
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM iam_passkeys)
      OR EXISTS(SELECT 1 FROM iam_mfa_contexts)
      OR EXISTS(SELECT 1 FROM iam_security_states WHERE kind='mfa')
      OR EXISTS(SELECT 1 FROM iam_sessions WHERE assurance='password_uv')
      OR EXISTS(SELECT 1 FROM iam_attempts WHERE stage<>'password')
      OR EXISTS(SELECT 1 FROM audit_events WHERE action='passkey_register') THEN
      RAISE EXCEPTION 'MFA state or history prevents downgrade'; END IF; END $$""")
    op.execute("DROP TABLE iam_mfa_contexts,iam_passkeys")
    op.execute("ALTER TABLE iam_security_states DROP CONSTRAINT iam_security_states_kind_check")
    op.execute(
        "ALTER TABLE iam_security_states ADD CONSTRAINT "
        "iam_security_states_kind_check CHECK(kind IN ('budget','attempt',"
        "'preparation','credential','session_slot'))"
    )
    op.execute("ALTER TABLE iam_sessions DROP COLUMN assurance")
    op.execute("ALTER TABLE iam_attempts DROP COLUMN stage")
    op.execute("ALTER TABLE audit_events DROP CONSTRAINT audit_events_action_check")
    op.execute(
        f"ALTER TABLE audit_events ADD CONSTRAINT "
        f"audit_events_action_check CHECK(action IN ({_ACTIONS}))"
    )
