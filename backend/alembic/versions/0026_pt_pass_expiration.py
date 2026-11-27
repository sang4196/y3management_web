"""Separate manual-expiration history; original issuance facts/balances remain untouched."""

from sqlalchemy import text

from alembic import op

revision = "0026_pt_pass_expiration"
down_revision = "0025_pt_pass_issuance"
branch_labels = None
depends_on = None


def preflight(expected: str) -> None:
    op.execute("LOCK TABLE iam_installation IN ACCESS EXCLUSIVE MODE")
    op.execute("LOCK TABLE alembic_version,iam_policy_transitions IN ACCESS EXCLUSIVE MODE")
    bind = op.get_bind()
    if list(bind.execute(text("SELECT version_num FROM alembic_version")).scalars()) != [expected]:
        raise ValueError("PASS_STATE_SCHEMA_MISMATCH")
    if not bind.execute(
        text("""SELECT EXISTS(SELECT FROM iam_installation i JOIN
      iam_policy_transitions p
      ON p.id=i.policy_transition_id WHERE i.id=1 AND i.auth_policy_version=2 AND p.from_version=1
      AND p.to_version=2 AND p.target_schema_revision='0014_password_only')""")
    ).scalar_one():
        raise ValueError("PASS_STATE_POLICY_MISMATCH")


