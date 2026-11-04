"""Retire factor authority atomically; preserve durable history and bounded GC."""

import json
from uuid import uuid4

import sqlalchemy as sa

from alembic import op

revision = "0014_password_only"
down_revision = "0013_workforce_trainer_state"
branch_labels = None
depends_on = None

TABLES = (
    "organization_organizations",
    "organization_branches",
    "iam_accounts",
    "iam_login_ids",
    "iam_admin_grants",
    "iam_sessions",
    "iam_security_states",
    "iam_budgets",
    "iam_attempts",
    "iam_preparations",
    "iam_credentials",
    "audit_events",
    "iam_passkeys",
    "iam_mfa_contexts",
    "iam_recovery_credentials",
    "iam_reset_credentials",
    "iam_emergency_cases",
    "iam_emergency_credentials",
    "workforce_trainers",
    "workforce_initial_snapshots",
    "workforce_registration_operations",
    "audit_workforce_initial_events",
    "iam_trainer_bindings",
    "iam_trainer_account_operations",
    "iam_trainer_setup_credentials",
    "audit_trainer_identity_events",
    "iam_trainer_role_grants",
    "iam_trainer_role_operations",
    "audit_trainer_role_events",
    "workforce_trainer_state_origins",
    "workforce_trainer_state_operations",
    "workforce_trainer_state_transitions",
    "audit_trainer_state_events",
)
CHILDREN = (
    "iam_sessions",
    "iam_attempts",
    "iam_preparations",
    "iam_credentials",
    "iam_trainer_setup_credentials",
    "iam_reset_credentials",
    "iam_recovery_credentials",
    "iam_emergency_credentials",
    "iam_mfa_contexts",
)
NEW_TABLES = (
    "audit_password_emergency_events",
    "iam_password_emergency_credentials",
    "iam_password_emergency_cases",
    "iam_policy_account_transitions",
    "iam_policy_transitions",
)
VERSIONS = (
    "row_version",
    "security_version",
    "key_set_version",
    "reset_generation",
    "recovery_generation",
)
CLASSIFICATIONS = (
    "disabled",
    "pending_setup",
    "password_pending",
    "key_only_retired",
    "unchanged_password",
)
FACTS = {
    "state": "text",
    "row_version": "bigint",
    "security_version": "bigint",
    "key_set_version": "bigint",
    "reset_generation": "bigint",
    "recovery_generation": "bigint",
    "password_reset_pending": "boolean",
    "recovery_pending": "boolean",
    "password_ready": "boolean",
    "key_ready": "boolean",
    "trainer_role_epoch": "bigint",
    "admin_scope": "text",
    "admin_branch": "uuid",
}


def _lock() -> None:
    op.execute("LOCK TABLE iam_security_control IN ACCESS EXCLUSIVE MODE")
    op.execute("LOCK TABLE iam_installation," + ",".join(TABLES) + " IN ACCESS EXCLUSIVE MODE")


def _lineage(case: dict, cases: dict) -> dict | None:
    current = case
    seen = set()
    while current["issuer_kind"] == "master_handoff":
        if current["id"] in seen:
            return None
        seen.add(current["id"])
        parent = cases.get(current["handoff_parent_id"])
        origin = cases.get(current["approval_origin_case_id"])
        if not parent or not origin or origin["issuer_kind"] != "operating":
            return None
        if any(
            parent[k] != current[k] or origin[k] != current[k]
            for k in ("organization_id", "account_id", "factors")
        ):
            return None
        if not origin["row_version"] <= parent["row_version"] < current["row_version"]:
            return None
        if (
            parent["completed_at"] is not None
            or origin["completed_at"] is not None
            or parent["issued_at"] > current["issued_at"]
            or any(current[k] != parent[k] + 1 for k in ("row_version", "security_version"))
            or current["reset_generation"]
            != parent["reset_generation"] + int(current["factors"] in ("password", "both"))
            or current["recovery_generation"]
            != parent["recovery_generation"] + int(current["factors"] in ("passkey", "both"))
            or current["key_set_version"]
            != parent["key_set_version"] + int(current["factors"] in ("passkey", "both"))
            or (
                parent["issuer_kind"] == "operating" and parent["expires_at"] > current["issued_at"]
            )
        ):
            return None
        if parent["id"] != current["supersedes"]:
            return None
        if parent["issuer_kind"] == "operating" and parent["id"] != origin["id"]:
            return None
        if (
            parent["issuer_kind"] == "master_handoff"
            and parent["approval_origin_case_id"] != origin["id"]
        ):
            return None
        current = parent
    return current if current["issuer_kind"] == "operating" else None


