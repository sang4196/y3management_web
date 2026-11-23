"""Independent current compensation version and actor-bound audited commands."""

from sqlalchemy import text

from alembic import op

revision = "0020_workforce_compensation"
down_revision = "0019_workforce_trainer_home"
branch_labels = None
depends_on = None


def preflight(expected: str) -> None:
    op.execute("LOCK TABLE iam_installation IN ACCESS EXCLUSIVE MODE")
    op.execute("LOCK TABLE alembic_version,iam_policy_transitions IN ACCESS EXCLUSIVE MODE")
    bind = op.get_bind()
    if list(bind.execute(text("SELECT version_num FROM alembic_version")).scalars()) != [expected]:
        raise ValueError("COMPENSATION_SCHEMA_MISMATCH")
    if not bind.execute(
        text("""SELECT EXISTS(SELECT FROM iam_installation i
        JOIN iam_policy_transitions p ON p.id=i.policy_transition_id
        WHERE i.id=1 AND i.auth_policy_version=2 AND p.from_version=1 AND p.to_version=2
          AND p.target_schema_revision='0014_password_only')""")
    ).scalar_one():
        raise ValueError("COMPENSATION_POLICY_MISMATCH")
    op.execute("""LOCK TABLE workforce_trainers,workforce_initial_snapshots,
        workforce_registration_operations,audit_workforce_initial_events
        IN ACCESS EXCLUSIVE MODE""")


def originals() -> None:
    # Independent defaults mean registration operation and audit clocks need not be equal.
    op.execute("""DO $$ BEGIN
      IF EXISTS(SELECT FROM workforce_trainers t
        LEFT JOIN workforce_initial_snapshots s ON s.organization_id=t.organization_id
          AND s.trainer_id=t.id
        LEFT JOIN workforce_registration_operations r ON r.organization_id=t.organization_id
          AND r.trainer_id=t.id
        WHERE s.trainer_id IS NULL OR r.trainer_id IS NULL OR t.created_at<>s.created_at
          OR t.rate_percent<>s.rate_percent OR t.fixed_amount_won<>s.fixed_amount_won
          OR t.base_salary_won<>s.base_salary_won
          OR t.base_salary_start_month<>s.base_salary_start_month
          OR NOT EXISTS(SELECT FROM audit_workforce_initial_events a
            JOIN audit_workforce_initial_events registered
              ON registered.organization_id=a.organization_id
              AND registered.trainer_id=a.trainer_id AND registered.operation_id=a.operation_id
              AND registered.event_kind='trainer_registered'
            WHERE a.organization_id=t.organization_id AND a.trainer_id=t.id
              AND a.operation_id=r.operation_id AND a.actor_id=r.creator_account_id
              AND registered.actor_id=a.actor_id AND registered.actor_role=a.actor_role
              AND registered.actor_branch IS NOT DISTINCT FROM a.actor_branch
              AND registered.target_home=s.home_branch_id AND registered.version=1
              AND a.event_kind='initial_compensation' AND a.version=1
              AND a.target_home=s.home_branch_id
              AND a.before_rate IS NULL AND a.before_fixed IS NULL
              AND a.before_base IS NULL AND a.before_month IS NULL
              AND a.after_rate=s.rate_percent AND a.after_fixed=s.fixed_amount_won
              AND a.after_base=s.base_salary_won AND a.after_month=s.base_salary_start_month))
      THEN RAISE EXCEPTION 'COMPENSATION_ORIGINAL_INCONSISTENT'; END IF;
    END $$""")