def upgrade() -> None:
    preflight(down_revision)
    op.execute("""
    ALTER TABLE pt_passes ADD CONSTRAINT pass_state_origin_key UNIQUE(organization_id,id,issued_at);
    ALTER TABLE pt_passes ADD CONSTRAINT pass_state_issue_key
      UNIQUE(organization_id,id,issued_branch_id);
    CREATE TABLE pt_pass_state_versions(
      organization_id uuid NOT NULL,pass_id uuid NOT NULL,version bigint NOT NULL CHECK(version>0),
      manual_expired boolean NOT NULL,kind text NOT NULL CHECK(kind IN
        ('issued','expire','release')),
      source_operation_id uuid,before_version bigint,before_expired boolean,before_recorded_at
        timestamptz,
      recorded_at timestamptz NOT NULL,origin_issued_at timestamptz,
      changed boolean NOT NULL DEFAULT true CHECK(changed),
      PRIMARY KEY(organization_id,pass_id,version),
      UNIQUE(organization_id,pass_id,version,manual_expired,recorded_at),
      FOREIGN KEY(organization_id,pass_id) REFERENCES pt_passes(organization_id,id),
      FOREIGN KEY(organization_id,pass_id,origin_issued_at) REFERENCES
        pt_passes(organization_id,id,issued_at),
      FOREIGN KEY(organization_id,pass_id,before_version,before_expired,before_recorded_at)
        REFERENCES
          pt_pass_state_versions(organization_id,pass_id,version,manual_expired,recorded_at),
      CHECK((kind='issued' AND version=1 AND NOT manual_expired AND source_operation_id IS NULL
          AND before_version IS NULL AND before_expired IS NULL AND before_recorded_at IS NULL
          AND origin_issued_at IS NOT NULL AND recorded_at=origin_issued_at)
        OR (kind IN ('expire','release') AND source_operation_id IS NOT NULL AND before_version
          IS NOT NULL
          AND before_version>0 AND version=before_version+1 AND before_expired IS NOT NULL
          AND before_recorded_at IS NOT NULL AND recorded_at>=before_recorded_at AND
            origin_issued_at IS NULL
          AND ((kind='expire' AND NOT before_expired AND manual_expired)
            OR (kind='release' AND before_expired AND NOT manual_expired)))));
    CREATE TABLE pt_pass_state_heads(
      organization_id uuid NOT NULL,pass_id uuid NOT NULL,current_version bigint NOT NULL
        CHECK(current_version>0),
      PRIMARY KEY(organization_id,pass_id),
      FOREIGN KEY(organization_id,pass_id) REFERENCES pt_passes(organization_id,id),
      FOREIGN KEY(organization_id,pass_id,current_version) REFERENCES
        pt_pass_state_versions(organization_id,pass_id,version) DEFERRABLE INITIALLY DEFERRED);
    CREATE TABLE pt_pass_state_operations(
      organization_id uuid NOT NULL,operation_id uuid NOT NULL,pass_id uuid NOT NULL,
      issued_branch_id uuid NOT NULL,actor_id uuid NOT NULL,
      actor_role text NOT NULL CHECK(actor_role IN ('MASTER','BRANCH_ADMIN')),actor_branch uuid,
      actor_branch_key uuid GENERATED ALWAYS AS
        (coalesce(actor_branch,'00000000-0000-0000-0000-000000000000'::uuid)) STORED NOT NULL,
      kind text NOT NULL CHECK(kind IN ('expire','release')),
      reason text NOT NULL CHECK(length(reason) BETWEEN 1 AND 200 AND reason=btrim(reason)
        AND length(btrim(reason))>0 AND reason !~ '[[:cntrl:]]'),
      before_version bigint NOT NULL CHECK(before_version>0),after_version bigint NOT NULL
        CHECK(after_version>0),
      before_expired boolean NOT NULL,after_expired boolean NOT NULL,
      before_recorded_at timestamptz NOT NULL,after_recorded_at timestamptz NOT NULL,
      recorded_at timestamptz NOT NULL,validated_at timestamptz,changed boolean NOT NULL,
      fingerprint bytea NOT NULL CHECK(octet_length(fingerprint)=32),
      PRIMARY KEY(organization_id,operation_id),
UNIQUE(organization_id,operation_id,pass_id,kind,after_version,after_expired,recorded_at,changed),
      UNIQUE(organization_id,operation_id,before_version,before_expired,before_recorded_at),
UNIQUE(organization_id,operation_id,pass_id,issued_branch_id,actor_id,actor_role,actor_branch_key,
kind,reason,before_version,after_version,before_expired,after_expired,before_recorded_at,recorded_at,changed),
      FOREIGN KEY(organization_id,pass_id,issued_branch_id) REFERENCES
        pt_passes(organization_id,id,issued_branch_id),
      FOREIGN KEY(organization_id,actor_id) REFERENCES iam_accounts(organization_id,id),
      FOREIGN KEY(organization_id,pass_id,before_version,before_expired,before_recorded_at)
        REFERENCES
          pt_pass_state_versions(organization_id,pass_id,version,manual_expired,recorded_at),
      FOREIGN KEY(organization_id,pass_id,after_version,after_expired,after_recorded_at)
        REFERENCES
          pt_pass_state_versions(organization_id,pass_id,version,manual_expired,recorded_at)
        DEFERRABLE INITIALLY DEFERRED,
      CHECK((actor_role='MASTER' AND actor_branch IS NULL) OR
        (actor_role='BRANCH_ADMIN' AND actor_branch IS NOT NULL AND actor_branch=issued_branch_id)),
      CHECK((kind='expire' AND after_expired) OR (kind='release' AND NOT after_expired)),
      CHECK(recorded_at>=before_recorded_at),
      CHECK((changed AND before_expired<>after_expired AND after_version=before_version+1
          AND after_recorded_at=recorded_at)
        OR (NOT changed AND before_expired=after_expired AND after_version=before_version
          AND after_recorded_at=before_recorded_at)));
    ALTER TABLE pt_pass_state_versions ADD CONSTRAINT pass_state_source_core_fk
      FOREIGN
        KEY(organization_id,source_operation_id,pass_id,kind,version,manual_expired,recorded_at,changed)
      REFERENCES pt_pass_state_operations(organization_id,operation_id,pass_id,kind,after_version,
        after_expired,recorded_at,changed) DEFERRABLE INITIALLY DEFERRED;
    ALTER TABLE pt_pass_state_versions ADD CONSTRAINT pass_state_source_before_fk
      FOREIGN
        KEY(organization_id,source_operation_id,before_version,before_expired,before_recorded_at)
      REFERENCES
        pt_pass_state_operations(organization_id,operation_id,before_version,before_expired,before_recorded_at)
      DEFERRABLE INITIALLY DEFERRED;
    CREATE TABLE audit_pass_state_events(
      id uuid PRIMARY KEY,organization_id uuid NOT NULL,operation_id uuid NOT NULL,pass_id uuid
        NOT NULL,
      issued_branch_id uuid NOT NULL,actor_id uuid NOT NULL,actor_role text NOT
        NULL,actor_branch uuid,
      actor_branch_key uuid GENERATED ALWAYS AS
        (coalesce(actor_branch,'00000000-0000-0000-0000-000000000000'::uuid)) STORED NOT NULL,
      kind text NOT NULL,reason text NOT NULL,before_version bigint NOT NULL,after_version
        bigint NOT NULL,
      before_expired boolean NOT NULL,after_expired boolean NOT NULL,before_recorded_at
        timestamptz NOT NULL,
      recorded_at timestamptz NOT NULL,changed boolean NOT NULL DEFAULT true CHECK(changed),
      UNIQUE(organization_id,operation_id),UNIQUE(organization_id,pass_id,after_version),
      CHECK((actor_role='MASTER' AND actor_branch IS NULL) OR
        (actor_role='BRANCH_ADMIN' AND actor_branch IS NOT NULL AND actor_branch=issued_branch_id)),
      CONSTRAINT audit_pass_state_core_fk FOREIGN
        KEY(organization_id,operation_id,pass_id,issued_branch_id,
actor_id,actor_role,actor_branch_key,kind,reason,before_version,after_version,before_expired,
        after_expired,before_recorded_at,recorded_at,changed)
      REFERENCES
        pt_pass_state_operations(organization_id,operation_id,pass_id,issued_branch_id,actor_id,
actor_role,actor_branch_key,kind,reason,before_version,after_version,before_expired,after_expired,
        before_recorded_at,recorded_at,changed) DEFERRABLE INITIALLY DEFERRED);
    INSERT INTO
      pt_pass_state_versions(organization_id,pass_id,version,manual_expired,kind,recorded_at,origin_issued_at)
      SELECT organization_id,id,1,false,'issued',issued_at,issued_at FROM pt_passes;
    INSERT INTO pt_pass_state_heads(organization_id,pass_id,current_version)
      SELECT organization_id,id,1 FROM pt_passes;
    """)


