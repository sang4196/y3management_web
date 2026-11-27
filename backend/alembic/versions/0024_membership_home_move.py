"""Member Home moves: preserve all23 rows, extend only kind/typed transition constraints."""

import re

from sqlalchemy import text

from alembic import op

revision = "0024_membership_home_move"
down_revision = "0023_membership_basics"
branch_labels = None
depends_on = None

OLD = {
    "membership_member_versions": {
        "membership_member_versions_kind_check": (
            "kind IN ('create','update','deactivate','reactivate')"
        ),
        "membership_member_versions_check": """(kind='create' AND before_version IS NULL
          AND before_active IS NULL AND before_home_branch_id IS NULL AND version=1 AND active)
          OR (kind IN ('update','deactivate','reactivate') AND before_version IS NOT NULL
          AND before_version>0 AND version=before_version+1 AND before_active IS NOT NULL
          AND before_home_branch_id IS NOT NULL AND home_branch_id=before_home_branch_id
          AND ((kind='update' AND active=before_active)
          OR (kind='deactivate' AND before_active AND NOT active)
          OR (kind='reactivate' AND NOT before_active AND active)))""",
    },
    "membership_member_operations": {
        "membership_member_operations_kind_check": (
            "kind IN ('create','update','deactivate','reactivate')"
        ),
        "membership_member_operations_check": """(actor_role='MASTER' AND actor_branch IS NULL)
          OR (actor_role IN ('BRANCH_ADMIN','OPERATOR') AND actor_branch IS NOT NULL
          AND actor_branch=home_branch_id)""",
        "membership_member_operations_check1": (
            "kind IN ('create','update') OR actor_role IN ('MASTER','BRANCH_ADMIN')"
        ),
        "membership_member_operations_check2": """(kind='create' AND before_version IS NULL AND
          after_version=1 AND changed)
          OR (kind IN ('update','deactivate','reactivate') AND before_version IS NOT NULL AND
            before_version>0
          AND ((changed AND after_version=before_version+1) OR (NOT changed AND
            after_version=before_version)))""",
    },
    "audit_member_events": {
        "audit_member_events_check": """(actor_role='MASTER' AND actor_branch IS NULL)
          OR (actor_role IN ('BRANCH_ADMIN','OPERATOR') AND actor_branch IS NOT NULL
          AND actor_branch=home_branch_id)""",
        "audit_member_events_check1": """(kind='create' AND before_version IS NULL AND
          after_version=1)
          OR (kind IN ('update','deactivate','reactivate') AND before_version IS NOT NULL AND
            before_version>0)""",
    },
}


def preflight(expected: str) -> None:
    op.execute("LOCK TABLE iam_installation IN ACCESS EXCLUSIVE MODE")
    op.execute("LOCK TABLE alembic_version,iam_policy_transitions IN ACCESS EXCLUSIVE MODE")
    bind = op.get_bind()
    if list(bind.execute(text("SELECT version_num FROM alembic_version")).scalars()) != [expected]:
        raise ValueError("MEMBER_HOME_SCHEMA_MISMATCH")
    if not bind.execute(
        text("""SELECT EXISTS(SELECT FROM iam_installation i
      JOIN iam_policy_transitions p ON p.id=i.policy_transition_id
      WHERE i.id=1 AND i.auth_policy_version=2 AND p.from_version=1 AND p.to_version=2
      AND p.target_schema_revision='0014_password_only')""")
    ).scalar_one():
        raise ValueError("MEMBER_HOME_POLICY_MISMATCH")
    op.execute("""LOCK TABLE membership_members,membership_member_versions,
      membership_member_operations,audit_member_events IN ACCESS EXCLUSIVE MODE""")


