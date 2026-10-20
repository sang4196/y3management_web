"""Atomic initial Trainer facts/settings and restricted typed audit."""

from alembic import op

revision = "0010_workforce_initial"
down_revision = "0009_iam_emergency_handoff"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    ALTER TABLE organization_branches ADD COLUMN active boolean NOT NULL DEFAULT true,
      ADD COLUMN row_version bigint NOT NULL DEFAULT 1 CHECK(row_version>0);
    CREATE TABLE workforce_trainers (
      id uuid PRIMARY KEY, organization_id uuid NOT NULL,
      home_branch_id uuid NOT NULL, name text NOT NULL CHECK(length(btrim(name)) BETWEEN 1 AND 200),
      phone text NOT NULL CHECK(length(btrim(phone)) BETWEEN 1 AND 128),
      active boolean NOT NULL, row_version bigint NOT NULL CHECK(row_version>0),
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      rate_percent integer NOT NULL CHECK(rate_percent BETWEEN 0 AND 100),
      fixed_amount_won numeric NOT NULL, base_salary_won numeric NOT NULL,
      base_salary_start_month date NOT NULL,
      UNIQUE(organization_id,id),
      FOREIGN KEY(organization_id,home_branch_id) REFERENCES
        organization_branches(organization_id,id),
      CHECK(fixed_amount_won NOT IN ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)
        AND fixed_amount_won>=0 AND fixed_amount_won=trunc(fixed_amount_won)),
      CHECK(base_salary_won NOT IN ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)
        AND base_salary_won>=0 AND base_salary_won=trunc(base_salary_won)),
      CHECK(base_salary_start_month BETWEEN DATE '0001-01-01' AND DATE '9999-12-01'
        AND extract(day from base_salary_start_month)=1));
    CREATE TABLE workforce_initial_snapshots (
      trainer_id uuid PRIMARY KEY, organization_id uuid NOT NULL, home_branch_id uuid NOT NULL,
      rate_percent integer NOT NULL CHECK(rate_percent BETWEEN 0 AND 100),
      fixed_amount_won numeric NOT NULL, base_salary_won numeric NOT NULL,
      base_salary_start_month date NOT NULL, version integer NOT NULL CHECK(version=1),
      created_at timestamptz NOT NULL,
      FOREIGN KEY(organization_id,trainer_id) REFERENCES workforce_trainers(organization_id,id),
      FOREIGN KEY(organization_id,home_branch_id) REFERENCES
        organization_branches(organization_id,id),
      CHECK(fixed_amount_won NOT IN ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)
        AND fixed_amount_won>=0 AND fixed_amount_won=trunc(fixed_amount_won)),
      CHECK(base_salary_won NOT IN ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)
        AND base_salary_won>=0 AND base_salary_won=trunc(base_salary_won)),
      CHECK(base_salary_start_month BETWEEN DATE '0001-01-01' AND DATE '9999-12-01'
        AND extract(day from base_salary_start_month)=1));
    CREATE TABLE workforce_registration_operations (
      organization_id uuid NOT NULL, operation_id uuid NOT NULL, trainer_id uuid NOT NULL UNIQUE,
      creator_account_id uuid NOT NULL, created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      canonical_version integer NOT NULL CHECK(canonical_version=1),
      fingerprint bytea NOT NULL CHECK(octet_length(fingerprint)=32),
      PRIMARY KEY(organization_id,operation_id),
      UNIQUE(organization_id,operation_id,trainer_id),
      FOREIGN KEY(organization_id,trainer_id) REFERENCES workforce_trainers(organization_id,id),
      FOREIGN KEY(organization_id,creator_account_id) REFERENCES iam_accounts(organization_id,id));
    CREATE TABLE audit_workforce_initial_events (
      id uuid PRIMARY KEY, organization_id uuid NOT NULL, operation_id uuid NOT NULL,
      trainer_id uuid NOT NULL, actor_id uuid NOT NULL, actor_role text NOT NULL,
      actor_branch uuid, target_home uuid NOT NULL, version integer NOT NULL CHECK(version=1),
      created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
      event_kind text NOT NULL CHECK(event_kind IN ('trainer_registered','initial_compensation')),
      before_rate integer, before_fixed numeric, before_base numeric, before_month date,
      after_rate integer, after_fixed numeric, after_base numeric, after_month date,
      UNIQUE(organization_id,operation_id,event_kind),
      FOREIGN KEY(organization_id,operation_id,trainer_id)
        REFERENCES workforce_registration_operations(organization_id,operation_id,trainer_id),
      FOREIGN KEY(organization_id,actor_id) REFERENCES iam_accounts(organization_id,id),
      FOREIGN KEY(organization_id,actor_branch) REFERENCES
        organization_branches(organization_id,id),
      FOREIGN KEY(organization_id,target_home) REFERENCES organization_branches(organization_id,id),
      CHECK((actor_role='MASTER' AND actor_branch IS NULL) OR
        (actor_role='BRANCH_ADMIN' AND actor_branch IS NOT NULL AND actor_branch=target_home)),
      CHECK(before_rate IS NULL AND before_fixed IS NULL AND before_base IS NULL AND
        before_month IS NULL),
      CHECK((event_kind='trainer_registered' AND after_rate IS NULL AND after_fixed IS NULL
        AND after_base IS NULL AND after_month IS NULL) OR
        (event_kind='initial_compensation' AND after_rate IS NOT NULL AND after_rate BETWEEN 0
        AND 100
        AND after_fixed IS NOT NULL AND after_fixed NOT IN
        ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)
        AND after_fixed>=0 AND after_fixed=trunc(after_fixed)
        AND after_base IS NOT NULL AND after_base NOT IN
        ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)
        AND after_base>=0 AND after_base=trunc(after_base)
        AND after_month IS NOT NULL AND after_month BETWEEN DATE '0001-01-01' AND DATE '9999-12-01'
        AND extract(day from after_month)=1)));
    """)


def downgrade() -> None:
    op.execute("""
    LOCK TABLE iam_installation, iam_accounts, iam_sessions, organization_branches,
      workforce_registration_operations, workforce_trainers, workforce_initial_snapshots,
      audit_workforce_initial_events IN ACCESS EXCLUSIVE MODE;
    DO $$ BEGIN
      IF EXISTS(SELECT 1 FROM workforce_trainers)
        OR EXISTS(SELECT 1 FROM workforce_initial_snapshots)
        OR EXISTS(SELECT 1 FROM workforce_registration_operations)
        OR EXISTS(SELECT 1 FROM audit_workforce_initial_events)
        OR EXISTS(SELECT 1 FROM organization_branches WHERE NOT active OR row_version<>1)
      THEN RAISE EXCEPTION 'workforce history or branch facts must be preserved'; END IF;
    END $$;
    DROP TABLE audit_workforce_initial_events;
    DROP TABLE workforce_registration_operations;
    DROP TABLE workforce_initial_snapshots;
    DROP TABLE workforce_trainers;
    ALTER TABLE organization_branches DROP COLUMN active, DROP COLUMN row_version;
    """)
