"""Operator role transitions, immutable receipts and movable work scope."""

from sqlalchemy import text

from alembic import op

revision = "0017_operator_management"
down_revision = "0016_operator_onboarding"
branch_labels = None
depends_on = None

OLD_ACTOR = """((kind IN ('issue','reissue') AND actor_id IS NOT NULL AND
 ((actor_role='MASTER' AND actor_branch IS NULL) OR
 (actor_role='BRANCH_ADMIN' AND actor_branch=branch_id AND actor_branch IS NOT NULL)))
 OR (kind='setup_complete' AND actor_role='CREDENTIAL_HOLDER' AND actor_id IS NULL
 AND actor_branch IS NULL)
 OR (kind IN ('login','logout','password_change') AND actor_role='OPERATOR'
 AND actor_id=account_id AND actor_id IS NOT NULL AND actor_branch=branch_id
 AND actor_branch IS NOT NULL))"""
NEW_ACTOR = """((kind IN ('issue','reissue') AND actor_id IS NOT NULL AND
 ((actor_role='MASTER' AND actor_branch IS NULL) OR
 (actor_role='BRANCH_ADMIN' AND actor_branch=branch_id AND actor_branch IS NOT NULL)))
 OR (kind='setup_complete' AND actor_role='CREDENTIAL_HOLDER' AND actor_id IS NULL
 AND actor_branch IS NULL)
 OR (kind IN ('login','logout','password_change') AND actor_id=account_id
 AND actor_id IS NOT NULL AND ((actor_role='MASTER' AND actor_branch IS NULL)
 OR (actor_role='BRANCH_ADMIN' AND actor_branch IS NOT NULL)
 OR (actor_role='OPERATOR' AND actor_branch=branch_id AND actor_branch IS NOT NULL))))"""


def preflight(expected: str) -> None:
    op.execute("LOCK TABLE iam_installation IN ACCESS EXCLUSIVE MODE")
    op.execute("LOCK TABLE alembic_version, iam_policy_transitions IN ACCESS EXCLUSIVE MODE")
    bind = op.get_bind()
    if list(bind.execute(text("SELECT version_num FROM alembic_version")).scalars()) != [expected]:
        raise ValueError("OPERATOR_MANAGEMENT_SCHEMA_MISMATCH")
    if not bind.execute(
        text("""SELECT EXISTS(SELECT FROM iam_installation i
        JOIN iam_policy_transitions p ON p.id=i.policy_transition_id
        WHERE i.id=1 AND i.auth_policy_version=2 AND p.from_version=1 AND p.to_version=2
        AND p.target_schema_revision='0014_password_only')""")
    ).scalar_one():
        raise ValueError("OPERATOR_MANAGEMENT_POLICY_MISMATCH")


