"""Separate immutable Trainer identity from current role and authentication epoch."""

from alembic import op

revision = "0012_iam_trainer_roles"
down_revision = "0011_iam_trainer_login"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    LOCK TABLE iam_installation,iam_accounts,iam_sessions,iam_credentials,iam_mfa_contexts,
      iam_recovery_credentials,iam_reset_credentials,iam_emergency_credentials,
      iam_trainer_setup_credentials,iam_trainer_bindings IN ACCESS EXCLUSIVE MODE;
    ALTER TABLE iam_accounts ADD COLUMN trainer_role_epoch bigint NOT NULL DEFAULT 0
      CHECK(trainer_role_epoch>=0), ADD CONSTRAINT iam_account_role_epoch
      UNIQUE(id,trainer_role_epoch);
    ALTER TABLE iam_sessions ADD COLUMN trainer_role_epoch bigint NOT NULL DEFAULT 0
      CHECK(trainer_role_epoch>=0);
    ALTER TABLE iam_mfa_contexts ADD COLUMN trainer_role_epoch bigint NOT NULL DEFAULT 0
      CHECK(trainer_role_epoch>=0);
    ALTER TABLE iam_trainer_setup_credentials ADD COLUMN trainer_role_epoch bigint NOT NULL
      DEFAULT 0
      CHECK(trainer_role_epoch>=0);
    UPDATE iam_accounts SET trainer_role_epoch=1
      WHERE id IN (SELECT account_id FROM iam_trainer_bindings);
    UPDATE iam_sessions s SET trainer_role_epoch=a.trainer_role_epoch FROM iam_accounts a
      WHERE s.account_id=a.id;
    UPDATE iam_mfa_contexts c SET trainer_role_epoch=a.trainer_role_epoch FROM iam_accounts a
      WHERE c.account_id=a.id;
    UPDATE iam_trainer_setup_credentials c SET trainer_role_epoch=a.trainer_role_epoch
      FROM iam_accounts a WHERE c.account_id=a.id;
    CREATE TABLE iam_trainer_role_grants (
      account_id uuid PRIMARY KEY,organization_id uuid NOT NULL,trainer_id uuid NOT NULL UNIQUE,
      granted boolean NOT NULL,role_version bigint NOT NULL CHECK(role_version>0),
      origin text NOT NULL CHECK(origin IN ('backfill','i1_issue','i2_link')),
      changed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      FOREIGN KEY(organization_id,account_id,trainer_id)
        REFERENCES iam_trainer_bindings(organization_id,account_id,trainer_id),
      FOREIGN KEY(account_id,role_version) REFERENCES iam_accounts(id,trainer_role_epoch)
        DEFERRABLE INITIALLY DEFERRED);
    INSERT INTO iam_trainer_role_grants(account_id,organization_id,trainer_id,granted,
      role_version,origin)
      SELECT account_id,organization_id,trainer_id,true,1,'backfill' FROM iam_trainer_bindings;
    CREATE TABLE iam_trainer_role_operations (
      organization_id uuid NOT NULL,operation_id uuid NOT NULL,trainer_id uuid NOT NULL,
      account_id uuid NOT NULL,actor_id uuid NOT NULL,target_home uuid NOT NULL,
      fingerprint bytea NOT NULL CHECK(octet_length(fingerprint)=32),
      changed boolean NOT NULL,granted boolean NOT NULL,
      committed_role_version bigint NOT NULL CHECK(committed_role_version>0),
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      PRIMARY KEY(organization_id,operation_id),
      UNIQUE(organization_id,operation_id,account_id,trainer_id),
      FOREIGN KEY(organization_id,account_id,trainer_id)
        REFERENCES iam_trainer_bindings(organization_id,account_id,trainer_id),
      FOREIGN KEY(organization_id,actor_id) REFERENCES iam_accounts(organization_id,id),
      FOREIGN KEY(organization_id,target_home) REFERENCES
      organization_branches(organization_id,id));
    CREATE TABLE audit_trainer_role_events (
      id uuid PRIMARY KEY,organization_id uuid NOT NULL,operation_id uuid NOT NULL,
      account_id uuid NOT NULL,trainer_id uuid NOT NULL,actor_id uuid NOT NULL,
      actor_role text NOT NULL,actor_branch uuid,target_home uuid NOT NULL,
      kind text NOT NULL CHECK(kind IN ('add','revoke','regrant')),
      before_granted boolean NOT NULL,after_granted boolean NOT NULL,
      before_role_version bigint NOT NULL CHECK(before_role_version>=0),
      after_role_version bigint NOT NULL CHECK(after_role_version=before_role_version+1),
      before_epoch bigint NOT NULL CHECK(before_epoch=before_role_version),
      after_epoch bigint NOT NULL CHECK(after_epoch=after_role_version),
      before_account_version bigint NOT NULL CHECK(before_account_version>0),
      after_account_version bigint NOT NULL CHECK(after_account_version=before_account_version),
      before_security_version bigint NOT NULL CHECK(before_security_version>0),
      after_security_version bigint NOT NULL CHECK(after_security_version=before_security_version),
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      UNIQUE(organization_id,operation_id),
      FOREIGN KEY(organization_id,operation_id,account_id,trainer_id)
        REFERENCES iam_trainer_role_operations(organization_id,operation_id,account_id,trainer_id),
      FOREIGN KEY(organization_id,actor_id) REFERENCES iam_accounts(organization_id,id),
      FOREIGN KEY(organization_id,actor_branch) REFERENCES
      organization_branches(organization_id,id),
      FOREIGN KEY(organization_id,target_home) REFERENCES organization_branches(organization_id,id),
      CHECK((actor_role='MASTER' AND actor_branch IS NULL) OR
        (actor_role='BRANCH_ADMIN' AND actor_branch IS NOT NULL AND actor_branch=target_home)),
      CHECK((kind='add' AND before_role_version=0 AND NOT before_granted AND after_granted) OR
        (kind='regrant' AND before_role_version>0 AND NOT before_granted AND after_granted) OR
        (kind='revoke' AND before_role_version>0 AND before_granted AND NOT after_granted)));
    """)


def downgrade() -> None:
    op.execute("""
    LOCK TABLE iam_installation,iam_accounts,iam_sessions,iam_credentials,iam_mfa_contexts,
      iam_recovery_credentials,iam_reset_credentials,iam_emergency_credentials,
      iam_trainer_setup_credentials,iam_trainer_role_grants,iam_trainer_bindings,
      iam_trainer_role_operations,audit_trainer_role_events IN ACCESS EXCLUSIVE MODE;
    DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM iam_trainer_role_operations)
        OR EXISTS(SELECT 1 FROM audit_trainer_role_events)
        OR EXISTS(SELECT 1 FROM iam_trainer_role_grants
          WHERE origin<>'backfill' OR NOT granted OR role_version<>1)
        OR EXISTS(SELECT 1 FROM iam_trainer_bindings b LEFT JOIN iam_trainer_role_grants g
          USING(account_id) WHERE g.account_id IS NULL)
        OR EXISTS(SELECT 1 FROM iam_accounts a LEFT JOIN iam_trainer_bindings b ON b.account_id=a.id
          WHERE a.trainer_role_epoch<>CASE WHEN b.account_id IS NULL THEN 0 ELSE 1 END)
        OR EXISTS(SELECT 1 FROM iam_sessions s JOIN iam_accounts a ON a.id=s.account_id
          WHERE s.trainer_role_epoch<>a.trainer_role_epoch)
        OR EXISTS(SELECT 1 FROM iam_mfa_contexts c JOIN iam_accounts a ON a.id=c.account_id
          WHERE c.trainer_role_epoch<>a.trainer_role_epoch)
        OR EXISTS(SELECT 1 FROM iam_trainer_setup_credentials c
          JOIN iam_accounts a ON a.id=c.account_id
          WHERE c.trainer_role_epoch<>a.trainer_role_epoch)
      THEN RAISE EXCEPTION 'trainer role history must be preserved'; END IF;
    END $$;
    DROP TABLE audit_trainer_role_events;
    DROP TABLE iam_trainer_role_operations;
    DROP TABLE iam_trainer_role_grants;
    ALTER TABLE iam_trainer_setup_credentials DROP COLUMN trainer_role_epoch;
    ALTER TABLE iam_mfa_contexts DROP COLUMN trainer_role_epoch;
    ALTER TABLE iam_sessions DROP COLUMN trainer_role_epoch;
    ALTER TABLE iam_accounts DROP CONSTRAINT iam_account_role_epoch,DROP COLUMN trainer_role_epoch;
    """)
