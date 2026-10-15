"""First IAM / Organization / Audit schema; explicit Alembic only."""

from alembic import op

revision = "0001_iam_s1"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE organization_organizations (id uuid PRIMARY KEY, name text NOT NULL);
    CREATE TABLE organization_branches (
      id uuid PRIMARY KEY, organization_id uuid NOT NULL REFERENCES organization_organizations(id),
      code varchar(32) NOT NULL, name varchar(128) NOT NULL,
      UNIQUE(organization_id,id), UNIQUE(organization_id,code));
    CREATE TABLE iam_installation (
      id integer PRIMARY KEY CHECK(id=1), organization_id uuid REFERENCES
      organization_organizations(id));
    INSERT INTO iam_installation(id) VALUES(1);
    CREATE TABLE iam_accounts (
      id uuid PRIMARY KEY, organization_id uuid NOT NULL REFERENCES organization_organizations(id),
      login_id varchar(64) NOT NULL UNIQUE CHECK(login_id ~ '^[a-z0-9][a-z0-9_.-]{2,63}$'),
      state text NOT NULL CHECK(state IN ('PENDING_SETUP','ACTIVE','DISABLED')),
      password_hash text,
      row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0),
      security_version bigint NOT NULL DEFAULT 1 CHECK(security_version>0),
      UNIQUE(organization_id,id),
      CHECK((state='PENDING_SETUP' AND password_hash IS NULL)
         OR (state IN ('ACTIVE','DISABLED') AND password_hash IS NOT NULL)));
    CREATE TABLE iam_login_ids (
      login_id varchar(64) PRIMARY KEY CHECK(login_id ~ '^[a-z0-9][a-z0-9_.-]{2,63}$'),
      account_id uuid NOT NULL REFERENCES iam_accounts(id), UNIQUE(login_id,account_id));
    ALTER TABLE iam_accounts ADD CONSTRAINT iam_current_id_owner
      FOREIGN KEY(login_id,id) REFERENCES iam_login_ids(login_id,account_id)
      DEFERRABLE INITIALLY DEFERRED;
    CREATE TABLE iam_admin_grants (
      account_id uuid PRIMARY KEY, organization_id uuid NOT NULL,
      scope text NOT NULL CHECK(scope IN ('ORGANIZATION','BRANCH')), branch_id uuid,
      FOREIGN KEY(organization_id,account_id) REFERENCES iam_accounts(organization_id,id),
      FOREIGN KEY(organization_id,branch_id) REFERENCES organization_branches(organization_id,id),
      CHECK((scope='ORGANIZATION' AND branch_id IS NULL) OR (scope='BRANCH' AND branch_id IS NOT
      NULL)));
    CREATE TABLE iam_sessions (
      id uuid PRIMARY KEY, account_id uuid NOT NULL REFERENCES iam_accounts(id),
      digest bytea NOT NULL UNIQUE, csrf text NOT NULL,
      security_version bigint NOT NULL CHECK(security_version>0),
      created_at timestamptz NOT NULL, last_activity timestamptz NOT NULL,
      expires_at timestamptz NOT NULL, revoked boolean NOT NULL DEFAULT false,
      CHECK(created_at<=last_activity AND last_activity<=expires_at));
    CREATE INDEX ON iam_sessions(account_id,id);
    CREATE TABLE iam_security_control(id integer PRIMARY KEY CHECK(id=1));
    INSERT INTO iam_security_control VALUES(1);
    CREATE TABLE iam_security_states (
      id uuid PRIMARY KEY, kind text NOT NULL CHECK(kind IN
      ('budget','attempt','preparation','credential','session_slot')),
      expires_at timestamptz NOT NULL,
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(), UNIQUE(id,expires_at));
    ALTER TABLE iam_sessions ADD CONSTRAINT iam_session_slot
      FOREIGN KEY(id,expires_at) REFERENCES iam_security_states(id,expires_at);
    CREATE INDEX ON iam_security_states(expires_at);
    CREATE TABLE iam_budgets (
      key bytea PRIMARY KEY, state_id uuid NOT NULL UNIQUE REFERENCES iam_security_states(id) ON
      DELETE CASCADE,
      cooldown timestamptz);
    CREATE TABLE iam_attempts (
      id uuid PRIMARY KEY REFERENCES iam_security_states(id) ON DELETE CASCADE,
      key bytea NOT NULL REFERENCES iam_budgets(key),
      outcome text NOT NULL CHECK(outcome IN ('pending','success','failure')),
      lease_until timestamptz NOT NULL, finished_at timestamptz);
    CREATE INDEX ON iam_attempts(key);
    CREATE TABLE iam_preparations (
      id uuid PRIMARY KEY REFERENCES iam_security_states(id) ON DELETE CASCADE,
      digest bytea NOT NULL UNIQUE, csrf text NOT NULL, expires_at timestamptz NOT NULL,
      consumed boolean NOT NULL DEFAULT false);
    CREATE TABLE iam_credentials (
      id uuid PRIMARY KEY REFERENCES iam_security_states(id) ON DELETE CASCADE,
      account_id uuid NOT NULL REFERENCES iam_accounts(id),
      digest bytea NOT NULL UNIQUE, row_version bigint NOT NULL CHECK(row_version>0),
      expires_at timestamptz NOT NULL, consumed boolean NOT NULL DEFAULT false);
    CREATE UNIQUE INDEX iam_one_pending_credential ON iam_credentials(account_id) WHERE NOT
      consumed;
    CREATE TABLE audit_events (
      id uuid PRIMARY KEY, organization_id uuid REFERENCES organization_organizations(id),
      actor_id uuid REFERENCES iam_accounts(id), target_id uuid, action text NOT NULL,
      happened_at timestamptz NOT NULL DEFAULT clock_timestamp(), success boolean NOT NULL,
      before_state text, after_state text, before_branch uuid, after_branch uuid,
      actor_role text, actor_scope text, actor_branch uuid,
      before_version bigint, after_version bigint, branch_code text, branch_name text,
      request_id uuid NOT NULL,
      CHECK(action IN ('bootstrap','branch_create','account_issue','setup_reissue','setup_complete',
                       'account_disable','scope_change','login','logout')));
    """)


def downgrade() -> None:
    # Operator-invoked destructive migration; never called by application startup.
    op.execute("ALTER TABLE iam_accounts DROP CONSTRAINT iam_current_id_owner")
    op.execute("ALTER TABLE iam_sessions DROP CONSTRAINT iam_session_slot")
    for table in (
        "audit_events",
        "iam_credentials",
        "iam_preparations",
        "iam_attempts",
        "iam_budgets",
        "iam_security_states",
        "iam_security_control",
        "iam_sessions",
        "iam_admin_grants",
        "iam_login_ids",
        "iam_accounts",
        "iam_installation",
        "organization_branches",
        "organization_organizations",
    ):
        op.execute(f"DROP TABLE {table}")
