"""Normal Master authority for immutable emergency issuance children."""

from alembic import op

revision = "0009_iam_emergency_handoff"
down_revision = "0008_iam_emergency_recovery"
branch_labels = None
depends_on = None
_ACTIONS = (
    "'bootstrap','branch_create','account_issue','setup_reissue','setup_complete',"
    "'account_disable','scope_change','login','logout','account_restore',"
    "'password_change','login_id_change','passkey_register','passkey_delete',"
    "'recovery_start','recovery_reissue','recovery_complete',"
    "'password_reset_start','password_reset_reissue','password_reset_complete',"
    "'emergency_issue','emergency_complete'"
)


def upgrade() -> None:
    op.execute("LOCK TABLE iam_security_control IN ACCESS EXCLUSIVE MODE")
    op.execute("""ALTER TABLE iam_emergency_cases
      ADD COLUMN issuer_kind text NOT NULL DEFAULT 'operating',
      ADD COLUMN issuer_account_id uuid REFERENCES iam_accounts(id),
      ADD COLUMN approval_origin_case_id uuid,
      ADD COLUMN handoff_parent_id uuid,
      ADD CONSTRAINT emergency_identity UNIQUE(id,organization_id,account_id,factors),
      ADD CONSTRAINT emergency_parent_scope FOREIGN KEY
        (handoff_parent_id,organization_id,account_id,factors)
        REFERENCES iam_emergency_cases(id,organization_id,account_id,factors),
      ADD CONSTRAINT emergency_origin_scope FOREIGN KEY
        (approval_origin_case_id,organization_id,account_id,factors)
        REFERENCES iam_emergency_cases(id,organization_id,account_id,factors),
      ADD CONSTRAINT emergency_no_self_parent CHECK(supersedes IS NULL OR supersedes<>id);
      CREATE UNIQUE INDEX emergency_single_child ON iam_emergency_cases(supersedes)
        WHERE supersedes IS NOT NULL;
      ALTER TABLE iam_emergency_cases
        ALTER COLUMN approval_ref DROP NOT NULL, ALTER COLUMN owner_ref DROP NOT NULL,
        ALTER COLUMN executor_ref DROP NOT NULL, ALTER COLUMN executor_uid DROP NOT NULL,
        ALTER COLUMN checked_at DROP NOT NULL, ALTER COLUMN approval_valid_until DROP NOT NULL;
      DO $$ DECLARE c record; BEGIN
        FOR c IN SELECT conname FROM pg_constraint
          WHERE conrelid='iam_emergency_cases'::regclass AND contype='c'
          AND (pg_get_constraintdef(oid) LIKE '%approval_mode%'
            OR pg_get_constraintdef(oid) LIKE '%approval_valid_until%')
        LOOP EXECUTE format('ALTER TABLE iam_emergency_cases DROP CONSTRAINT %I',c.conname);
        END LOOP;
      END $$;
      ALTER TABLE iam_emergency_cases ADD CONSTRAINT emergency_issuer_variant CHECK (
        (issuer_kind='operating' AND approval_mode='manual'
         AND issuer_account_id IS NULL AND approval_origin_case_id IS NULL
         AND handoff_parent_id IS NULL
         AND approval_ref IS NOT NULL AND owner_ref IS NOT NULL
         AND executor_ref IS NOT NULL AND executor_uid IS NOT NULL
         AND checked_at IS NOT NULL AND approval_valid_until IS NOT NULL
         AND checked_at<=issued_at AND approval_valid_until>issued_at)
        OR (issuer_kind='master_handoff' AND approval_mode='current_master'
         AND issuer_account_id IS NOT NULL AND issuer_account_id<>account_id
         AND approval_origin_case_id IS NOT NULL AND approval_origin_case_id<>id
         AND supersedes IS NOT NULL AND handoff_parent_id IS NOT NULL
         AND handoff_parent_id=supersedes
         AND approval_ref IS NULL AND owner_ref IS NULL AND executor_ref IS NULL
         AND executor_uid IS NULL AND checked_at IS NULL AND approval_valid_until IS NULL));
      ALTER TABLE audit_events
        ADD COLUMN approval_origin_case_id uuid REFERENCES iam_emergency_cases(id),
        ADD COLUMN previous_case_id uuid REFERENCES iam_emergency_cases(id),
        ADD COLUMN handoff_kind text CHECK(handoff_kind IN ('takeover','reissue'));
      ALTER TABLE audit_events DROP CONSTRAINT audit_events_approval_mode_check;
      ALTER TABLE audit_events ADD CONSTRAINT audit_events_approval_mode_check
        CHECK(approval_mode IN ('manual','current_master'));
      ALTER TABLE audit_events DROP CONSTRAINT audit_events_action_check;
      ALTER TABLE audit_events DROP CONSTRAINT audit_events_emergency_check;
    """)
    op.execute(
        "ALTER TABLE audit_events ADD CONSTRAINT audit_events_action_check "
        f"CHECK(action IN ({_ACTIONS},'emergency_handoff'))"
    )
    op.execute("""ALTER TABLE audit_events ADD CONSTRAINT audit_events_emergency_check CHECK (
      (action IN ('emergency_issue','emergency_complete','emergency_handoff')
       AND organization_id IS NOT NULL AND target_id IS NOT NULL
       AND emergency_case_id IS NOT NULL AND emergency_factors IS NOT NULL
       AND actor_role IS NOT NULL AND actor_scope IS NOT NULL AND approval_mode IS NOT NULL
       AND (
        (approval_mode='manual' AND executor_ref IS NOT NULL
         AND approval_origin_case_id IS NULL AND previous_case_id IS NULL AND handoff_kind IS NULL
         AND ((action='emergency_issue' AND actor_id IS NULL
               AND actor_role='SYSTEM_RECOVERY_OPERATOR' AND actor_scope='EMERGENCY_RECOVERY')
          OR (action='emergency_complete' AND actor_id IS NOT NULL AND actor_id=target_id
               AND actor_role='RECOVERY_RECIPIENT' AND actor_scope='EMERGENCY_RECOVERY')))
        OR (approval_mode='current_master' AND executor_ref IS NULL
         AND approval_origin_case_id IS NOT NULL AND previous_case_id IS NOT NULL
         AND handoff_kind IS NOT NULL
         AND ((action='emergency_handoff' AND actor_id IS NOT NULL AND actor_id<>target_id
               AND actor_role='MASTER' AND actor_scope='ORGANIZATION')
          OR (action='emergency_complete' AND actor_id IS NOT NULL AND actor_id=target_id
               AND actor_role='RECOVERY_RECIPIENT' AND actor_scope='EMERGENCY_RECOVERY')))))
      OR (action NOT IN ('emergency_issue','emergency_complete','emergency_handoff')
       AND emergency_case_id IS NULL AND emergency_factors IS NULL AND executor_ref IS NULL
       AND approval_mode IS NULL AND approval_origin_case_id IS NULL
       AND previous_case_id IS NULL AND handoff_kind IS NULL))""")