def upgrade() -> None:
    preflight(down_revision)
    originals()
    op.execute("""
    ALTER TABLE workforce_trainers ADD COLUMN compensation_version bigint NOT NULL DEFAULT 1
      CHECK(compensation_version>0);
    CREATE TABLE workforce_compensation_operations (
      organization_id uuid NOT NULL,operation_id uuid NOT NULL,trainer_id uuid NOT NULL,
      actor_id uuid NOT NULL,actor_role text NOT NULL,actor_branch uuid,target_home uuid NOT NULL,
      canonical_version integer NOT NULL CHECK(canonical_version=1),
      fingerprint bytea NOT NULL CHECK(octet_length(fingerprint)=32),
      expected_trainer_version bigint NOT NULL CHECK(expected_trainer_version>0),
      expected_compensation_version bigint NOT NULL,
      before_rate integer NOT NULL CHECK(before_rate BETWEEN 0 AND 100),
      after_rate integer NOT NULL CHECK(after_rate BETWEEN 0 AND 100),
      before_fixed numeric NOT NULL,after_fixed numeric NOT NULL,
      before_version bigint NOT NULL CHECK(before_version>0),after_version bigint NOT NULL,
      changed boolean NOT NULL,recorded_at timestamptz NOT NULL,
      PRIMARY KEY(organization_id,operation_id),
      UNIQUE(organization_id,operation_id,trainer_id,actor_id,actor_role,target_home,
        before_rate,after_rate,before_fixed,after_fixed,before_version,after_version,changed,recorded_at),
      FOREIGN KEY(organization_id,trainer_id) REFERENCES workforce_trainers(organization_id,id),
      FOREIGN KEY(organization_id,actor_id) REFERENCES iam_accounts(organization_id,id),
      FOREIGN KEY(organization_id,target_home) REFERENCES organization_branches(organization_id,id),
      CHECK((actor_role='MASTER' AND actor_branch IS NULL) OR
        (actor_role='BRANCH_ADMIN' AND actor_branch IS NOT NULL AND actor_branch=target_home)),
      CHECK(before_fixed NOT IN ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)
        AND before_fixed>=0 AND before_fixed=trunc(before_fixed)),
      CHECK(after_fixed NOT IN ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)
        AND after_fixed>=0 AND after_fixed=trunc(after_fixed)),
      CHECK(expected_compensation_version=before_version),
      CHECK((changed AND (before_rate<>after_rate OR before_fixed<>after_fixed)
          AND after_version=before_version+1) OR
        (NOT changed AND before_rate=after_rate AND before_fixed=after_fixed
          AND after_version=before_version)));
    CREATE TABLE audit_compensation_events (
      id uuid PRIMARY KEY,organization_id uuid NOT NULL,operation_id uuid NOT NULL,
      trainer_id uuid NOT NULL,actor_id uuid NOT NULL,actor_role text NOT NULL,
      actor_branch uuid,target_home uuid NOT NULL,
      before_rate integer NOT NULL,after_rate integer NOT NULL,
      before_fixed numeric NOT NULL,after_fixed numeric NOT NULL,
      before_version bigint NOT NULL CHECK(before_version>0),after_version bigint NOT NULL,
      changed boolean NOT NULL DEFAULT true CHECK(changed),recorded_at timestamptz NOT NULL,
      UNIQUE(organization_id,operation_id),UNIQUE(organization_id,trainer_id,after_version),
      FOREIGN KEY(organization_id,operation_id,trainer_id,actor_id,actor_role,target_home,
        before_rate,after_rate,before_fixed,after_fixed,before_version,after_version,changed,
        recorded_at) REFERENCES workforce_compensation_operations(organization_id,operation_id,
        trainer_id,actor_id,actor_role,target_home,before_rate,after_rate,before_fixed,after_fixed,
        before_version,after_version,changed,recorded_at),
      CHECK((actor_role='MASTER' AND actor_branch IS NULL) OR
        (actor_role='BRANCH_ADMIN' AND actor_branch IS NOT NULL AND actor_branch=target_home)),
      CHECK((before_rate<>after_rate OR before_fixed<>after_fixed)
        AND after_version=before_version+1));
    """)


def downgrade() -> None:
    preflight(revision)
    op.execute("""LOCK TABLE workforce_compensation_operations,audit_compensation_events
        IN ACCESS EXCLUSIVE MODE""")
    if (
        op.get_bind()
        .execute(
            text("""SELECT EXISTS(SELECT FROM workforce_compensation_operations)
        OR EXISTS(SELECT FROM audit_compensation_events)
        OR EXISTS(SELECT FROM workforce_trainers WHERE compensation_version<>1)""")
        )
        .scalar_one()
    ):
        raise ValueError("COMPENSATION_HISTORY_PRESENT")
    originals()
    op.execute("DROP TABLE audit_compensation_events")
    op.execute("DROP TABLE workforce_compensation_operations")
    op.drop_column("workforce_trainers", "compensation_version")