def _recovery_evidence(bind, row, latest, origin) -> None:
    # A retained event, not the transient token's survival, proves the pending origin.
    # Inspect the latest credential-bearing event: an older matching generation alone
    # cannot override a later completion or a conflicting emergency operation.
    events = (
        bind.execute(
            sa.text("""SELECT * FROM audit_events
      WHERE target_id=:a AND organization_id=:o AND success
      AND after_key_set_version IS NOT NULL
      ORDER BY after_version DESC NULLS LAST,happened_at DESC"""),
            {"a": row["id"], "o": row["organization_id"]},
        )
        .mappings()
        .all()
    )
    if (
        not events
        or row["key_ready"]
        or row["recovery_generation"] <= 0
        or row["state"] == "PENDING_SETUP"
    ):
        raise ValueError("PASSWORD_TRANSITION_UNCLASSIFIED_RECOVERY")
    event = events[0]
    if (
        event["after_recovery_generation"] != row["recovery_generation"]
        or event["after_key_set_version"] != row["key_set_version"]
        or event["after_version"] is None
        or event["after_version"] > row["row_version"]
    ):
        raise ValueError("PASSWORD_TRANSITION_CONFLICTING_RECOVERY")
    normal = (
        event["action"] in ("recovery_start", "recovery_reissue")
        and not row["password_reset_pending"]
        and row["password_ready"]
        and event["before_recovery_generation"] is not None
        and event["before_key_set_version"] is not None
        and event["after_recovery_generation"] == event["before_recovery_generation"] + 1
        and event["after_key_set_version"] == event["before_key_set_version"] + 1
    )
    emergency = bool(
        latest
        and origin
        and latest["completed_at"] is None
        and event["emergency_case_id"] == latest["id"]
        and event["action"] in ("emergency_issue", "emergency_handoff")
        and event["after_version"] == latest["row_version"]
        and latest["organization_id"] == row["organization_id"]
        and latest["factors"] in ("passkey", "both")
        and all(
            latest[k] == row[k]
            for k in ("key_set_version", "reset_generation", "recovery_generation")
        )
        and row["password_reset_pending"] == (latest["factors"] == "both")
        and row["password_ready"] == (latest["factors"] == "passkey")
    )
    if not (normal or emergency):
        raise ValueError("PASSWORD_TRANSITION_UNCLASSIFIED_RECOVERY")


def _summary_constraint(column="summary", names=TABLES) -> str:
    # Subqueries are unavailable in CHECK. The fixed vocabulary and each numeric
    # value are checked explicitly; JSON subtraction detects any unexpected key.
    keys = ",".join("'" + name + "'" for name in names)
    values = " AND ".join(
        f"jsonb_typeof(summary->'{name}')='number' AND (summary->>'{name}') ~ '^[0-9]+$'"
        for name in names
    )
    return (
        "jsonb_typeof(summary)='object' AND summary ?& ARRAY["
        + keys
        + "] AND summary - ARRAY["
        + keys
        + "] = '{}'::jsonb AND "
        + values
    ).replace("summary", column)


