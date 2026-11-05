"""Independent Operator work scope and single-use initial credentials."""

from sqlalchemy import text

from alembic import op

revision = "0016_operator_onboarding"
down_revision = "0015_account_lifecycle"
branch_labels = None
depends_on = None


def _preflight(expected: str) -> None:
    bind = op.get_bind()
    # Serialize with application writers before taking locks on their child tables.
    bind.execute(text("SELECT id FROM iam_installation WHERE id=1 FOR UPDATE")).one()
    op.execute("LOCK TABLE alembic_version, iam_policy_transitions IN SHARE ROW EXCLUSIVE MODE")
    if list(bind.execute(text("SELECT version_num FROM alembic_version")).scalars()) != [expected]:
        raise ValueError("OPERATOR_SCHEMA_MISMATCH")
    if not bind.execute(
        text("""SELECT EXISTS (
        SELECT FROM iam_installation i JOIN iam_policy_transitions p
        ON i.policy_transition_id=p.id WHERE i.id=1 AND i.auth_policy_version=2
        AND p.from_version=1 AND p.to_version=2
        AND p.target_schema_revision='0014_password_only')""")
    ).scalar_one():
        raise ValueError("OPERATOR_POLICY_MISMATCH")


def upgrade() -> None:
    _preflight(down_revision)
    op.execute("""
        CREATE TABLE iam_operator_grants (
            account_id uuid PRIMARY KEY, organization_id uuid NOT NULL, branch_id uuid NOT NULL,
            granted boolean NOT NULL, version bigint NOT NULL CHECK(version>0),
            UNIQUE(organization_id,account_id,branch_id),
            FOREIGN KEY(organization_id,account_id) REFERENCES iam_accounts(organization_id,id),
            FOREIGN KEY(organization_id,branch_id)
                REFERENCES organization_branches(organization_id,id)
        );
        CREATE FUNCTION iam_operator_grant_guard() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            IF TG_OP='DELETE' THEN
                RAISE EXCEPTION 'OPERATOR_GRANT_HISTORY';
            END IF;
            IF NEW.account_id<>OLD.account_id OR NEW.organization_id<>OLD.organization_id
                OR NEW.version<=OLD.version THEN
                RAISE EXCEPTION 'OPERATOR_GRANT_VERSION';
            END IF;
            RETURN NEW;
        END $$;
        CREATE TRIGGER iam_operator_grant_evolution BEFORE UPDATE OR DELETE ON iam_operator_grants
            FOR EACH ROW EXECUTE FUNCTION iam_operator_grant_guard();
        ALTER TABLE iam_sessions ADD COLUMN operator_version bigint NOT NULL DEFAULT 0
            CHECK(operator_version>=0);
        CREATE TABLE iam_operator_setup_credentials (
            id uuid PRIMARY KEY,
            allocator_kind text NOT NULL DEFAULT 'credential' CHECK(allocator_kind='credential'),
            purpose text NOT NULL CHECK(purpose='operator_initial'),
            policy_version integer NOT NULL CHECK(policy_version=2),
            organization_id uuid NOT NULL, account_id uuid NOT NULL, branch_id uuid NOT NULL,
            account_version bigint NOT NULL CHECK(account_version>0),
            security_version bigint NOT NULL CHECK(security_version>0),
            grant_version bigint NOT NULL CHECK(grant_version>0),
            digest bytea NOT NULL UNIQUE CHECK(octet_length(digest)=32),
            expires_at timestamptz NOT NULL, consumed boolean NOT NULL DEFAULT false,
            FOREIGN KEY(id,policy_version,allocator_kind,expires_at)
                REFERENCES iam_security_states(id,policy_version,kind,expires_at) ON DELETE CASCADE,
            FOREIGN KEY(organization_id,account_id,branch_id)
                REFERENCES iam_operator_grants(organization_id,account_id,branch_id)
        );
        CREATE UNIQUE INDEX iam_one_operator_initial ON iam_operator_setup_credentials(account_id)
            WHERE NOT consumed;
        CREATE TABLE audit_operator_account_events (
            id uuid PRIMARY KEY, organization_id uuid NOT NULL, account_id uuid NOT NULL,
            branch_id uuid NOT NULL, actor_id uuid, actor_branch uuid, actor_role text NOT NULL,
            kind text NOT NULL, before_state text, after_state text NOT NULL,
            before_version bigint, after_version bigint NOT NULL CHECK(after_version>0),
            created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            FOREIGN KEY(organization_id,account_id) REFERENCES iam_accounts(organization_id,id),
            FOREIGN KEY(organization_id,branch_id)
                REFERENCES organization_branches(organization_id,id),
            FOREIGN KEY(organization_id,actor_id) REFERENCES iam_accounts(organization_id,id),
            FOREIGN KEY(organization_id,actor_branch)
                REFERENCES organization_branches(organization_id,id),
            CHECK ((kind IN ('issue','reissue') AND actor_id IS NOT NULL AND
                    ((actor_role='MASTER' AND actor_branch IS NULL) OR
                    (actor_role='BRANCH_ADMIN' AND actor_branch IS NOT NULL
                     AND actor_branch=branch_id)))
                OR (kind='setup_complete' AND actor_role='CREDENTIAL_HOLDER' AND
                    actor_id IS NULL AND actor_branch IS NULL)
                OR (kind IN ('login','logout','password_change') AND actor_role='OPERATOR'
                    AND actor_id IS NOT NULL AND actor_id=account_id
                    AND actor_branch IS NOT NULL AND actor_branch=branch_id)),
            CHECK ((kind='issue' AND before_state IS NULL AND before_version IS NULL
                    AND after_state='PENDING_SETUP' AND after_version=1)
                OR (kind IN ('reissue','setup_complete') AND before_state IS NOT NULL
                    AND before_state='PENDING_SETUP' AND before_version IS NOT NULL
                    AND before_version>0 AND after_version=before_version+1 AND
                    after_state=CASE kind WHEN 'reissue' THEN 'PENDING_SETUP' ELSE 'ACTIVE' END)
                OR (kind IN ('login','logout','password_change') AND before_state IS NOT NULL
                    AND before_state='ACTIVE' AND after_state='ACTIVE' AND before_version>0
                    AND before_version IS NOT NULL
                    AND after_version=before_version+CASE kind WHEN 'password_change' THEN 1
                    ELSE 0 END))
        )
    """)


def downgrade() -> None:
    # Drain policy readers before child DDL and later revisions in this transaction.
    op.execute("LOCK TABLE iam_installation IN ACCESS EXCLUSIVE MODE")
    _preflight(revision)
    op.execute("""LOCK TABLE iam_sessions, iam_operator_setup_credentials, iam_operator_grants,
        audit_operator_account_events IN ACCESS EXCLUSIVE MODE""")
    if (
        op.get_bind()
        .execute(
            text("""SELECT EXISTS(SELECT FROM iam_operator_grants)
        OR EXISTS(SELECT FROM iam_operator_setup_credentials)
        OR EXISTS(SELECT FROM audit_operator_account_events)
        OR EXISTS(SELECT FROM iam_sessions WHERE operator_version<>0)""")
        )
        .scalar_one()
    ):
        raise ValueError("OPERATOR_HISTORY_PRESENT")
    op.execute("""DROP TABLE audit_operator_account_events, iam_operator_setup_credentials;
        DROP TABLE iam_operator_grants;
        DROP FUNCTION iam_operator_grant_guard();
        ALTER TABLE iam_sessions DROP COLUMN operator_version""")
