"""Observed Home origins and atomic forward changes, without inferred past."""

from sqlalchemy import text

from alembic import op

revision = "0019_workforce_trainer_home"
down_revision = "0018_withdrawn_operator_move"
branch_labels = None
depends_on = None


def preflight(expected: str) -> None:
    op.execute("LOCK TABLE iam_installation IN ACCESS EXCLUSIVE MODE")
    op.execute("LOCK TABLE alembic_version, iam_policy_transitions IN ACCESS EXCLUSIVE MODE")
    bind = op.get_bind()
    if list(bind.execute(text("SELECT version_num FROM alembic_version")).scalars()) != [expected]:
        raise ValueError("TRAINER_HOME_SCHEMA_MISMATCH")
    if not bind.execute(
        text("""SELECT EXISTS(SELECT FROM iam_installation i
        JOIN iam_policy_transitions p ON p.id=i.policy_transition_id
        WHERE i.id=1 AND i.auth_policy_version=2 AND p.from_version=1 AND p.to_version=2
        AND p.target_schema_revision='0014_password_only')""")
    ).scalar_one():
        raise ValueError("TRAINER_HOME_POLICY_MISMATCH")
    op.execute("""LOCK TABLE workforce_trainers,workforce_initial_snapshots,
        workforce_registration_operations,audit_workforce_initial_events
        IN ACCESS EXCLUSIVE MODE""")


def upgrade() -> None:
    preflight(down_revision)
    op.execute("""
    DO $$ BEGIN
      IF EXISTS(SELECT FROM workforce_trainers t
        LEFT JOIN organization_branches b ON b.id=t.home_branch_id
          AND b.organization_id=t.organization_id
        LEFT JOIN workforce_initial_snapshots s ON s.trainer_id=t.id
          AND s.organization_id=t.organization_id
        LEFT JOIN workforce_registration_operations r ON r.trainer_id=t.id
          AND r.organization_id=t.organization_id
        WHERE b.id IS NULL OR s.trainer_id IS NULL OR r.trainer_id IS NULL
          OR t.created_at<>s.created_at
          OR NOT EXISTS(SELECT FROM audit_workforce_initial_events a
            WHERE a.organization_id=t.organization_id AND a.trainer_id=t.id
              AND a.operation_id=r.operation_id AND a.actor_id=r.creator_account_id
              AND a.event_kind='trainer_registered' AND a.version=1
              AND a.target_home=s.home_branch_id))
      THEN RAISE EXCEPTION 'TRAINER_HOME_ORIGIN_INCONSISTENT'; END IF;
    END $$;
    CREATE TABLE workforce_trainer_home_origins (
      trainer_id uuid PRIMARY KEY, organization_id uuid NOT NULL,
      origin text NOT NULL CHECK(origin IN ('legacy_observation','registered')),
      home_branch_id uuid NOT NULL, trainer_version bigint NOT NULL CHECK(trainer_version>0),
      recorded_at timestamptz NOT NULL, registration_operation_id uuid,
      FOREIGN KEY(organization_id,trainer_id) REFERENCES workforce_trainers(organization_id,id),
      FOREIGN KEY(organization_id,home_branch_id) REFERENCES
        organization_branches(organization_id,id),
      FOREIGN KEY(organization_id,registration_operation_id,trainer_id) REFERENCES
        workforce_registration_operations(organization_id,operation_id,trainer_id),
      CHECK((origin='legacy_observation' AND registration_operation_id IS NULL) OR
        (origin='registered' AND registration_operation_id IS NOT NULL AND trainer_version=1)));
    CREATE TABLE workforce_trainer_home_operations (
      organization_id uuid NOT NULL,operation_id uuid NOT NULL,trainer_id uuid NOT NULL,
      actor_id uuid NOT NULL,canonical_version integer NOT NULL CHECK(canonical_version=1),
      fingerprint bytea NOT NULL CHECK(octet_length(fingerprint)=32),
      before_home_branch_id uuid NOT NULL,after_home_branch_id uuid NOT NULL,
      expected_trainer_version bigint NOT NULL,
      before_version bigint NOT NULL CHECK(before_version>0),after_version bigint NOT NULL,
      changed boolean NOT NULL,recorded_at timestamptz NOT NULL,
      PRIMARY KEY(organization_id,operation_id),
      UNIQUE(organization_id,operation_id,trainer_id,actor_id,before_home_branch_id,
        after_home_branch_id,before_version,after_version,changed,recorded_at),
      FOREIGN KEY(organization_id,trainer_id) REFERENCES workforce_trainers(organization_id,id),
      FOREIGN KEY(organization_id,actor_id) REFERENCES iam_accounts(organization_id,id),
      FOREIGN KEY(organization_id,before_home_branch_id) REFERENCES
        organization_branches(organization_id,id),
      FOREIGN KEY(organization_id,after_home_branch_id) REFERENCES
        organization_branches(organization_id,id),
      CHECK(expected_trainer_version=before_version),
      CHECK((changed AND before_home_branch_id<>after_home_branch_id
          AND after_version=before_version+1)
        OR (NOT changed AND before_home_branch_id=after_home_branch_id
          AND after_version=before_version)));
    CREATE TABLE workforce_trainer_home_transitions (
      organization_id uuid NOT NULL,operation_id uuid NOT NULL,trainer_id uuid NOT NULL,
      actor_id uuid NOT NULL,before_home_branch_id uuid NOT NULL,after_home_branch_id uuid NOT NULL,
      before_version bigint NOT NULL CHECK(before_version>0),after_version bigint NOT NULL,
      recorded_at timestamptz NOT NULL,changed boolean NOT NULL DEFAULT true CHECK(changed),
      PRIMARY KEY(organization_id,operation_id),UNIQUE(organization_id,trainer_id,after_version),
      UNIQUE(organization_id,operation_id,trainer_id,actor_id,before_home_branch_id,
        after_home_branch_id,before_version,after_version,recorded_at),
      FOREIGN KEY(organization_id,operation_id,trainer_id,actor_id,before_home_branch_id,
        after_home_branch_id,before_version,after_version,changed,recorded_at) REFERENCES
        workforce_trainer_home_operations(organization_id,operation_id,trainer_id,actor_id,
          before_home_branch_id,after_home_branch_id,before_version,after_version,changed,recorded_at),
      CHECK(before_home_branch_id<>after_home_branch_id
          AND after_version=before_version+1));
    CREATE TABLE audit_trainer_home_events (
      id uuid PRIMARY KEY,organization_id uuid NOT NULL,operation_id uuid NOT NULL,
      trainer_id uuid NOT NULL,actor_id uuid NOT NULL,
      actor_role text NOT NULL CHECK(actor_role='MASTER'),
      actor_branch uuid CHECK(actor_branch IS NULL),
      before_home_branch_id uuid NOT NULL,after_home_branch_id uuid NOT NULL,
      before_version bigint NOT NULL CHECK(before_version>0),after_version bigint NOT NULL,
      recorded_at timestamptz NOT NULL,UNIQUE(organization_id,operation_id),
      FOREIGN KEY(organization_id,operation_id,trainer_id,actor_id,before_home_branch_id,
        after_home_branch_id,before_version,after_version,recorded_at) REFERENCES
        workforce_trainer_home_transitions(organization_id,operation_id,trainer_id,actor_id,
          before_home_branch_id,after_home_branch_id,before_version,after_version,recorded_at),
      CHECK(before_home_branch_id<>after_home_branch_id
          AND after_version=before_version+1));
    INSERT INTO workforce_trainer_home_origins
      (trainer_id,organization_id,origin,home_branch_id,trainer_version,recorded_at)
      SELECT id,organization_id,'legacy_observation',home_branch_id,row_version,clock_timestamp()
      FROM workforce_trainers;
    """)


