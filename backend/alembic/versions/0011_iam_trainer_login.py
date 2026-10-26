"""Explicit Trainer identity, one-time initial setup and durable typed identity audit."""

from alembic import op

revision = "0011_iam_trainer_login"
down_revision = "0010_workforce_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE iam_trainer_bindings (
      account_id uuid PRIMARY KEY, organization_id uuid NOT NULL, trainer_id uuid NOT NULL UNIQUE,
      binding_version bigint NOT NULL DEFAULT 1 CHECK(binding_version=1),
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      UNIQUE(organization_id,account_id,trainer_id),
      FOREIGN KEY(organization_id,account_id) REFERENCES iam_accounts(organization_id,id),
      FOREIGN KEY(organization_id,trainer_id) REFERENCES workforce_trainers(organization_id,id));
    CREATE TABLE iam_trainer_account_operations (
      organization_id uuid NOT NULL, operation_id uuid NOT NULL,
      kind text NOT NULL CHECK(kind IN ('issue','reissue')),
      trainer_id uuid NOT NULL, account_id uuid NOT NULL, actor_id uuid NOT NULL,
      target_home_at_commit uuid NOT NULL, canonical_version integer NOT NULL
        CHECK(canonical_version=1),
      fingerprint bytea NOT NULL CHECK(octet_length(fingerprint)=32),
      committed_account_version bigint NOT NULL CHECK(committed_account_version>0),
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      PRIMARY KEY(organization_id,operation_id),
      UNIQUE(organization_id,operation_id,account_id,trainer_id),
      FOREIGN KEY(organization_id,account_id,trainer_id)
        REFERENCES iam_trainer_bindings(organization_id,account_id,trainer_id),
      FOREIGN KEY(organization_id,actor_id) REFERENCES iam_accounts(organization_id,id),
      FOREIGN KEY(organization_id,target_home_at_commit) REFERENCES
        organization_branches(organization_id,id));
    CREATE TABLE iam_trainer_setup_credentials (
      id uuid PRIMARY KEY REFERENCES iam_security_states(id) ON DELETE CASCADE,
      purpose text NOT NULL CHECK(purpose='trainer_initial'), organization_id uuid NOT NULL,
      account_id uuid NOT NULL, trainer_id uuid NOT NULL,
      digest bytea NOT NULL UNIQUE CHECK(octet_length(digest)=32),
      account_version bigint NOT NULL CHECK(account_version>0),
      security_version bigint NOT NULL CHECK(security_version>0),
      binding_version bigint NOT NULL CHECK(binding_version=1),
      expires_at timestamptz NOT NULL, consumed boolean NOT NULL DEFAULT false,
      FOREIGN KEY(organization_id,account_id,trainer_id)
        REFERENCES iam_trainer_bindings(organization_id,account_id,trainer_id));
    CREATE UNIQUE INDEX iam_one_trainer_initial ON iam_trainer_setup_credentials(account_id)
      WHERE NOT consumed;
    CREATE TABLE audit_trainer_identity_events (
      id uuid PRIMARY KEY, organization_id uuid NOT NULL, account_id uuid NOT NULL,
      trainer_id uuid NOT NULL, kind text NOT NULL CHECK(kind IN
        ('issue','reissue','setup_complete','login','logout','password_change')),
      actor_id uuid, actor_role text NOT NULL CHECK(actor_role IN
        ('MASTER','BRANCH_ADMIN','TRAINER','CREDENTIAL_HOLDER')), actor_branch uuid,
      target_home uuid NOT NULL, operation_id uuid,
      before_state text, after_state text NOT NULL,
      before_version bigint, after_version bigint NOT NULL CHECK(after_version>0),
      before_security_version bigint, after_security_version bigint NOT NULL
        CHECK(after_security_version>0),
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      FOREIGN KEY(organization_id,account_id,trainer_id)
        REFERENCES iam_trainer_bindings(organization_id,account_id,trainer_id),
      FOREIGN KEY(organization_id,operation_id,account_id,trainer_id)
        REFERENCES
        iam_trainer_account_operations(organization_id,operation_id,account_id,trainer_id),
      FOREIGN KEY(organization_id,actor_id) REFERENCES iam_accounts(organization_id,id),
      FOREIGN KEY(organization_id,actor_branch) REFERENCES
        organization_branches(organization_id,id),
      FOREIGN KEY(organization_id,target_home) REFERENCES organization_branches(organization_id,id),
      CHECK((kind IN ('issue','reissue') AND operation_id IS NOT NULL AND actor_id IS NOT NULL
        AND ((actor_role='MASTER' AND actor_branch IS NULL) OR
          (actor_role='BRANCH_ADMIN' AND actor_branch IS NOT NULL AND actor_branch=target_home)))
        OR (kind='setup_complete' AND operation_id IS NULL AND actor_id IS NULL
          AND actor_role='CREDENTIAL_HOLDER' AND actor_branch IS NULL)
        OR (kind IN ('login','logout','password_change') AND operation_id IS NULL
          AND actor_id IS NOT NULL AND actor_id=account_id AND actor_role='TRAINER' AND
        actor_branch IS NULL)),
      CHECK((kind='issue' AND before_state IS NULL AND after_state='PENDING_SETUP'
          AND before_version IS NULL AND before_security_version IS NULL
          AND after_version=1 AND after_security_version=1)
        OR (kind='reissue' AND before_state IS NOT NULL AND before_state='PENDING_SETUP'
          AND after_state='PENDING_SETUP' AND before_version IS NOT NULL AND before_version>0
          AND before_security_version IS NOT NULL AND before_security_version>0
          AND after_version=before_version+1 AND after_security_version=before_security_version)
        OR (kind='setup_complete' AND before_state IS NOT NULL AND before_state='PENDING_SETUP'
          AND after_state='ACTIVE' AND before_version IS NOT NULL AND before_version>0
          AND before_security_version IS NOT NULL AND before_security_version>0
          AND after_version=before_version+1 AND after_security_version=before_security_version+1)
        OR (kind IN ('login','logout','password_change') AND before_state IS NOT NULL
          AND before_state='ACTIVE' AND after_state='ACTIVE'
          AND before_version IS NOT NULL AND before_version>0
          AND before_security_version IS NOT NULL AND before_security_version>0
          AND ((kind='password_change' AND after_version=before_version+1
            AND after_security_version=before_security_version+1)
            OR (kind IN ('login','logout') AND after_version=before_version
              AND after_security_version=before_security_version)))));
    CREATE UNIQUE INDEX audit_trainer_operation_once ON audit_trainer_identity_events
      (organization_id,operation_id) WHERE operation_id IS NOT NULL;
    """)


def downgrade() -> None:
    op.execute("""
    LOCK TABLE iam_installation, iam_accounts, iam_sessions, iam_trainer_bindings,
      iam_trainer_account_operations, iam_trainer_setup_credentials,
      audit_trainer_identity_events IN ACCESS EXCLUSIVE MODE;
    DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM iam_trainer_bindings)
        OR EXISTS(SELECT 1 FROM iam_trainer_account_operations)
        OR EXISTS(SELECT 1 FROM iam_trainer_setup_credentials)
        OR EXISTS(SELECT 1 FROM audit_trainer_identity_events)
      THEN RAISE EXCEPTION 'trainer identity history must be preserved'; END IF;
    END $$;
    DROP TABLE audit_trainer_identity_events;
    DROP TABLE iam_trainer_setup_credentials;
    DROP TABLE iam_trainer_account_operations;
    DROP TABLE iam_trainer_bindings;
    """)
