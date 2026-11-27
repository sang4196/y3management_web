"""Basic issuance only; original revisions and all historical rows stay intact."""

from sqlalchemy import text

from alembic import op

revision = "0025_pt_pass_issuance"
down_revision = "0024_membership_home_move"
branch_labels = None
depends_on = None


def preflight(expected: str) -> None:
    op.execute("LOCK TABLE iam_installation IN ACCESS EXCLUSIVE MODE")
    op.execute("LOCK TABLE alembic_version,iam_policy_transitions IN ACCESS EXCLUSIVE MODE")
    bind = op.get_bind()
    if list(bind.execute(text("SELECT version_num FROM alembic_version")).scalars()) != [expected]:
        raise ValueError("PASS_SCHEMA_MISMATCH")
    if not bind.execute(
        text("""SELECT EXISTS(SELECT FROM iam_installation i
      JOIN iam_policy_transitions p ON p.id=i.policy_transition_id
      WHERE i.id=1 AND i.auth_policy_version=2 AND p.from_version=1 AND p.to_version=2
      AND p.target_schema_revision='0014_password_only')""")
    ).scalar_one():
        raise ValueError("PASS_POLICY_MISMATCH")


def upgrade() -> None:
    preflight(down_revision)
    op.execute("""
    ALTER TABLE pt_product_versions ADD CONSTRAINT pt_issue_snapshot_key UNIQUE
      (organization_id,product_id,version,price_won,session_count,payment_type,is_service,selling);
    CREATE TABLE pt_passes(
      id uuid PRIMARY KEY,organization_id uuid NOT NULL,source_operation_id uuid NOT NULL,
      actor_id uuid NOT NULL,issued_branch_id uuid NOT NULL,branch_version bigint NOT NULL
        CHECK(branch_version>0),
      member_id uuid NOT NULL,member_version bigint NOT NULL CHECK(member_version>0),
      trainer_id uuid NOT NULL,trainer_version bigint NOT NULL CHECK(trainer_version>0),
      product_id uuid NOT NULL,product_version bigint NOT NULL CHECK(product_version>0),
      price_won numeric NOT NULL CHECK(price_won NOT IN
        ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric)
        AND price_won>=0 AND price_won=trunc(price_won) AND length(price_won::text)<=1024),
      purchased_sessions bigint NOT NULL CHECK(purchased_sessions>0),
      initial_remaining_sessions bigint NOT NULL
        CHECK(initial_remaining_sessions=purchased_sessions),
      payment_type text NOT NULL CHECK(payment_type IN ('RATE','FIXED_AMOUNT')),
      is_service boolean NOT NULL CHECK(NOT is_service OR payment_type='FIXED_AMOUNT'),
      product_selling boolean NOT NULL DEFAULT true CHECK(product_selling),issued_at timestamptz
        NOT NULL,
      UNIQUE(organization_id,id),
      UNIQUE(organization_id,id,source_operation_id,actor_id,member_id,member_version,trainer_id,
        trainer_version,issued_branch_id,branch_version,product_id,product_version,issued_at),
      FOREIGN KEY(organization_id,actor_id) REFERENCES iam_accounts(organization_id,id),
      FOREIGN KEY(organization_id,issued_branch_id) REFERENCES
        organization_branches(organization_id,id),
      FOREIGN KEY(organization_id,member_id,member_version) REFERENCES
        membership_member_versions(organization_id,member_id,version),
      FOREIGN KEY(organization_id,trainer_id) REFERENCES workforce_trainers(organization_id,id),
      FOREIGN KEY(organization_id,product_id,product_version,price_won,purchased_sessions,
        payment_type,is_service,product_selling) REFERENCES pt_product_versions
(organization_id,product_id,version,price_won,session_count,payment_type,is_service,selling));
    CREATE TABLE pt_pass_issue_operations(
      organization_id uuid NOT NULL,operation_id uuid NOT NULL,pass_id uuid NOT NULL,
      actor_id uuid NOT NULL,actor_role text NOT NULL CHECK(actor_role IN
        ('MASTER','BRANCH_ADMIN','OPERATOR')),
      actor_branch uuid,actor_branch_key uuid GENERATED ALWAYS AS
        (coalesce(actor_branch,'00000000-0000-0000-0000-000000000000'::uuid)) STORED NOT NULL,
      issued_branch_id uuid NOT NULL,expected_branch_version bigint NOT NULL
        CHECK(expected_branch_version>0),
      member_id uuid NOT NULL,expected_member_version bigint NOT NULL
        CHECK(expected_member_version>0),
      trainer_id uuid NOT NULL,expected_trainer_version bigint NOT NULL
        CHECK(expected_trainer_version>0),
      product_id uuid NOT NULL,expected_product_version bigint NOT NULL
        CHECK(expected_product_version>0),
      fingerprint bytea NOT NULL CHECK(octet_length(fingerprint)=32),
      recorded_at timestamptz NOT NULL,validated_at timestamptz,
      PRIMARY KEY(organization_id,operation_id),UNIQUE(organization_id,pass_id),
      UNIQUE(organization_id,operation_id,pass_id,actor_id,recorded_at),
      UNIQUE(organization_id,operation_id,pass_id,member_id,trainer_id,issued_branch_id,
        actor_id,actor_role,actor_branch_key,recorded_at),
      CHECK((actor_role='MASTER' AND actor_branch IS NULL) OR
        (actor_role IN ('BRANCH_ADMIN','OPERATOR') AND actor_branch IS NOT NULL AND
          actor_branch=issued_branch_id)),
      CONSTRAINT pass_issue_core_fk FOREIGN KEY(organization_id,pass_id,operation_id,actor_id,
        member_id,expected_member_version,trainer_id,expected_trainer_version,issued_branch_id,
        expected_branch_version,product_id,expected_product_version,recorded_at)
        REFERENCES
          pt_passes(organization_id,id,source_operation_id,actor_id,member_id,member_version,
trainer_id,trainer_version,issued_branch_id,branch_version,product_id,product_version,issued_at)
        DEFERRABLE INITIALLY DEFERRED);
    ALTER TABLE pt_passes ADD CONSTRAINT pass_source_core_fk
      FOREIGN KEY(organization_id,source_operation_id,id,actor_id,issued_at)
      REFERENCES pt_pass_issue_operations(organization_id,operation_id,pass_id,actor_id,recorded_at)
      DEFERRABLE INITIALLY DEFERRED;
    CREATE TABLE audit_pass_issue_events(
      id uuid PRIMARY KEY,organization_id uuid NOT NULL,operation_id uuid NOT NULL,pass_id uuid
        NOT NULL,
      member_id uuid NOT NULL,trainer_id uuid NOT NULL,issued_branch_id uuid NOT NULL,
      actor_id uuid NOT NULL,actor_role text NOT NULL,actor_branch uuid,
      actor_branch_key uuid GENERATED ALWAYS AS
        (coalesce(actor_branch,'00000000-0000-0000-0000-000000000000'::uuid)) STORED NOT NULL,
      recorded_at timestamptz NOT NULL,UNIQUE(organization_id,operation_id),
      CHECK((actor_role='MASTER' AND actor_branch IS NULL) OR
        (actor_role IN ('BRANCH_ADMIN','OPERATOR') AND actor_branch IS NOT NULL
          AND actor_branch=issued_branch_id)),
      CONSTRAINT audit_pass_core_fk FOREIGN KEY(organization_id,operation_id,pass_id,member_id,
        trainer_id,issued_branch_id,actor_id,actor_role,actor_branch_key,recorded_at)
        REFERENCES pt_pass_issue_operations(organization_id,operation_id,pass_id,member_id,
          trainer_id,issued_branch_id,actor_id,actor_role,actor_branch_key,recorded_at)
        DEFERRABLE INITIALLY DEFERRED);
    """)


def downgrade() -> None:
    preflight(revision)
    op.execute(
        "LOCK TABLE pt_passes,pt_pass_issue_operations,audit_pass_issue_events "
        "IN ACCESS EXCLUSIVE MODE"
    )
    if (
        op.get_bind()
        .execute(
            text("""SELECT EXISTS(SELECT FROM pt_passes) OR
      EXISTS(SELECT FROM pt_pass_issue_operations) OR EXISTS(SELECT FROM
        audit_pass_issue_events)""")
        )
        .scalar_one()
    ):
        raise ValueError("PASS_ISSUANCE_HISTORY_PRESENT")
    op.execute("DROP TABLE audit_pass_issue_events")
    op.execute("ALTER TABLE pt_passes DROP CONSTRAINT pass_source_core_fk")
    op.execute("DROP TABLE pt_pass_issue_operations")
    op.execute("DROP TABLE pt_passes")
    op.execute("ALTER TABLE pt_product_versions DROP CONSTRAINT pt_issue_snapshot_key")
