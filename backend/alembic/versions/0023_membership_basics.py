"""Limited Membership facts and kind-bound Actor receipts; original revisions stay intact."""

from sqlalchemy import text

from alembic import op

revision = "0023_membership_basics"
down_revision = "0022_pt_product_catalog"
branch_labels = None
depends_on = None


def preflight(expected: str) -> None:
    op.execute("LOCK TABLE iam_installation IN ACCESS EXCLUSIVE MODE")
    op.execute("LOCK TABLE alembic_version,iam_policy_transitions IN ACCESS EXCLUSIVE MODE")
    bind = op.get_bind()
    if list(bind.execute(text("SELECT version_num FROM alembic_version")).scalars()) != [expected]:
        raise ValueError("MEMBERSHIP_SCHEMA_MISMATCH")
    if not bind.execute(
        text("""SELECT EXISTS(SELECT FROM iam_installation i
      JOIN iam_policy_transitions p ON p.id=i.policy_transition_id
      WHERE i.id=1 AND i.auth_policy_version=2 AND p.from_version=1 AND p.to_version=2
      AND p.target_schema_revision='0014_password_only')""")
    ).scalar_one():
        raise ValueError("MEMBERSHIP_POLICY_MISMATCH")


def upgrade() -> None:
    preflight(down_revision)
    op.execute("""
    CREATE TABLE membership_members (
      id uuid PRIMARY KEY,organization_id uuid NOT NULL,
      current_version bigint NOT NULL CHECK(current_version>0),created_at timestamptz NOT NULL,
      UNIQUE(organization_id,id));
    CREATE TABLE membership_member_versions (
      organization_id uuid NOT NULL,member_id uuid NOT NULL,
      version bigint NOT NULL CHECK(version>0),
      name text NOT NULL CHECK(length(name) BETWEEN 1 AND 200 AND name=btrim(name)
        AND length(btrim(name))>0 AND name !~ '[[:cntrl:]]'),
      phone text NOT NULL CHECK(phone ~ '^010[2-9][0-9]{7}$'),
      home_branch_id uuid NOT NULL,active boolean NOT NULL,
      source_operation_id uuid NOT NULL,actor_id uuid NOT NULL,
      kind text NOT NULL CHECK(kind IN ('create','update','deactivate','reactivate')),
      before_version bigint,before_active boolean,before_home_branch_id uuid,
      recorded_at timestamptz NOT NULL,changed boolean NOT NULL CHECK(changed),
      PRIMARY KEY(organization_id,member_id,version),
      UNIQUE(organization_id,member_id,version,active,home_branch_id),
      UNIQUE(organization_id,member_id,version,home_branch_id),
      FOREIGN KEY(organization_id,member_id) REFERENCES membership_members(organization_id,id)
        DEFERRABLE INITIALLY DEFERRED,
      FOREIGN KEY(organization_id,home_branch_id) REFERENCES
      organization_branches(organization_id,id),
      FOREIGN KEY(organization_id,member_id,before_version,before_active,before_home_branch_id)
        REFERENCES membership_member_versions(organization_id,member_id,version,active,
      home_branch_id),
      CHECK((kind='create' AND before_version IS NULL AND before_active IS NULL
          AND before_home_branch_id IS NULL AND version=1 AND active)
        OR (kind IN ('update','deactivate','reactivate') AND before_version IS NOT NULL
          AND before_version>0 AND version=before_version+1 AND before_active IS NOT NULL
          AND before_home_branch_id IS NOT NULL AND home_branch_id=before_home_branch_id
          AND ((kind='update' AND active=before_active)
            OR (kind='deactivate' AND before_active AND NOT active)
            OR (kind='reactivate' AND NOT before_active AND active)))));
    ALTER TABLE membership_members ADD CONSTRAINT membership_current_fk
      FOREIGN KEY(organization_id,id,current_version) REFERENCES
      membership_member_versions(organization_id,member_id,version) DEFERRABLE INITIALLY DEFERRED;
    CREATE TABLE membership_member_operations (
      organization_id uuid NOT NULL,operation_id uuid NOT NULL,member_id uuid NOT NULL,
      actor_id uuid NOT NULL,actor_role text NOT NULL CHECK(actor_role IN ('MASTER',
      'BRANCH_ADMIN','OPERATOR')),
      actor_branch uuid,home_branch_id uuid NOT NULL,
      actor_branch_key uuid GENERATED ALWAYS AS
        (coalesce(actor_branch,'00000000-0000-0000-0000-000000000000'::uuid)) STORED NOT NULL,
      kind text NOT NULL CHECK(kind IN ('create','update','deactivate','reactivate')),
      before_version bigint,after_version bigint NOT NULL CHECK(after_version>0),
      changed boolean NOT NULL,recorded_at timestamptz NOT NULL,validated_at timestamptz,
      canonical_version integer NOT NULL CHECK(canonical_version=1),
      fingerprint bytea NOT NULL CHECK(octet_length(fingerprint)=32),
      PRIMARY KEY(organization_id,operation_id),
      UNIQUE(organization_id,operation_id,member_id,actor_id,kind,after_version,changed,
      recorded_at,home_branch_id),
      UNIQUE(organization_id,operation_id,member_id,actor_id,actor_role,actor_branch_key,
      kind,after_version,changed,recorded_at,home_branch_id),
      UNIQUE(organization_id,operation_id,before_version),
      FOREIGN KEY(organization_id,member_id,after_version,home_branch_id) REFERENCES
        membership_member_versions(organization_id,member_id,version,home_branch_id)
      DEFERRABLE INITIALLY DEFERRED,
      FOREIGN KEY(organization_id,member_id,before_version) REFERENCES
        membership_member_versions(organization_id,member_id,version),
      FOREIGN KEY(organization_id,actor_id) REFERENCES iam_accounts(organization_id,id),
      CHECK((actor_role='MASTER' AND actor_branch IS NULL)
        OR (actor_role IN ('BRANCH_ADMIN','OPERATOR') AND actor_branch IS NOT NULL AND
      actor_branch=home_branch_id)),
      CHECK(kind IN ('create','update') OR actor_role IN ('MASTER','BRANCH_ADMIN')),
      CHECK((kind='create' AND before_version IS NULL AND after_version=1 AND changed)
        OR (kind IN ('update','deactivate','reactivate') AND before_version IS NOT NULL
      AND before_version>0
          AND ((changed AND after_version=before_version+1) OR (NOT changed AND
      after_version=before_version)))));
    ALTER TABLE membership_member_versions ADD CONSTRAINT membership_source_core_fk FOREIGN KEY
      (organization_id,source_operation_id,member_id,actor_id,kind,version,changed,
      recorded_at,home_branch_id)
      REFERENCES membership_member_operations(organization_id,operation_id,member_id,actor_id,kind,
        after_version,changed,recorded_at,home_branch_id) DEFERRABLE INITIALLY DEFERRED;
    ALTER TABLE membership_member_versions ADD CONSTRAINT membership_source_before_fk FOREIGN KEY
      (organization_id,source_operation_id,before_version) REFERENCES
      membership_member_operations(organization_id,operation_id,before_version)
      DEFERRABLE INITIALLY DEFERRED;
    CREATE TABLE audit_member_events (
      id uuid PRIMARY KEY,organization_id uuid NOT NULL,operation_id uuid NOT NULL,
      member_id uuid NOT NULL,
      actor_id uuid NOT NULL,actor_role text NOT NULL,actor_branch uuid,home_branch_id
      uuid NOT NULL,
      actor_branch_key uuid GENERATED ALWAYS AS
        (coalesce(actor_branch,'00000000-0000-0000-0000-000000000000'::uuid)) STORED NOT NULL,
      kind text NOT NULL,before_version bigint,after_version bigint NOT NULL,
      changed boolean NOT NULL CHECK(changed),recorded_at timestamptz NOT NULL,
      UNIQUE(organization_id,operation_id),UNIQUE(organization_id,member_id,after_version),
      CONSTRAINT audit_member_core_fk FOREIGN KEY(organization_id,operation_id,member_id,actor_id,
        actor_role,actor_branch_key,kind,after_version,changed,recorded_at,home_branch_id)
        REFERENCES membership_member_operations(organization_id,operation_id,member_id,actor_id,
          actor_role,actor_branch_key,kind,after_version,changed,recorded_at,
      home_branch_id) DEFERRABLE INITIALLY DEFERRED,
      CONSTRAINT audit_member_before_fk FOREIGN KEY(organization_id,operation_id,before_version)
        REFERENCES membership_member_operations(organization_id,operation_id,
      before_version) DEFERRABLE INITIALLY DEFERRED,
      CHECK((actor_role='MASTER' AND actor_branch IS NULL)
        OR (actor_role IN ('BRANCH_ADMIN','OPERATOR') AND actor_branch IS NOT NULL AND
      actor_branch=home_branch_id)),
      CHECK((kind='create' AND before_version IS NULL AND after_version=1)
        OR (kind IN ('update','deactivate','reactivate') AND before_version IS NOT NULL
      AND before_version>0)));
    """)


def downgrade() -> None:
    preflight(revision)
    op.execute("""LOCK TABLE membership_members,membership_member_versions,
      membership_member_operations,audit_member_events IN ACCESS EXCLUSIVE MODE""")
    if (
        op.get_bind()
        .execute(
            text("""SELECT EXISTS(SELECT FROM membership_members)
      OR EXISTS(SELECT FROM membership_member_versions) OR EXISTS(SELECT FROM
      membership_member_operations)
      OR EXISTS(SELECT FROM audit_member_events)""")
        )
        .scalar_one()
    ):
        raise ValueError("MEMBERSHIP_HISTORY_PRESENT")
    op.execute("DROP TABLE audit_member_events")
    op.execute("ALTER TABLE membership_member_versions DROP CONSTRAINT membership_source_core_fk")
    op.execute("ALTER TABLE membership_member_versions DROP CONSTRAINT membership_source_before_fk")
    op.execute("DROP TABLE membership_member_operations")
    op.execute("ALTER TABLE membership_members DROP CONSTRAINT membership_current_fk")
    op.execute("DROP TABLE membership_member_versions")
    op.execute("DROP TABLE membership_members")