def downgrade() -> None:
    preflight(revision)
    op.execute(
        "LOCK TABLE pt_pass_state_heads,pt_pass_state_versions,pt_pass_state_operations,"
        "audit_pass_state_events IN ACCESS EXCLUSIVE MODE"
    )
    if (
        op.get_bind()
        .execute(
            text("""SELECT EXISTS(SELECT FROM pt_pass_state_versions WHERE
      version<>1 OR manual_expired OR kind<>'issued')
      OR EXISTS(SELECT FROM pt_pass_state_operations) OR EXISTS(SELECT FROM
        audit_pass_state_events)""")
        )
        .scalar_one()
    ):
        raise ValueError("PASS_STATE_HISTORY_PRESENT")
    op.execute("DROP TABLE audit_pass_state_events")
    op.execute("DROP TABLE pt_pass_state_heads")
    op.execute("ALTER TABLE pt_pass_state_versions DROP CONSTRAINT pass_state_source_core_fk")
    op.execute("ALTER TABLE pt_pass_state_versions DROP CONSTRAINT pass_state_source_before_fk")
    op.execute("DROP TABLE pt_pass_state_operations")
    op.execute("DROP TABLE pt_pass_state_versions")
    op.execute("ALTER TABLE pt_passes DROP CONSTRAINT pass_state_origin_key")
    op.execute("ALTER TABLE pt_passes DROP CONSTRAINT pass_state_issue_key")