def upgrade() -> None:
    preflight(down_revision)
    # Check the original kind/actor CHECK name set before any ALTER.
    for table, checks in OLD.items():
        actual = {
            name
            for name, definition in op.get_bind().execute(
                text("""SELECT conname,
          pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid=to_regclass(:t) AND
            contype='c'"""),
                {"t": table},
            )
            if re.search(r"\b(?:kind|actor_branch)\b", definition)
        }
        if actual != set(checks):
            raise ValueError("MEMBER_HOME_CONSTRAINT_MISMATCH")
    for table, checks in OLD.items():
        for name in checks:
            op.execute(f"ALTER TABLE {table} DROP CONSTRAINT {name}")
    op.execute("""
    ALTER TABLE membership_member_versions
      ADD CONSTRAINT member_home_version_kind CHECK(kind IN
        ('create','update','deactivate','reactivate','move_home')),
      ADD CONSTRAINT member_home_version_transition CHECK(
        (kind='create' AND before_version IS NULL AND before_active IS NULL
          AND before_home_branch_id IS NULL AND version=1 AND active)
        OR (kind IN ('update','deactivate','reactivate','move_home') AND before_version IS NOT NULL
          AND before_version>0 AND version=before_version+1 AND before_active IS NOT NULL
          AND before_home_branch_id IS NOT NULL
          AND ((kind='move_home' AND home_branch_id<>before_home_branch_id AND active=before_active)
            OR (kind IN ('update','deactivate','reactivate') AND
              home_branch_id=before_home_branch_id
              AND ((kind='update' AND active=before_active)
                OR (kind='deactivate' AND before_active AND NOT active)
                OR (kind='reactivate' AND NOT before_active AND active))))));
    ALTER TABLE membership_member_operations
      ADD CONSTRAINT member_home_operation_kind CHECK(kind IN
        ('create','update','deactivate','reactivate','move_home')),
      ADD CONSTRAINT member_home_actor_scope CHECK(
        (actor_role='MASTER' AND actor_branch IS NULL)
        OR (actor_role IN ('BRANCH_ADMIN','OPERATOR') AND actor_branch IS NOT NULL
          AND (actor_branch=home_branch_id OR (kind='move_home' AND actor_role='BRANCH_ADMIN')))),
      ADD CONSTRAINT member_home_admin CHECK(kind IN ('create','update') OR actor_role IN
        ('MASTER','BRANCH_ADMIN')),
      ADD CONSTRAINT member_home_operation_delta CHECK(
        (kind='create' AND before_version IS NULL AND after_version=1 AND changed)
        OR (kind IN ('update','deactivate','reactivate','move_home') AND before_version IS NOT
          NULL AND before_version>0
          AND ((changed AND after_version=before_version+1) OR (NOT changed AND
            after_version=before_version)))),
      ADD CONSTRAINT member_home_actor_before_fk FOREIGN KEY
        (organization_id,member_id,before_version,actor_branch) REFERENCES
        membership_member_versions(organization_id,member_id,version,home_branch_id);
    ALTER TABLE audit_member_events
      ADD CONSTRAINT member_home_audit_scope CHECK(
        (actor_role='MASTER' AND actor_branch IS NULL)
        OR (actor_role IN ('BRANCH_ADMIN','OPERATOR') AND actor_branch IS NOT NULL
          AND (actor_branch=home_branch_id OR (kind='move_home' AND actor_role='BRANCH_ADMIN')))),
      ADD CONSTRAINT member_home_audit_before CHECK(
        (kind='create' AND before_version IS NULL AND after_version=1)
        OR (kind IN ('update','deactivate','reactivate','move_home') AND before_version IS NOT
          NULL AND before_version>0));
    """)


def downgrade() -> None:
    preflight(revision)
    if (
        op.get_bind()
        .execute(
            text("""SELECT
      EXISTS(SELECT FROM membership_member_versions WHERE kind='move_home') OR
      EXISTS(SELECT FROM membership_member_operations WHERE kind='move_home') OR
      EXISTS(SELECT FROM audit_member_events WHERE kind='move_home')""")
        )
        .scalar_one()
    ):
        raise ValueError("MEMBER_HOME_HISTORY_PRESENT")
    for table, names in {
        "membership_member_versions": [
            "member_home_version_kind",
            "member_home_version_transition",
        ],
        "membership_member_operations": [
            "member_home_operation_kind",
            "member_home_actor_scope",
            "member_home_admin",
            "member_home_operation_delta",
            "member_home_actor_before_fk",
        ],
        "audit_member_events": ["member_home_audit_scope", "member_home_audit_before"],
    }.items():
        for name in names:
            op.execute(f"ALTER TABLE {table} DROP CONSTRAINT {name}")
    for table, checks in OLD.items():
        for name, definition in checks.items():
            op.execute(f"ALTER TABLE {table} ADD CONSTRAINT {name} CHECK({definition})")
