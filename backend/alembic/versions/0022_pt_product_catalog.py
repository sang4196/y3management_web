"""Organization Catalog immutable versions and Actor-bound operation receipts."""

from sqlalchemy import text

from alembic import op

revision = "0022_pt_product_catalog"
down_revision = "0021_workforce_base_schedule"
branch_labels = None
depends_on = None


def preflight(expected: str) -> None:
    op.execute("LOCK TABLE iam_installation IN ACCESS EXCLUSIVE MODE")
    op.execute("LOCK TABLE alembic_version,iam_policy_transitions IN ACCESS EXCLUSIVE MODE")
    b = op.get_bind()
    if list(b.execute(text("SELECT version_num FROM alembic_version")).scalars()) != [expected]:
        raise ValueError("CATALOG_SCHEMA_MISMATCH")
    if not b.execute(
        text("""SELECT EXISTS(SELECT FROM iam_installation i
      JOIN iam_policy_transitions p ON p.id=i.policy_transition_id
      WHERE i.id=1 AND i.auth_policy_version=2 AND p.from_version=1 AND p.to_version=2
      AND p.target_schema_revision='0014_password_only')""")
    ).scalar_one():
        raise ValueError("CATALOG_POLICY_MISMATCH")


def upgrade() -> None:
    preflight(down_revision)
    op.execute("""
    CREATE TABLE pt_products (
      id uuid PRIMARY KEY,organization_id uuid NOT NULL,
      current_version bigint NOT NULL CHECK(current_version>0),created_at timestamptz NOT NULL,
      UNIQUE(organization_id,id));
    CREATE TABLE pt_product_versions (
      organization_id uuid NOT NULL,
      product_id uuid NOT NULL,
      version bigint NOT NULL CHECK(version>0),
      name text NOT NULL CHECK(length(name) BETWEEN 1 AND 200 AND length(btrim(name))>0
        AND name=btrim(name) AND name !~ '[[:cntrl:]]'),
      price_won numeric NOT NULL CHECK(price_won NOT IN
        ('NaN'::numeric,'Infinity'::numeric,'-Infinity'::numeric) AND price_won>=0
        AND price_won=trunc(price_won) AND length(price_won::text)<=1024),
      session_count bigint NOT NULL CHECK(session_count>0),
      payment_type text NOT NULL CHECK(payment_type IN ('RATE','FIXED_AMOUNT')),
      is_service boolean NOT NULL,selling boolean NOT NULL,
      source_operation_id uuid NOT NULL,actor_id uuid NOT NULL,
      kind text NOT NULL CHECK(kind IN ('create','update','stop')),
      before_version bigint,before_selling boolean,recorded_at timestamptz NOT NULL,
      changed boolean NOT NULL CHECK(changed),
      PRIMARY KEY(organization_id,product_id,version),
      UNIQUE(organization_id,product_id,version,selling),
      FOREIGN KEY(organization_id,product_id) REFERENCES pt_products(organization_id,id)
        DEFERRABLE INITIALLY DEFERRED,
      FOREIGN KEY(organization_id,product_id,before_version,before_selling) REFERENCES
        pt_product_versions(organization_id,product_id,version,selling),
      CHECK(NOT is_service OR payment_type='FIXED_AMOUNT'),
      CHECK((kind='create'
        AND before_version IS NULL
        AND before_selling IS NULL
        AND version=1
        AND selling)
        OR (kind IN ('update','stop') AND before_version IS NOT NULL AND before_version>0
          AND before_selling IS NOT NULL AND version=before_version+1
          AND ((kind='update' AND selling=before_selling)
            OR (kind='stop' AND before_selling AND NOT selling)))));
    ALTER TABLE pt_products ADD CONSTRAINT pt_products_current_fk
      FOREIGN KEY(organization_id,id,current_version) REFERENCES
      pt_product_versions(organization_id,product_id,version) DEFERRABLE INITIALLY DEFERRED;
    CREATE TABLE pt_product_operations (
      organization_id uuid NOT NULL,operation_id uuid NOT NULL,product_id uuid NOT NULL,
      actor_id uuid NOT NULL,actor_role text NOT NULL CHECK(actor_role='MASTER'),
      actor_branch uuid CHECK(actor_branch IS NULL),
      kind text NOT NULL CHECK(kind IN ('create','update','stop')),
      before_version bigint,after_version bigint NOT NULL CHECK(after_version>0),
      changed boolean NOT NULL,recorded_at timestamptz NOT NULL,validated_at timestamptz,
      canonical_version integer NOT NULL CHECK(canonical_version=1),
      fingerprint bytea NOT NULL CHECK(octet_length(fingerprint)=32),
      PRIMARY KEY(organization_id,operation_id),
      UNIQUE(organization_id,operation_id,product_id,actor_id,actor_role,kind,after_version,changed,recorded_at),
      UNIQUE(organization_id,operation_id,product_id,actor_id,kind,after_version,changed,recorded_at),
      UNIQUE(organization_id,operation_id,before_version),
      FOREIGN KEY(organization_id,product_id,after_version) REFERENCES
        pt_product_versions(organization_id,product_id,version) DEFERRABLE INITIALLY DEFERRED,
      FOREIGN KEY(organization_id,product_id,before_version) REFERENCES
        pt_product_versions(organization_id,product_id,version),
      FOREIGN KEY(organization_id,actor_id) REFERENCES iam_accounts(organization_id,id),
      CHECK((kind='create' AND before_version IS NULL AND after_version=1 AND changed)
        OR (kind IN ('update','stop') AND before_version IS NOT NULL AND before_version>0

        AND ((changed
        AND after_version=before_version+1)
        OR (NOT changed
        AND after_version=before_version)))));
    ALTER TABLE pt_product_versions ADD CONSTRAINT pt_versions_source_core_fk FOREIGN KEY
      (organization_id,source_operation_id,product_id,actor_id,kind,version,changed,recorded_at)
      REFERENCES pt_product_operations(organization_id,operation_id,product_id,actor_id,kind,
        after_version,changed,recorded_at) DEFERRABLE INITIALLY DEFERRED;
    ALTER TABLE pt_product_versions ADD CONSTRAINT pt_versions_source_before_fk FOREIGN KEY
      (organization_id,source_operation_id,before_version) REFERENCES
      pt_product_operations(organization_id,operation_id,before_version)
        DEFERRABLE INITIALLY DEFERRED;
    CREATE TABLE audit_product_events (
      id uuid PRIMARY KEY,organization_id uuid NOT NULL,operation_id uuid NOT NULL,
      product_id uuid NOT NULL,
      actor_id uuid NOT NULL,actor_role text NOT NULL CHECK(actor_role='MASTER'),
      actor_branch uuid CHECK(actor_branch IS NULL),
      kind text NOT NULL CHECK(kind IN ('create','update','stop')),
      before_version bigint,after_version bigint NOT NULL,changed boolean NOT NULL CHECK(changed),
      recorded_at timestamptz NOT NULL,UNIQUE(organization_id,operation_id),
      UNIQUE(organization_id,product_id,after_version),
      CONSTRAINT audit_product_core_fk FOREIGN KEY(organization_id,operation_id,product_id,actor_id,
        actor_role,kind,after_version,changed,recorded_at) REFERENCES pt_product_operations
        (organization_id,operation_id,product_id,actor_id,actor_role,kind,after_version,changed,recorded_at)
        DEFERRABLE INITIALLY DEFERRED,
      CONSTRAINT audit_product_before_fk FOREIGN KEY(organization_id,operation_id,before_version)
        REFERENCES pt_product_operations(organization_id,operation_id,before_version)
        DEFERRABLE INITIALLY DEFERRED,
      CHECK((kind='create' AND before_version IS NULL AND after_version=1)
        OR (kind IN ('update','stop') AND before_version IS NOT NULL AND before_version>0
          )));
    """)


def downgrade() -> None:
    preflight(revision)
    op.execute("""LOCK TABLE pt_products,pt_product_versions,pt_product_operations,
      audit_product_events IN ACCESS EXCLUSIVE MODE""")
    if (
        op.get_bind()
        .execute(
            text("""SELECT EXISTS(SELECT FROM pt_products)
      OR EXISTS(SELECT FROM pt_product_versions) OR EXISTS(SELECT FROM pt_product_operations)
      OR EXISTS(SELECT FROM audit_product_events)""")
        )
        .scalar_one()
    ):
        raise ValueError("CATALOG_HISTORY_PRESENT")
    op.execute("DROP TABLE audit_product_events")
    op.execute("ALTER TABLE pt_product_versions DROP CONSTRAINT pt_versions_source_core_fk")
    op.execute("ALTER TABLE pt_product_versions DROP CONSTRAINT pt_versions_source_before_fk")
    op.execute("DROP TABLE pt_product_operations")
    op.execute("ALTER TABLE pt_products DROP CONSTRAINT pt_products_current_fk")
    op.execute("DROP TABLE pt_product_versions")
    op.execute("DROP TABLE pt_products")