def upgrade() -> None:
    bind = op.get_bind()
    _lock()
    counts = {t: bind.execute(sa.text(f"SELECT count(*) FROM {t}")).scalar_one() for t in TABLES}
    rows = (
        bind.execute(
            sa.text("""SELECT a.*,g.scope AS admin_scope,g.branch_id AS admin_branch,
      a.password_hash IS NOT NULL AS password_ready,
      EXISTS(SELECT 1 FROM iam_passkeys k WHERE k.account_id=a.id AND k.revoked_at IS NULL) AS
      key_ready
      FROM iam_accounts a LEFT JOIN iam_admin_grants g ON g.account_id=a.id
      ORDER BY a.id FOR UPDATE OF a""")
        )
        .mappings()
        .all()
    )
    cases = {
        r["id"]: dict(r)
        for r in bind.execute(
            sa.text("SELECT * FROM iam_emergency_cases ORDER BY account_id,row_version FOR UPDATE")
        ).mappings()
    }
    transitions = []
    for row in rows:
        before = {k: row[k] for k in FACTS}
        state, ready, pending = row["state"], row["password_ready"], row["password_reset_pending"]
        if not (
            (state == "PENDING_SETUP" and not ready and not pending)
            or (
                state in ("ACTIVE", "DISABLED")
                and (
                    (pending and not ready and row["reset_generation"] > 0)
                    or (not pending and ready)
                )
            )
        ):
            raise ValueError("PASSWORD_TRANSITION_INCONSISTENT_ACCOUNT")
        own = [c for c in cases.values() if c["account_id"] == row["id"]]
        latest = max(own, key=lambda c: c["row_version"], default=None)
        origin = _lineage(latest, cases) if latest else None
        if latest and origin is None:
            raise ValueError("PASSWORD_TRANSITION_INVALID_LINEAGE")
        same = bool(
            latest
            and latest["completed_at"] is None
            and origin
            and latest["organization_id"] == row["organization_id"]
            and all(row[k] == latest[k] for k in VERSIONS)
            and not any(c["supersedes"] == latest["id"] for c in own)
        )
        eligible = bool(
            same
            and state == "ACTIVE"
            and row["admin_scope"] == "ORGANIZATION"
            and latest["factors"] in ("password", "both")
            and pending
            and not ready
            and row["recovery_pending"] == (latest["factors"] == "both")
            and row["key_ready"] == (latest["factors"] == "password")
        )
        reason = (
            "eligible"
            if eligible
            else "no_case"
            if latest is None
            else "completed"
            if latest["completed_at"] is not None
            else "stale_case"
            if not same
            else "inactive_account"
            if state != "ACTIVE"
            else "ineligible_role"
            if row["admin_scope"] != "ORGANIZATION"
            else "key_only"
            if latest["factors"] == "passkey"
            else "password_not_pending"
        )
        if row["recovery_pending"]:
            _recovery_evidence(bind, row, latest, origin)
        classification = (
            "disabled"
            if state == "DISABLED"
            else "pending_setup"
            if state == "PENDING_SETUP"
            else "password_pending"
            if pending
            else "key_only_retired"
            if row["recovery_pending"]
            else "unchanged_password"
        )
        after = dict(
            before,
            row_version=row["row_version"] + 1,
            security_version=row["security_version"] + 1,
            recovery_pending=False,
            key_ready=False,
        )
        transitions.append(
            (
                row,
                before,
                after,
                classification,
                reason,
                latest if eligible else None,
                origin if eligible else None,
            )
        )
    op.execute(
        """CREATE TABLE iam_policy_transitions (
      id uuid PRIMARY KEY, from_version smallint NOT NULL, to_version smallint NOT NULL,
      transition_at timestamptz NOT NULL, target_schema_revision text NOT NULL, summary jsonb
      NOT NULL,
      classification_counts jsonb NOT NULL,
      CONSTRAINT iam_policy_classification_counts CHECK(CLASSIFICATION_SHAPE),
      CONSTRAINT iam_policy_direction CHECK(from_version=1 AND to_version=2),
      CONSTRAINT iam_policy_to_once UNIQUE(to_version),
      CONSTRAINT iam_policy_summary_shape CHECK(SUMMARY_SHAPE));
    ALTER TABLE iam_installation ADD COLUMN auth_policy_version smallint,
      ADD COLUMN policy_transition_id uuid,
      ADD CONSTRAINT iam_installation_policy_check CHECK(auth_policy_version=2),
      ADD CONSTRAINT iam_installation_transition_fk FOREIGN KEY(policy_transition_id)
        REFERENCES iam_policy_transitions(id);
    ALTER TABLE iam_security_states ADD COLUMN policy_version smallint NOT NULL DEFAULT 1,
      ADD CONSTRAINT iam_security_policy_check CHECK(policy_version IN (1,2)),
      ADD CONSTRAINT iam_security_policy_identity UNIQUE(id,policy_version),
      ADD CONSTRAINT iam_security_allocation_identity UNIQUE(id,policy_version,kind,expires_at);
    ALTER TABLE iam_security_states ALTER COLUMN policy_version DROP DEFAULT;
    """.replace("SUMMARY_SHAPE", _summary_constraint()).replace(
            "CLASSIFICATION_SHAPE", _summary_constraint("classification_counts", CLASSIFICATIONS)
        )
    )
    facts = ",".join(
        f"{prefix}_{key} {typ}" + ("" if key in ("admin_scope", "admin_branch") else " NOT NULL")
        for prefix in ("before", "after")
        for key, typ in FACTS.items()
    )
    op.execute(f"""CREATE TABLE iam_policy_account_transitions (
      transition_id uuid NOT NULL, organization_id uuid NOT NULL, account_id uuid NOT NULL,
      {facts}, classification text NOT NULL, retirement_kind text NOT NULL,
      legacy_parent_id uuid, legacy_origin_id uuid, legacy_factors text,
      legacy_password_continuation_eligible boolean NOT NULL,
      continuation_reason text NOT NULL,
      CONSTRAINT iam_policy_continuation_reason CHECK(continuation_reason IN
        ('eligible','no_case','completed','stale_case','inactive_account','ineligible_role','key_only','password_not_pending')
        AND legacy_password_continuation_eligible=(continuation_reason='eligible')),
      PRIMARY KEY(transition_id,organization_id,account_id),
      CONSTRAINT iam_policy_account_header_fk FOREIGN KEY(transition_id) REFERENCES
      iam_policy_transitions(id),
      CONSTRAINT iam_policy_account_target_fk FOREIGN KEY(organization_id,account_id)
        REFERENCES iam_accounts(organization_id,id),
      CONSTRAINT iam_policy_account_retirement CHECK(
        (before_recovery_pending AND retirement_kind='retired_feature') OR
        (NOT before_recovery_pending AND retirement_kind='none')),
      CONSTRAINT iam_policy_account_classification CHECK(classification IN
        ('disabled','pending_setup','password_pending','key_only_retired','unchanged_password')),
      CONSTRAINT iam_policy_account_versions CHECK(after_row_version=before_row_version+1
        AND after_security_version=before_security_version+1 AND after_state=before_state
        AND after_password_ready=before_password_ready
        AND after_password_reset_pending=before_password_reset_pending
        AND after_reset_generation=before_reset_generation
        AND after_recovery_generation=before_recovery_generation
        AND after_key_set_version=before_key_set_version
        AND after_trainer_role_epoch=before_trainer_role_epoch
        AND after_admin_scope IS NOT DISTINCT FROM before_admin_scope
        AND after_admin_branch IS NOT DISTINCT FROM before_admin_branch
        AND NOT after_recovery_pending AND NOT after_key_ready),
      CONSTRAINT iam_policy_account_eligible CHECK(
        (legacy_password_continuation_eligible AND legacy_parent_id IS NOT NULL
         AND legacy_origin_id IS NOT NULL AND legacy_factors IS NOT NULL
         AND legacy_factors IN ('password','both') AND before_state='ACTIVE'
         AND before_password_reset_pending AND NOT before_password_ready)
        OR (NOT legacy_password_continuation_eligible AND legacy_parent_id IS NULL
          AND legacy_origin_id IS NULL AND legacy_factors IS NULL)),
      CONSTRAINT iam_policy_account_parent_fk FOREIGN KEY
        (legacy_parent_id,organization_id,account_id,legacy_factors)
        REFERENCES iam_emergency_cases(id,organization_id,account_id,factors),
      CONSTRAINT iam_policy_account_origin_fk FOREIGN KEY
        (legacy_origin_id,organization_id,account_id,legacy_factors)
        REFERENCES iam_emergency_cases(id,organization_id,account_id,factors),
      CONSTRAINT iam_policy_account_eligibility_identity UNIQUE
        (transition_id,organization_id,account_id,legacy_parent_id,legacy_origin_id,
         legacy_factors,legacy_password_continuation_eligible));""")
    ident = uuid4()
    now = bind.execute(sa.text("SELECT clock_timestamp()")).scalar_one()
    classified = {kind: sum(item[3] == kind for item in transitions) for kind in CLASSIFICATIONS}
    bind.execute(
        sa.text(
            "INSERT INTO iam_policy_transitions "
            "VALUES(:i,1,2,:n,:r,CAST(:s AS jsonb),CAST(:c AS jsonb))"
        ),
        {"i": ident, "n": now, "r": revision, "s": json.dumps(counts), "c": json.dumps(classified)},
    )
    for row, before, after, classification, reason, parent, origin in transitions:
        values = {
            f"{prefix}_{k}": v
            for prefix, snap in (("before", before), ("after", after))
            for k, v in snap.items()
        }
        values.update(
            transition_id=ident,
            organization_id=row["organization_id"],
            account_id=row["id"],
            classification=classification,
            continuation_reason=reason,
            retirement_kind="retired_feature" if row["recovery_pending"] else "none",
            legacy_parent_id=parent["id"] if parent else None,
            legacy_origin_id=origin["id"] if origin else None,
            legacy_factors=parent["factors"] if parent else None,
            legacy_password_continuation_eligible=bool(parent),
        )
        bind.execute(
            sa.text(
                "INSERT INTO iam_policy_account_transitions ("
                + ",".join(values)
                + ") VALUES ("
                + ",".join(":" + k for k in values)
                + ")"
            ),
            values,
        )
    recorded = set(
        bind.execute(
            sa.text("SELECT account_id FROM iam_policy_account_transitions WHERE transition_id=:i"),
            {"i": ident},
        ).scalars()
    )
    if recorded != {row["id"] for row in rows} or len(recorded) != counts["iam_accounts"]:
        raise ValueError("PASSWORD_TRANSITION_ACCOUNT_SET_MISMATCH")
    recorded_counts = dict(
        bind.execute(
            sa.text(
                "SELECT classification,count(*) FROM iam_policy_account_transitions "
                "WHERE transition_id=:i GROUP BY classification"
            ),
            {"i": ident},
        ).all()
    )
    if {kind: recorded_counts.get(kind, 0) for kind in CLASSIFICATIONS} != classified:
        raise ValueError("PASSWORD_TRANSITION_CLASSIFICATION_COUNT_MISMATCH")
    op.execute(
        "UPDATE iam_accounts SET row_version=row_version+1,"
        "security_version=security_version+1,recovery_pending=false"
    )
    op.execute("UPDATE iam_sessions SET revoked=true")
    for table in CHILDREN:
        if table not in ("iam_sessions", "iam_attempts"):
            op.execute(
                f"UPDATE {table} SET consumed=true"
                + (",password_hash=NULL" if table == "iam_mfa_contexts" else "")
            )
        op.execute(f"""ALTER TABLE {table} ADD COLUMN policy_version smallint NOT NULL DEFAULT 1,
          ADD CONSTRAINT {table}_policy_check CHECK(policy_version IN (1,2)),
          ADD CONSTRAINT {table}_policy_fk FOREIGN KEY(id,policy_version)
            REFERENCES iam_security_states(id,policy_version);
          ALTER TABLE {table} ALTER COLUMN policy_version DROP DEFAULT;""")
        if table not in ("iam_sessions", "iam_attempts"):
            op.execute(
                f"ALTER TABLE {table} ADD CONSTRAINT {table}_legacy_consumed "
                "CHECK(policy_version<>1 OR consumed)"
            )
    bind.execute(sa.text("UPDATE iam_passkeys SET revoked_at=COALESCE(revoked_at,:n)"), {"n": now})
    bind.execute(
        sa.text("UPDATE iam_installation SET auth_policy_version=2,policy_transition_id=:i"),
        {"i": ident},
    )
    op.execute("""ALTER TABLE iam_installation ALTER COLUMN auth_policy_version SET NOT NULL,
      ALTER COLUMN policy_transition_id SET NOT NULL;
    ALTER TABLE iam_sessions ADD COLUMN login_attempt_id uuid,
      ADD CONSTRAINT iam_sessions_legacy_revoked CHECK(policy_version<>1 OR revoked),
      ADD CONSTRAINT iam_sessions_password_policy CHECK(policy_version<>2 OR assurance='password'),
      ADD CONSTRAINT iam_sessions_attempt_binding CHECK(policy_version<>2 OR login_attempt_id
      IS NOT NULL);""")
    _password_cases()


