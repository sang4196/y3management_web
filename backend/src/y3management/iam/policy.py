"""Server-owned authentication policy boundary; never accept client policy claims."""

from sqlalchemy import text
from sqlalchemy.orm import Session

from y3management.contracts import Rejected
from y3management.iam.public import PolicyStamp


def current_policy(session: Session) -> PolicyStamp:
    row = session.execute(
        text("""SELECT i.auth_policy_version,i.policy_transition_id
      FROM iam_installation i JOIN iam_policy_transitions p ON p.id=i.policy_transition_id
      WHERE i.id=1 AND i.auth_policy_version=2 AND p.from_version=1 AND p.to_version=2
      AND p.target_schema_revision='0014_password_only'
      AND (SELECT array_agg(version_num::text) FROM alembic_version)
          = ARRAY['0015_account_lifecycle']""")
    ).first()
    if row is None:
        raise Rejected(503, "authentication_policy_unavailable")
    return PolicyStamp(row.auth_policy_version, row.policy_transition_id)


def check_policy(session: Session, expected: PolicyStamp) -> None:
    if current_policy(session) != expected:
        raise Rejected(503, "authentication_policy_changed")