def downgrade() -> None:
    preflight(revision)
    op.execute("""
    LOCK TABLE workforce_trainer_home_origins,workforce_trainer_home_operations,
      workforce_trainer_home_transitions,audit_trainer_home_events IN ACCESS EXCLUSIVE MODE;
    DO $$ BEGIN
      IF EXISTS(SELECT FROM workforce_trainer_home_operations)
        OR EXISTS(SELECT FROM workforce_trainer_home_transitions)
        OR EXISTS(SELECT FROM audit_trainer_home_events)
        OR EXISTS(SELECT FROM workforce_trainer_home_origins o
          WHERE o.origin='registered' AND NOT EXISTS(
            SELECT FROM workforce_initial_snapshots s
            JOIN workforce_registration_operations r ON r.organization_id=s.organization_id
              AND r.trainer_id=s.trainer_id
            JOIN audit_workforce_initial_events a ON a.organization_id=r.organization_id
              AND a.operation_id=r.operation_id AND a.trainer_id=r.trainer_id
              AND a.event_kind='trainer_registered' AND a.actor_id=r.creator_account_id
            WHERE s.organization_id=o.organization_id AND s.trainer_id=o.trainer_id
              AND r.operation_id=o.registration_operation_id
              AND s.home_branch_id=o.home_branch_id AND a.target_home=o.home_branch_id
              AND s.created_at=o.recorded_at AND s.version=1 AND a.version=1
              AND o.trainer_version=1))
        OR EXISTS(SELECT FROM workforce_trainers t FULL JOIN workforce_trainer_home_origins o
          ON t.id=o.trainer_id WHERE t.id IS NULL OR o.trainer_id IS NULL
            OR t.organization_id<>o.organization_id OR t.home_branch_id<>o.home_branch_id)
      THEN RAISE EXCEPTION 'TRAINER_HOME_HISTORY_PRESENT'; END IF;
    END $$;
    DROP TABLE audit_trainer_home_events;
    DROP TABLE workforce_trainer_home_transitions;
    DROP TABLE workforce_trainer_home_operations;
    DROP TABLE workforce_trainer_home_origins;
    """)