def _password_cases() -> None:
    op.execute("""CREATE TABLE iam_password_emergency_cases (
      id uuid CONSTRAINT iam_pw_cases_pkey PRIMARY KEY,
      organization_id uuid NOT NULL,account_id uuid NOT NULL,
      policy_version smallint NOT NULL, purpose text NOT NULL, source_purpose text NOT NULL,
      kind text NOT NULL, fingerprint bytea NOT NULL,
      issuer_account_id uuid, approval_mode text NOT NULL,
      approval_ref varchar(128),owner_ref varchar(128),executor_ref varchar(128),executor_uid
      bigint,
      checked_at timestamptz,approval_valid_until timestamptz,
      parent_id uuid,legacy_origin_id uuid,legacy_parent_id uuid,
      legacy_origin_factors text,legacy_parent_factors text,
      policy_transition_id uuid,continuation_eligible boolean,
      issued_at timestamptz NOT NULL,expires_at timestamptz NOT NULL,completed_at timestamptz,
      row_version bigint NOT NULL,security_version bigint NOT NULL,reset_generation bigint NOT NULL,
      CONSTRAINT iam_pw_case_identity UNIQUE(id,organization_id,account_id),
      CONSTRAINT iam_pw_case_source_identity UNIQUE
        (id,organization_id,account_id,policy_version,source_purpose,expires_at),
      CONSTRAINT iam_pw_case_policy CHECK(policy_version=2),
      CONSTRAINT iam_pw_case_purpose CHECK(purpose='password' AND
      source_purpose='emergency_password'),
      CONSTRAINT iam_pw_case_fingerprint CHECK(octet_length(fingerprint)=32),
      CONSTRAINT iam_pw_case_deadline CHECK(expires_at>issued_at AND
      expires_at<=issued_at+interval '30 minutes'),
      CONSTRAINT iam_pw_case_versions CHECK(row_version>0 AND security_version>0 AND
      reset_generation>0),
      CONSTRAINT iam_pw_case_target_fk FOREIGN KEY(organization_id,account_id) REFERENCES
      iam_accounts(organization_id,id),
      CONSTRAINT iam_pw_case_actor_fk FOREIGN KEY(organization_id,issuer_account_id) REFERENCES
      iam_accounts(organization_id,id),
      CONSTRAINT iam_pw_case_parent_fk FOREIGN KEY(parent_id,organization_id,account_id)
        REFERENCES iam_password_emergency_cases(id,organization_id,account_id),
      CONSTRAINT iam_pw_case_legacy_origin_fk FOREIGN
      KEY(legacy_origin_id,organization_id,account_id,legacy_origin_factors)
        REFERENCES iam_emergency_cases(id,organization_id,account_id,factors),
      CONSTRAINT iam_pw_case_legacy_parent_fk FOREIGN
      KEY(legacy_parent_id,organization_id,account_id,legacy_parent_factors)
        REFERENCES iam_emergency_cases(id,organization_id,account_id,factors),
      CONSTRAINT iam_pw_case_transition_fk FOREIGN
      KEY(policy_transition_id,organization_id,account_id,
        legacy_parent_id,legacy_origin_id,legacy_parent_factors,continuation_eligible)
        REFERENCES iam_policy_account_transitions(transition_id,organization_id,account_id,
          legacy_parent_id,legacy_origin_id,legacy_factors,legacy_password_continuation_eligible),
      CONSTRAINT iam_pw_case_no_self_parent CHECK(parent_id IS NULL OR parent_id<>id),
      CONSTRAINT iam_pw_case_variant CHECK (
        (kind='operating' AND approval_mode='manual' AND issuer_account_id IS NULL
         AND approval_ref IS NOT NULL AND owner_ref IS NOT NULL AND executor_ref IS NOT NULL
         AND executor_uid IS NOT NULL AND executor_uid>=0 AND owner_ref<>executor_ref
         AND checked_at IS NOT NULL AND approval_valid_until IS NOT NULL
         AND checked_at<=issued_at AND approval_valid_until>issued_at
         AND parent_id IS NULL AND legacy_origin_id IS NULL AND legacy_parent_id IS NULL
         AND legacy_origin_factors IS NULL AND legacy_parent_factors IS NULL
         AND policy_transition_id IS NULL AND continuation_eligible IS NULL)
        OR (kind IN ('legacy_handoff','handoff') AND approval_mode='current_master'
         AND issuer_account_id IS NOT NULL AND issuer_account_id<>account_id
         AND approval_ref IS NULL AND owner_ref IS NULL AND executor_ref IS NULL
         AND executor_uid IS NULL AND checked_at IS NULL AND approval_valid_until IS NULL
         AND ((kind='legacy_handoff' AND parent_id IS NULL AND legacy_origin_id IS NOT NULL
           AND legacy_parent_id IS NOT NULL AND legacy_origin_factors IS NOT NULL
           AND legacy_parent_factors IS NOT NULL AND legacy_origin_factors=legacy_parent_factors
           AND legacy_parent_factors IN ('password','both') AND policy_transition_id IS NOT NULL
           AND continuation_eligible IS NOT NULL AND continuation_eligible)
          OR (kind='handoff' AND parent_id IS NOT NULL AND legacy_origin_id IS NULL
           AND legacy_parent_id IS NULL AND legacy_origin_factors IS NULL
           AND legacy_parent_factors IS NULL AND policy_transition_id IS NULL AND
           continuation_eligible IS NULL)))));
    CREATE UNIQUE INDEX iam_pw_one_child ON iam_password_emergency_cases(parent_id) WHERE
    parent_id IS NOT NULL;
    CREATE UNIQUE INDEX iam_pw_one_legacy_child ON
    iam_password_emergency_cases(legacy_parent_id) WHERE legacy_parent_id IS NOT NULL;
    CREATE TABLE iam_password_emergency_credentials (
      id uuid CONSTRAINT iam_pw_credentials_pkey PRIMARY KEY,case_id uuid NOT NULL,
      organization_id uuid NOT NULL,account_id uuid NOT NULL,
      policy_version smallint NOT NULL,allocator_kind text NOT NULL,purpose text NOT NULL,
      digest bytea NOT NULL,expires_at timestamptz NOT NULL,consumed boolean NOT NULL DEFAULT false,
      CONSTRAINT iam_pw_one_source_per_case UNIQUE(case_id),
      CONSTRAINT iam_pw_source_digest_unique UNIQUE(digest),
      CONSTRAINT iam_pw_source_digest CHECK(octet_length(digest)=32),
      CONSTRAINT iam_pw_source_kind CHECK(allocator_kind='emergency'),
      CONSTRAINT iam_pw_source_purpose CHECK(purpose='emergency_password'),
      CONSTRAINT iam_pw_source_policy CHECK(policy_version=2),
      CONSTRAINT iam_pw_source_allocator_fk FOREIGN KEY(id,policy_version,allocator_kind,expires_at)
        REFERENCES iam_security_states(id,policy_version,kind,expires_at) ON DELETE CASCADE,
      CONSTRAINT iam_pw_source_case_fk FOREIGN
      KEY(case_id,organization_id,account_id,policy_version,purpose,expires_at)
        REFERENCES
        iam_password_emergency_cases(id,organization_id,account_id,policy_version,source_purpose,expires_at));
    CREATE INDEX iam_pw_source_account_idx ON iam_password_emergency_credentials(account_id);
    CREATE TABLE audit_password_emergency_events (
      id uuid CONSTRAINT audit_pw_events_pkey PRIMARY KEY,
      case_id uuid NOT NULL,organization_id uuid NOT NULL,target_id uuid NOT NULL,actor_id uuid,
      action text NOT NULL,actor_role text NOT NULL,approval_mode text NOT NULL,
      before_version bigint NOT NULL,after_version bigint NOT NULL,
      before_security_version bigint NOT NULL,after_security_version bigint NOT NULL,
      before_reset_generation bigint NOT NULL,after_reset_generation bigint NOT NULL,
      policy_version smallint NOT NULL CHECK(policy_version=2),recorded_at timestamptz NOT NULL,
      CONSTRAINT audit_pw_case_fk FOREIGN KEY(case_id,organization_id,target_id)
        REFERENCES iam_password_emergency_cases(id,organization_id,account_id),
      CONSTRAINT audit_pw_actor_fk FOREIGN KEY(organization_id,actor_id) REFERENCES
      iam_accounts(organization_id,id),
      CONSTRAINT audit_pw_version_check CHECK(after_version=before_version+1
        AND after_security_version=before_security_version+1
        AND after_reset_generation>=before_reset_generation),
      CONSTRAINT audit_pw_event_variant CHECK(
        (action='issue' AND actor_id IS NULL AND actor_role='SYSTEM_RECOVERY_OPERATOR' AND
        approval_mode='manual')
        OR (action='handoff' AND actor_id IS NOT NULL AND actor_id<>target_id AND
        actor_role='MASTER' AND approval_mode='current_master')
        OR (action='complete' AND actor_id IS NOT NULL AND actor_id=target_id AND
        actor_role='RECOVERY_RECIPIENT'
          AND approval_mode IN ('manual','current_master'))));
    CREATE INDEX audit_pw_case_time_idx ON audit_password_emergency_events(case_id,recorded_at);
    """)


