"""Independent Base ledger and immutable actor-bound future plan receipts."""

from sqlalchemy import text

from alembic import op

revision = "0021_workforce_base_schedule"
down_revision = "0020_workforce_compensation"
branch_labels = None
depends_on = None


def preflight(expected: str) -> None:
    op.execute("LOCK TABLE iam_installation IN ACCESS EXCLUSIVE MODE")
    op.execute("LOCK TABLE alembic_version,iam_policy_transitions IN ACCESS EXCLUSIVE MODE")
    bind = op.get_bind()
    if list(bind.execute(text("SELECT version_num FROM alembic_version")).scalars()) != [expected]:
        raise ValueError("BASE_SCHEDULE_SCHEMA_MISMATCH")
    if not bind.execute(
        text("""SELECT EXISTS(SELECT FROM iam_installation i
        JOIN iam_policy_transitions p ON p.id=i.policy_transition_id
        WHERE i.id=1 AND i.auth_policy_version=2 AND p.from_version=1 AND p.to_version=2
          AND p.target_schema_revision='0014_password_only')""")
    ).scalar_one():
        raise ValueError("BASE_SCHEDULE_POLICY_MISMATCH")
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
      THEN RAISE EXCEPTION 'BASE_SCHEDULE_ORIGINAL_INCONSISTENT'; END IF;
    END $$""")


def upgrade() -> None:
    preflight(down_revision)
    originals()
    op.execute("""
    CREATE TABLE workforce_base_ledgers (
      trainer_id uuid PRIMARY KEY,organization_id uuid NOT NULL,
      ledger_version bigint NOT NULL DEFAULT 1 CHECK(ledger_version>0),
      registration_operation_id uuid NOT NULL,UNIQUE(organization_id,trainer_id),
      FOREIGN KEY(trainer_id) REFERENCES workforce_initial_snapshots(trainer_id),
      FOREIGN KEY(organization_id,trainer_id) REFERENCES workforce_trainers(organization_id,id),
      FOREIGN KEY(organization_id,registration_operation_id,trainer_id) REFERENCES
        workforce_registration_operations(organization_id,operation_id,trainer_id));
    CREATE TABLE workforce_base_changes (
      id uuid PRIMARY KEY,organization_id uuid NOT NULL,trainer_id uuid NOT NULL,
      start_month date NOT NULL CHECK(start_month BETWEEN DATE '0001-01-01' AND DATE '9999-12-01'
        AND extract(day from start_month)=1),
      planned_amount numeric NOT NULL,revision bigint NOT NULL CHECK(revision>0),
      active boolean NOT NULL,CHECK(id<>trainer_id),UNIQUE(organization_id,trainer_id,id),
      UNIQUE(organization_id,trainer_id,id,start_month),
      FOREIGN KEY(organization_id,trainer_id) REFERENCES
        workforce_base_ledgers(organization_id,trainer_id),
      CHECK(planned_amount NOT IN ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)
        AND planned_amount>=0 AND planned_amount=trunc(planned_amount)));
    CREATE UNIQUE INDEX workforce_base_active_month ON workforce_base_changes
      (organization_id,trainer_id,start_month) WHERE active;
    CREATE TABLE workforce_base_operations (
      organization_id uuid NOT NULL,operation_id uuid NOT NULL,trainer_id uuid NOT NULL,
      actor_id uuid NOT NULL,actor_role text NOT NULL,actor_branch uuid,target_home uuid NOT NULL,
      kind text NOT NULL CHECK(kind IN ('create','edit','cancel')),change_id uuid NOT NULL,
      start_month date NOT NULL CHECK(start_month BETWEEN DATE '0001-01-01' AND DATE '9999-12-01'
        AND extract(day from start_month)=1),
      before_amount numeric,after_amount numeric NOT NULL,
      before_active boolean,after_active boolean NOT NULL,
      before_revision bigint,after_revision bigint NOT NULL CHECK(after_revision>0),
      before_ledger_version bigint NOT NULL CHECK(before_ledger_version>0),
      after_ledger_version bigint NOT NULL CHECK(after_ledger_version>0),
      changed boolean NOT NULL,recorded_at timestamptz NOT NULL,
      canonical_version integer NOT NULL CHECK(canonical_version=1),
      fingerprint bytea NOT NULL CHECK(octet_length(fingerprint)=32),
      expected_trainer_version bigint NOT NULL CHECK(expected_trainer_version>0),
      validated_at timestamptz NOT NULL,business_month date NOT NULL,
      PRIMARY KEY(organization_id,operation_id),
      UNIQUE(organization_id,operation_id,trainer_id,actor_id,actor_role,target_home,kind,
        change_id,start_month,after_amount,after_active,after_revision,before_ledger_version,
        after_ledger_version,changed,recorded_at),
      UNIQUE(organization_id,operation_id,before_amount,before_active,before_revision),
      FOREIGN KEY(organization_id,trainer_id,change_id,start_month) REFERENCES
        workforce_base_changes(organization_id,trainer_id,id,start_month),
      FOREIGN KEY(organization_id,actor_id) REFERENCES iam_accounts(organization_id,id),
      FOREIGN KEY(organization_id,target_home) REFERENCES organization_branches(organization_id,id),
      CHECK(business_month=date_trunc('month',validated_at AT TIME ZONE 'Asia/Seoul')::date
        AND start_month>business_month),
      CHECK((actor_role='MASTER' AND actor_branch IS NULL) OR
        (actor_role='BRANCH_ADMIN' AND actor_branch IS NOT NULL AND actor_branch=target_home)),
      CHECK(after_amount NOT IN ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)
        AND after_amount>=0 AND after_amount=trunc(after_amount)),
      CHECK(before_amount IS NULL OR (before_amount NOT IN
        ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)
        AND before_amount>=0 AND before_amount=trunc(before_amount))),
      CHECK((kind='create' AND before_amount IS NULL AND before_active IS NULL
          AND before_revision IS NULL AND after_active AND after_revision=1 AND changed
          AND after_ledger_version=before_ledger_version+1) OR
        (kind='edit' AND before_amount IS NOT NULL AND before_active IS NOT NULL AND before_active
          AND before_revision IS NOT NULL AND before_revision>0 AND after_active AND
          ((changed AND before_amount<>after_amount AND after_revision=before_revision+1
             AND after_ledger_version=before_ledger_version+1) OR
           (NOT changed AND before_amount=after_amount AND after_revision=before_revision
             AND after_ledger_version=before_ledger_version))) OR
        (kind='cancel' AND before_amount IS NOT NULL AND before_amount=after_amount
          AND before_active IS NOT NULL AND before_active AND NOT after_active
          AND before_revision IS NOT NULL AND before_revision>0
          AND after_revision=before_revision+1 AND changed
          AND after_ledger_version=before_ledger_version+1)));
    CREATE TABLE audit_base_schedule_events (
      id uuid PRIMARY KEY,organization_id uuid NOT NULL,
      operation_id uuid NOT NULL,trainer_id uuid NOT NULL,
      actor_id uuid NOT NULL,actor_role text NOT NULL,actor_branch uuid,target_home uuid NOT NULL,
      kind text NOT NULL CHECK(kind IN ('create','edit','cancel')),change_id uuid NOT NULL,
      start_month date NOT NULL CHECK(start_month BETWEEN DATE '0001-01-01' AND DATE '9999-12-01'
        AND extract(day from start_month)=1),
      before_amount numeric,after_amount numeric NOT NULL,
      before_active boolean,after_active boolean NOT NULL,
      before_revision bigint,after_revision bigint NOT NULL CHECK(after_revision>0),
      before_ledger_version bigint NOT NULL CHECK(before_ledger_version>0),
      after_ledger_version bigint NOT NULL CHECK(after_ledger_version>0),
      changed boolean NOT NULL,recorded_at timestamptz NOT NULL,
      CHECK(changed),UNIQUE(organization_id,operation_id),
      UNIQUE(organization_id,trainer_id,after_ledger_version),
      FOREIGN KEY(organization_id,operation_id,trainer_id,actor_id,actor_role,target_home,kind,
        change_id,start_month,after_amount,after_active,after_revision,before_ledger_version,
        after_ledger_version,changed,recorded_at) REFERENCES workforce_base_operations(
        organization_id,operation_id,trainer_id,actor_id,actor_role,target_home,kind,
        change_id,start_month,after_amount,after_active,after_revision,before_ledger_version,
        after_ledger_version,changed,recorded_at)
        DEFERRABLE INITIALLY DEFERRED,
      FOREIGN KEY(organization_id,operation_id,before_amount,before_active,before_revision)
        REFERENCES workforce_base_operations
          (organization_id,operation_id,before_amount,before_active,before_revision)
        DEFERRABLE INITIALLY DEFERRED,
      CHECK((actor_role='MASTER' AND actor_branch IS NULL) OR
        (actor_role='BRANCH_ADMIN' AND actor_branch IS NOT NULL AND actor_branch=target_home)),
      CHECK(after_amount NOT IN ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)
        AND after_amount>=0 AND after_amount=trunc(after_amount)),
      CHECK(before_amount IS NULL OR (before_amount NOT IN
        ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)
        AND before_amount>=0 AND before_amount=trunc(before_amount))),
      CHECK((kind='create' AND before_amount IS NULL AND before_active IS NULL
          AND before_revision IS NULL AND after_active AND after_revision=1 AND changed
          AND after_ledger_version=before_ledger_version+1) OR
        (kind='edit' AND before_amount IS NOT NULL AND before_active IS NOT NULL AND before_active
          AND before_revision IS NOT NULL AND before_revision>0 AND after_active AND
          ((changed AND before_amount<>after_amount AND after_revision=before_revision+1
             AND after_ledger_version=before_ledger_version+1) OR
           (NOT changed AND before_amount=after_amount AND after_revision=before_revision
             AND after_ledger_version=before_ledger_version))) OR
        (kind='cancel' AND before_amount IS NOT NULL AND before_amount=after_amount
          AND before_active IS NOT NULL AND before_active AND NOT after_active
          AND before_revision IS NOT NULL AND before_revision>0
          AND after_revision=before_revision+1 AND changed
          AND after_ledger_version=before_ledger_version+1)));
    INSERT INTO workforce_base_ledgers(organization_id,trainer_id,registration_operation_id)
      SELECT organization_id,trainer_id,operation_id FROM workforce_registration_operations;
    """)


def downgrade() -> None:
    preflight(revision)
    op.execute("""LOCK TABLE workforce_base_ledgers,workforce_base_changes,
        workforce_base_operations,audit_base_schedule_events IN ACCESS EXCLUSIVE MODE""")
    if (
        op.get_bind()
        .execute(
            text("""SELECT EXISTS(SELECT FROM workforce_base_operations)
        OR EXISTS(SELECT FROM audit_base_schedule_events)
        OR EXISTS(SELECT FROM workforce_base_changes)
        OR EXISTS(SELECT FROM workforce_trainers t FULL JOIN workforce_base_ledgers l
          ON t.id=l.trainer_id WHERE t.id IS NULL OR l.trainer_id IS NULL
            OR t.organization_id<>l.organization_id OR l.ledger_version<>1
            OR NOT EXISTS(SELECT FROM workforce_registration_operations r
              WHERE r.organization_id=l.organization_id AND r.trainer_id=l.trainer_id
                AND r.operation_id=l.registration_operation_id))""")
        )
        .scalar_one()
    ):
        raise ValueError("BASE_SCHEDULE_HISTORY_PRESENT")
    originals()
    op.execute("DROP TABLE audit_base_schedule_events")
    op.execute("DROP TABLE workforce_base_operations")
    op.execute("DROP TABLE workforce_base_changes")
    op.execute("DROP TABLE workforce_base_ledgers")
