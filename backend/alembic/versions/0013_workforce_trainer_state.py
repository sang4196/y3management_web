"""Observed origins and atomic forward Trainer state facts; no inferred past."""

from alembic import op

revision = "0013_workforce_trainer_state"
down_revision = "0012_iam_trainer_roles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    LOCK TABLE iam_installation, workforce_trainers IN ACCESS EXCLUSIVE MODE;
    CREATE TABLE workforce_trainer_state_origins (
      trainer_id uuid PRIMARY KEY, organization_id uuid NOT NULL,
      origin text NOT NULL CHECK(origin IN ('legacy_observation','registered')),
      active boolean NOT NULL, trainer_version bigint NOT NULL CHECK(trainer_version>0),
      recorded_at timestamptz NOT NULL, registration_operation_id uuid,
      FOREIGN KEY(organization_id,trainer_id) REFERENCES workforce_trainers(organization_id,id),
      FOREIGN KEY(organization_id,registration_operation_id,trainer_id) REFERENCES
        workforce_registration_operations(organization_id,operation_id,trainer_id),
      CHECK((origin='legacy_observation' AND registration_operation_id IS NULL) OR
        (origin='registered' AND registration_operation_id IS NOT NULL AND active
          AND trainer_version=1)));
    CREATE TABLE workforce_trainer_state_operations (
      organization_id uuid NOT NULL, operation_id uuid NOT NULL, trainer_id uuid NOT NULL,
      actor_id uuid NOT NULL, target_home uuid NOT NULL,
      canonical_version integer NOT NULL CHECK(canonical_version=1),
      fingerprint bytea NOT NULL CHECK(octet_length(fingerprint)=32),
      desired_active boolean NOT NULL, expected_trainer_version bigint NOT NULL,
      before_active boolean NOT NULL, before_version bigint NOT NULL CHECK(before_version>0),
      committed_active boolean NOT NULL, committed_trainer_version bigint NOT NULL,
      changed boolean NOT NULL, recorded_at timestamptz NOT NULL,
      PRIMARY KEY(organization_id,operation_id),
      UNIQUE(organization_id,operation_id,trainer_id),
      UNIQUE(organization_id,operation_id,trainer_id,before_active,committed_active,
        before_version,committed_trainer_version,changed),
      FOREIGN KEY(organization_id,trainer_id) REFERENCES workforce_trainers(organization_id,id),
      FOREIGN KEY(organization_id,actor_id) REFERENCES iam_accounts(organization_id,id),
      FOREIGN KEY(organization_id,target_home) REFERENCES organization_branches(organization_id,id),
      CHECK(expected_trainer_version=before_version AND desired_active=committed_active),
      CHECK((changed AND before_active<>committed_active
        AND committed_trainer_version=before_version+1) OR
        (NOT changed AND before_active=committed_active
        AND committed_trainer_version=before_version)));
    CREATE TABLE workforce_trainer_state_transitions (
      organization_id uuid NOT NULL, operation_id uuid NOT NULL, trainer_id uuid NOT NULL,
      before_active boolean NOT NULL, after_active boolean NOT NULL,
      before_version bigint NOT NULL CHECK(before_version>0), after_version bigint NOT NULL,
      changed boolean NOT NULL DEFAULT true CHECK(changed), recorded_at timestamptz NOT NULL,
      PRIMARY KEY(organization_id,operation_id),
      UNIQUE(organization_id,trainer_id,after_version),
      UNIQUE(organization_id,operation_id,trainer_id,before_active,after_active,
        before_version,after_version),
      FOREIGN KEY(organization_id,operation_id,trainer_id,before_active,after_active,
        before_version,after_version,changed) REFERENCES workforce_trainer_state_operations
        (organization_id,operation_id,trainer_id,before_active,committed_active,
        before_version,committed_trainer_version,changed),
      CHECK(before_active<>after_active AND after_version=before_version+1));
    CREATE TABLE audit_trainer_state_events (
      id uuid PRIMARY KEY, organization_id uuid NOT NULL, operation_id uuid NOT NULL,
      trainer_id uuid NOT NULL, account_id uuid, actor_id uuid NOT NULL,
      actor_role text NOT NULL, actor_branch uuid, target_home uuid NOT NULL,
      before_active boolean NOT NULL, after_active boolean NOT NULL,
      before_version bigint NOT NULL CHECK(before_version>0), after_version bigint NOT NULL,
      recorded_at timestamptz NOT NULL,
      UNIQUE(organization_id,operation_id),
      FOREIGN KEY(organization_id,operation_id,trainer_id,before_active,after_active,
        before_version,after_version) REFERENCES workforce_trainer_state_transitions
        (organization_id,operation_id,trainer_id,before_active,after_active,
        before_version,after_version),
      FOREIGN KEY(organization_id,account_id,trainer_id) REFERENCES
        iam_trainer_bindings(organization_id,account_id,trainer_id),
      FOREIGN KEY(organization_id,actor_id) REFERENCES iam_accounts(organization_id,id),
      FOREIGN KEY(organization_id,actor_branch) REFERENCES
        organization_branches(organization_id,id),
      FOREIGN KEY(organization_id,target_home) REFERENCES organization_branches(organization_id,id),
      CHECK(before_active<>after_active AND after_version=before_version+1),
      CHECK((actor_role='MASTER' AND actor_branch IS NULL) OR
        (actor_role='BRANCH_ADMIN' AND actor_branch IS NOT NULL AND actor_branch=target_home)));
    INSERT INTO workforce_trainer_state_origins
      (trainer_id,organization_id,origin,active,trainer_version,recorded_at)
      SELECT id,organization_id,'legacy_observation',active,row_version,clock_timestamp()
      FROM workforce_trainers;
    """)


def downgrade() -> None:
    op.execute("""
    LOCK TABLE iam_installation, workforce_trainers, workforce_trainer_state_origins,
      workforce_trainer_state_operations, workforce_trainer_state_transitions,
      audit_trainer_state_events IN ACCESS EXCLUSIVE MODE;
    DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM workforce_trainer_state_operations)
        OR EXISTS(SELECT 1 FROM workforce_trainer_state_transitions)
        OR EXISTS(SELECT 1 FROM audit_trainer_state_events)
        OR EXISTS(SELECT 1 FROM workforce_trainer_state_origins WHERE origin<>'legacy_observation')
        OR EXISTS(SELECT 1 FROM workforce_trainers t FULL JOIN workforce_trainer_state_origins o
          ON t.id=o.trainer_id WHERE t.id IS NULL OR o.trainer_id IS NULL
            OR t.organization_id<>o.organization_id OR t.active<>o.active
            OR t.row_version<>o.trainer_version)
      THEN RAISE EXCEPTION 'trainer state facts must be preserved'; END IF;
    END $$;
    DROP TABLE audit_trainer_state_events;
    DROP TABLE workforce_trainer_state_transitions;
    DROP TABLE workforce_trainer_state_operations;
    DROP TABLE workforce_trainer_state_origins;
    """)