def downgrade() -> None:
    bind = op.get_bind()
    _lock()
    op.execute("LOCK TABLE " + ",".join(NEW_TABLES) + " IN ACCESS EXCLUSIVE MODE")
    expected = (
        set(TABLES)
        | set(NEW_TABLES)
        | {"iam_installation", "iam_security_control", "alembic_version"}
    )
    actual = set(
        bind.execute(
            sa.text("SELECT tablename FROM pg_tables WHERE schemaname=current_schema()")
        ).scalars()
    )
    if actual != expected:
        raise ValueError("PASSWORD_DOWNGRADE_UNKNOWN_TABLES")
    if any(
        bind.execute(sa.text(f"SELECT EXISTS(SELECT 1 FROM {table})")).scalar_one()
        for table in (*TABLES, *NEW_TABLES[:-1])
    ):
        raise ValueError("PASSWORD_DOWNGRADE_REQUIRES_GLOBAL_EMPTY")
    headers = bind.execute(sa.text("SELECT * FROM iam_policy_transitions")).mappings().all()
    installation = bind.execute(sa.text("SELECT * FROM iam_installation")).mappings().all()
    controls = list(bind.execute(sa.text("SELECT id FROM iam_security_control")).scalars())
    revisions = list(bind.execute(sa.text("SELECT version_num FROM alembic_version")).scalars())
    if (
        revisions != [revision]
        or len(headers) != 1
        or len(installation) != 1
        or controls != [1]
        or installation[0]["id"] != 1
        or installation[0]["organization_id"] is not None
        or installation[0]["auth_policy_version"] != 2
        or installation[0]["policy_transition_id"] != headers[0]["id"]
        or headers[0]["target_schema_revision"] != revision
        or headers[0]["summary"] != {t: 0 for t in TABLES}
        or headers[0]["classification_counts"] != {kind: 0 for kind in CLASSIFICATIONS}
    ):
        raise ValueError("PASSWORD_DOWNGRADE_NONEMPTY_TRANSITION")
    for table in NEW_TABLES[:-1]:
        op.execute(f"DROP TABLE {table}")
    op.execute("ALTER TABLE iam_sessions DROP COLUMN login_attempt_id CASCADE")
    for table in CHILDREN:
        op.execute(f"ALTER TABLE {table} DROP COLUMN policy_version CASCADE")
    op.execute("ALTER TABLE iam_security_states DROP COLUMN policy_version CASCADE")
    op.execute(
        "ALTER TABLE iam_installation DROP COLUMN auth_policy_version,"
        "DROP COLUMN policy_transition_id"
    )
    op.execute("DROP TABLE iam_policy_transitions")