def upgrade() -> None:
    preflight(down_revision)
    source_fk = (
        op.get_bind()
        .execute(
            text("""SELECT conname FROM pg_constraint
        WHERE conrelid='iam_operator_setup_credentials'::regclass
        AND confrelid='iam_operator_grants'::regclass AND contype='f'""")
        )
        .scalar_one()
    )
    op.drop_constraint(source_fk, "iam_operator_setup_credentials", type_="foreignkey")
    op.execute("""ALTER TABLE iam_operator_grants ADD CONSTRAINT iam_operator_stable_identity
        UNIQUE(organization_id,account_id);
        ALTER TABLE iam_operator_setup_credentials ADD CONSTRAINT iam_operator_source_identity
          FOREIGN KEY(organization_id,account_id)
          REFERENCES iam_operator_grants(organization_id,account_id);
        ALTER TABLE iam_operator_setup_credentials ADD CONSTRAINT iam_operator_source_branch
          FOREIGN KEY(organization_id,branch_id)
          REFERENCES organization_branches(organization_id,id);
        ALTER TABLE audit_operator_account_events 
          DROP CONSTRAINT audit_operator_account_events_check;
    """)
    op.execute(
        "ALTER TABLE audit_operator_account_events ADD CONSTRAINT audit_operator_actor "
        f"CHECK {NEW_ACTOR}"
    )
    op.execute("""CREATE TABLE iam_operator_role_operations (
        organization_id uuid NOT NULL, operation_id uuid NOT NULL,
        account_id uuid NOT NULL, actor_id uuid NOT NULL,
        fingerprint bytea NOT NULL CHECK(octet_length(fingerprint)=32),
        action text NOT NULL CHECK(action IN ('role','move')),
        changed boolean NOT NULL, granted boolean NOT NULL,
        branch_id uuid NOT NULL, committed_version bigint NOT NULL CHECK(committed_version>0),
        created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
        PRIMARY KEY(organization_id,operation_id),
        UNIQUE(organization_id,operation_id,account_id,actor_id),
        FOREIGN KEY(organization_id,account_id) REFERENCES iam_accounts(organization_id,id),
        FOREIGN KEY(organization_id,actor_id) REFERENCES iam_accounts(organization_id,id),
        FOREIGN KEY(organization_id,branch_id) REFERENCES organization_branches(organization_id,id)
    );
    CREATE TABLE audit_operator_role_events (
        organization_id uuid NOT NULL, operation_id uuid NOT NULL,
        account_id uuid NOT NULL, actor_id uuid NOT NULL,
        actor_role text NOT NULL, actor_branch uuid,
        kind text NOT NULL CHECK(kind IN ('add','revoke','regrant','move')),
        before_granted boolean NOT NULL, after_granted boolean NOT NULL,
        before_branch uuid, after_branch uuid NOT NULL,
        before_version bigint NOT NULL CHECK(before_version>=0),
        after_version bigint NOT NULL CHECK(after_version=before_version+1),
        account_state text NOT NULL CHECK(account_state IN ('ACTIVE','PENDING_SETUP','DISABLED')),
        account_version bigint NOT NULL CHECK(account_version>0),
        created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
        PRIMARY KEY(organization_id,operation_id),
        FOREIGN KEY(organization_id,operation_id,account_id,actor_id)
          REFERENCES iam_operator_role_operations(organization_id,operation_id,account_id,actor_id),
        FOREIGN KEY(organization_id,account_id) REFERENCES iam_accounts(organization_id,id),
        FOREIGN KEY(organization_id,actor_id) REFERENCES iam_accounts(organization_id,id),
        FOREIGN KEY(organization_id,actor_branch) 
          REFERENCES organization_branches(organization_id,id),
        FOREIGN KEY(organization_id,before_branch) 
          REFERENCES organization_branches(organization_id,id),
        FOREIGN KEY(organization_id,after_branch) 
          REFERENCES organization_branches(organization_id,id),
        CHECK ((actor_role='MASTER' AND actor_branch IS NULL) OR
          (actor_role='BRANCH_ADMIN' AND actor_branch IS NOT NULL AND kind<>'move'
           AND actor_branch=after_branch)),
        CHECK (kind='add' OR (before_branch IS NOT NULL AND before_version>0)),
        CHECK ((kind='add' AND before_version=0 AND before_branch IS NULL
                    AND NOT before_granted AND after_granted) OR
          (kind='revoke' AND before_granted AND NOT after_granted AND
                    before_branch=after_branch) OR
          (kind='regrant' AND NOT before_granted AND after_granted AND
                    before_branch=after_branch) OR
          (kind='move' AND before_granted AND after_granted AND before_branch<>after_branch))
    )""")


def downgrade() -> None:
    preflight(revision)
    op.execute("""LOCK TABLE iam_operator_role_operations, audit_operator_role_events,
        iam_operator_setup_credentials, iam_operator_grants, audit_operator_account_events
        IN ACCESS EXCLUSIVE MODE""")
    if (
        op.get_bind()
        .execute(
            text("""SELECT
        EXISTS(SELECT FROM iam_operator_role_operations) OR
        EXISTS(SELECT FROM audit_operator_role_events) OR
        EXISTS(SELECT FROM audit_operator_account_events
          WHERE kind IN ('login','logout','password_change') AND actor_role<>'OPERATOR') OR
        EXISTS(SELECT FROM iam_operator_setup_credentials c JOIN iam_operator_grants g
          ON g.account_id=c.account_id WHERE c.branch_id<>g.branch_id)""")
        )
        .scalar_one()
    ):
        raise ValueError("OPERATOR_MANAGEMENT_HISTORY_PRESENT")
    op.execute("""DROP TABLE audit_operator_role_events, iam_operator_role_operations;
        ALTER TABLE audit_operator_account_events DROP CONSTRAINT audit_operator_actor;
        ALTER TABLE iam_operator_setup_credentials DROP CONSTRAINT iam_operator_source_identity,
          DROP CONSTRAINT iam_operator_source_branch;
        ALTER TABLE iam_operator_setup_credentials
          ADD FOREIGN KEY(organization_id,account_id,branch_id)
          REFERENCES iam_operator_grants(organization_id,account_id,branch_id);
        ALTER TABLE iam_operator_grants DROP CONSTRAINT iam_operator_stable_identity""")
    op.execute(
        "ALTER TABLE audit_operator_account_events ADD CONSTRAINT "
        f"audit_operator_account_events_check CHECK {OLD_ACTOR}"
    )
