"""Preserve withdrawn Operator status when moving its retained work branch."""

from sqlalchemy import text

from alembic import op

revision = "0018_withdrawn_operator_move"
down_revision = "0017_operator_management"
branch_labels = None
depends_on = None

OLD_TRANSITION = """((kind='add' AND before_version=0 AND before_branch IS NULL
    AND NOT before_granted AND after_granted) OR
  (kind='revoke' AND before_granted AND NOT after_granted AND before_branch=after_branch) OR
  (kind='regrant' AND NOT before_granted AND after_granted AND before_branch=after_branch) OR
  (kind='move' AND before_granted AND after_granted AND before_branch<>after_branch))"""
NEW_TRANSITION = OLD_TRANSITION.replace(
    "kind='move' AND before_granted AND after_granted",
    "kind='move' AND before_granted=after_granted",
)


def preflight(expected: str) -> None:
    op.execute("LOCK TABLE iam_installation IN ACCESS EXCLUSIVE MODE")
    op.execute("LOCK TABLE alembic_version, iam_policy_transitions IN ACCESS EXCLUSIVE MODE")
    bind = op.get_bind()
    if list(bind.execute(text("SELECT version_num FROM alembic_version")).scalars()) != [expected]:
        raise ValueError("WITHDRAWN_OPERATOR_SCHEMA_MISMATCH")
    if not bind.execute(
        text("""SELECT EXISTS(SELECT FROM iam_installation i
        JOIN iam_policy_transitions p ON p.id=i.policy_transition_id
        WHERE i.id=1 AND i.auth_policy_version=2 AND p.from_version=1 AND p.to_version=2
        AND p.target_schema_revision='0014_password_only')""")
    ).scalar_one():
        raise ValueError("WITHDRAWN_OPERATOR_POLICY_MISMATCH")
    op.execute("""LOCK TABLE iam_operator_role_operations, audit_operator_role_events
        IN ACCESS EXCLUSIVE MODE""")


def replace_transition(expected: str, replacement: str) -> None:
    # Let PostgreSQL canonicalize the original expression with identical column types/order.
    # LIKE does not copy CHECKs by default; this transaction-local parser witness has no rows.
    op.execute("""CREATE TEMPORARY TABLE iam018_expected_transition
        (LIKE audit_operator_role_events) ON COMMIT DROP""")
    op.execute(
        "ALTER TABLE pg_temp.iam018_expected_transition "
        f"ADD CONSTRAINT expected_transition CHECK {expected}"
    )
    matches = list(
        op.get_bind()
        .execute(
            text("""SELECT actual.conname FROM pg_constraint actual
            JOIN pg_constraint expected ON expected.conrelid=
                'pg_temp.iam018_expected_transition'::regclass
                AND expected.conname='expected_transition'
            WHERE actual.conrelid='audit_operator_role_events'::regclass
              AND actual.contype='c' AND actual.convalidated AND NOT actual.connoinherit
              AND actual.conkey=expected.conkey
              AND pg_get_expr(actual.conbin,actual.conrelid)=
                  pg_get_expr(expected.conbin,expected.conrelid)""")
        )
        .scalars()
    )
    if len(matches) != 1:
        raise ValueError("WITHDRAWN_OPERATOR_TRANSITION_CHECK_MISMATCH")
    op.drop_constraint(matches[0], "audit_operator_role_events", type_="check")
    # Keep the discovered original name, including on a downgrade to the original17 shape.
    op.create_check_constraint(matches[0], "audit_operator_role_events", replacement)
    op.execute("DROP TABLE pg_temp.iam018_expected_transition")


def upgrade() -> None:
    preflight(down_revision)
    replace_transition(OLD_TRANSITION, NEW_TRANSITION)


def downgrade() -> None:
    preflight(revision)
    if (
        op.get_bind()
        .execute(
            text("""SELECT EXISTS(SELECT FROM audit_operator_role_events
            WHERE kind='move' AND NOT before_granted AND NOT after_granted)
          OR EXISTS(SELECT FROM iam_operator_role_operations
            WHERE action='move' AND NOT granted)""")
        )
        .scalar_one()
    ):
        raise ValueError("WITHDRAWN_OPERATOR_MOVE_HISTORY_PRESENT")
    replace_transition(NEW_TRANSITION, OLD_TRANSITION)