def downgrade() -> None:
    op.execute("LOCK TABLE iam_security_control IN ACCESS EXCLUSIVE MODE")
    op.execute(
        "LOCK TABLE iam_accounts,iam_sessions,iam_passkeys,iam_emergency_cases,"
        "iam_emergency_credentials,iam_mfa_contexts,iam_security_states,audit_events "
        "IN ACCESS EXCLUSIVE MODE"
    )
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT 1 FROM iam_emergency_cases
        WHERE issuer_kind='master_handoff') OR EXISTS(SELECT 1 FROM audit_events
        WHERE approval_mode='current_master') THEN
        RAISE EXCEPTION 'Handoff history prevents downgrade'; END IF; END $$;
      ALTER TABLE audit_events DROP CONSTRAINT audit_events_emergency_check;
      ALTER TABLE audit_events DROP CONSTRAINT audit_events_action_check;
      ALTER TABLE audit_events DROP CONSTRAINT audit_events_approval_mode_check;
      ALTER TABLE audit_events ADD CONSTRAINT audit_events_approval_mode_check
        CHECK(approval_mode='manual');
      ALTER TABLE audit_events DROP COLUMN approval_origin_case_id,
        DROP COLUMN previous_case_id,DROP COLUMN handoff_kind;
      DROP INDEX emergency_single_child;
      ALTER TABLE iam_emergency_cases DROP CONSTRAINT emergency_issuer_variant;
      ALTER TABLE iam_emergency_cases DROP CONSTRAINT emergency_parent_scope;
      ALTER TABLE iam_emergency_cases DROP CONSTRAINT emergency_origin_scope;
      ALTER TABLE iam_emergency_cases DROP CONSTRAINT emergency_identity;
      ALTER TABLE iam_emergency_cases DROP CONSTRAINT emergency_no_self_parent;
      ALTER TABLE iam_emergency_cases DROP COLUMN issuer_kind,DROP COLUMN issuer_account_id,
        DROP COLUMN approval_origin_case_id,DROP COLUMN handoff_parent_id;
      ALTER TABLE iam_emergency_cases
        ALTER COLUMN approval_ref SET NOT NULL, ALTER COLUMN owner_ref SET NOT NULL,
        ALTER COLUMN executor_ref SET NOT NULL, ALTER COLUMN executor_uid SET NOT NULL,
        ALTER COLUMN checked_at SET NOT NULL, ALTER COLUMN approval_valid_until SET NOT NULL,
        ADD CHECK(approval_mode='manual'),
        ADD CHECK(checked_at<=issued_at AND approval_valid_until>issued_at);
    """)
    op.execute(
        "ALTER TABLE audit_events ADD CONSTRAINT audit_events_action_check "
        f"CHECK(action IN ({_ACTIONS}))"
    )
    op.execute("""ALTER TABLE audit_events ADD CONSTRAINT audit_events_emergency_check CHECK (
      (action IN ('emergency_issue','emergency_complete') AND emergency_case_id IS NOT NULL
        AND organization_id IS NOT NULL AND target_id IS NOT NULL
        AND emergency_factors IS NOT NULL AND executor_ref IS NOT NULL
        AND approval_mode IS NOT NULL AND actor_role IS NOT NULL AND actor_scope IS NOT NULL
        AND approval_mode='manual'
        AND ((action='emergency_issue' AND actor_id IS NULL
          AND actor_role='SYSTEM_RECOVERY_OPERATOR' AND actor_scope='EMERGENCY_RECOVERY')
          OR (action='emergency_complete' AND actor_id IS NOT NULL AND actor_id=target_id
            AND actor_role='RECOVERY_RECIPIENT' AND actor_scope='EMERGENCY_RECOVERY')))
      OR (action NOT IN ('emergency_issue','emergency_complete') AND emergency_case_id IS NULL
        AND emergency_factors IS NULL AND executor_ref IS NULL AND approval_mode IS NULL))""")
