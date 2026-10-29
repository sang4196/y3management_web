"""IAM-owned role transitions. Identity bindings and administrator factors survive withdrawal."""

import hashlib
import json
from dataclasses import asdict
from datetime import timedelta
from uuid import UUID

from sqlalchemy import text

from y3management.contracts import Rejected
from y3management.iam.infrastructure import IAM, login_id
from y3management.iam.public import (
    Authentication,
    Caller,
    RoleActorSnapshot,
    TrainerRoleCandidate,
    TrainerRoleChange,
    TrainerRoleRequest,
    TrainerRoleResult,
    TrainerRoleState,
)


class TrainerRoles:
    def __init__(self, iam: IAM) -> None:
        self.iam = iam
        self.s = iam.s

    def lock(self, ident: UUID) -> None:
        # Account and every affected session are held before credential/context locks.
        for table in (
            "iam_credentials",
            "iam_mfa_contexts",
            "iam_recovery_credentials",
            "iam_reset_credentials",
            "iam_emergency_credentials",
            "iam_trainer_setup_credentials",
        ):
            self.s.execute(
                text(f"SELECT id FROM {table} WHERE account_id=:a ORDER BY id FOR UPDATE"),
                {"a": ident},
            ).all()
        for table in ("iam_trainer_role_grants", "iam_trainer_bindings"):
            self.s.execute(
                text(f"SELECT account_id FROM {table} WHERE account_id=:a FOR UPDATE"), {"a": ident}
            ).all()

    def state(self, organization: UUID, trainer: UUID) -> TrainerRoleState:
        binding = self.iam.trainer_binding(organization, trainer)
        if binding is None:
            return TrainerRoleState(trainer, None, None, None, None, False, 0)
        roles = self.iam.account_roles(binding.account_id)
        return TrainerRoleState(
            trainer,
            binding.account_id,
            roles.account.login_id,
            roles.account.state,
            roles.account.version,
            roles.trainer_granted,
            roles.trainer_role_epoch,
        )

    def ready(self, ident: UUID) -> bool:
        roles = self.iam.account_roles(ident)
        row = self.s.execute(
            text(
                "SELECT state,password_hash IS NOT NULL AS password_ready,"
                "recovery_pending,password_reset_pending FROM iam_accounts WHERE id=:a"
            ),
            {"a": ident},
        ).one()
        return bool(
            row.state == "ACTIVE"
            and row.password_ready
            and not row.recovery_pending
            and not row.password_reset_pending
            and roles.admin
            and self.s.execute(
                text("SELECT 1 FROM iam_passkeys WHERE account_id=:a AND revoked_at IS NULL"),
                {"a": ident},
            ).first()
        )

    def lookup(self, organization: UUID, trainer: UUID, identifier: str) -> TrainerRoleCandidate:
        row = self.s.execute(
            text("SELECT id FROM iam_accounts WHERE organization_id=:o AND login_id=:l"),
            {"o": organization, "l": login_id(identifier)},
        ).first()
        if row is None:
            raise Rejected(404, "not_found")
        roles = self.iam.account_roles(row.id)
        if roles.binding is not None and roles.binding.trainer_id != trainer:
            raise Rejected(409, "conflict")
        return TrainerRoleCandidate(
            row.id,
            roles.account.login_id,
            roles.account.state,
            roles.account.version,
            roles.trainer_role_epoch,
            self.ready(row.id)
            if roles.binding is None
            else roles.account.state in ("ACTIVE", "PENDING_SETUP"),
        )

    def operation(self, organization: UUID, operation: UUID) -> TrainerRoleResult | None:
        row = (
            self.s.execute(
                text(
                    "SELECT * FROM iam_trainer_role_operations "
                    "WHERE organization_id=:o AND operation_id=:i"
                ),
                {"o": organization, "i": operation},
            )
            .mappings()
            .first()
        )
        if row is None:
            return None
        return TrainerRoleResult(
            operation,
            row["changed"],
            row["granted"],
            row["committed_role_version"],
            self.state(organization, row["trainer_id"]),
        )

    def stable_actor(self, authentication: Authentication) -> bytes:
        ident = authentication.caller.account_id
        account = (
            self.s.execute(
                text(
                    "SELECT id,organization_id,state,row_version,security_version,"
                    "recovery_pending,password_reset_pending,key_set_version "
                    "FROM iam_accounts WHERE id=:a"
                ),
                {"a": ident},
            )
            .mappings()
            .one()
        )
        session = (
            self.s.execute(
                text(
                    "SELECT id,account_id,digest,csrf,security_version,"
                    "trainer_role_epoch,created_at,last_activity,expires_at,assurance "
                    "FROM iam_sessions WHERE id=:i"
                ),
                {"i": authentication.session_id},
            )
            .mappings()
            .one()
        )
        roles = self.iam.account_roles(ident)
        keys = (
            self.s.execute(
                text(
                    "SELECT key_id FROM iam_passkeys WHERE account_id=:a "
                    "AND revoked_at IS NULL ORDER BY key_id"
                ),
                {"a": ident},
            )
            .scalars()
            .all()
        )
        return hashlib.sha256(
            json.dumps(
                [dict(account), dict(session), asdict(roles.account), keys],
                sort_keys=True,
                default=str,
            ).encode()
        ).digest()

    def snapshot(self, authentication: Authentication) -> RoleActorSnapshot:
        row = self.s.execute(
            text("SELECT last_activity,expires_at FROM iam_sessions WHERE id=:i"),
            {"i": authentication.session_id},
        ).one()
        return RoleActorSnapshot(
            authentication,
            self.stable_actor(authentication),
            self.iam.account_roles(authentication.caller.account_id).trainer_role_epoch,
            row.last_activity,
            row.expires_at,
        )

    def confirm_actor(self, snapshot: RoleActorSnapshot, *, self_change: bool) -> None:
        auth = snapshot.authentication
        revoked = self.s.execute(
            text("SELECT revoked FROM iam_sessions WHERE id=:i"), {"i": auth.session_id}
        ).scalar_one()
        epoch = self.iam.account_roles(auth.caller.account_id).trainer_role_epoch
        stable_digest = self.stable_actor(auth)
        now = self.iam.now()
        if (
            stable_digest != snapshot.stable_digest
            or revoked != self_change
            or epoch != snapshot.role_epoch + int(self_change)
            or snapshot.expires_at <= now
            or snapshot.last_activity + timedelta(minutes=30) <= now
        ):
            raise Rejected(401, "unauthorized")

    def change(
        self,
        caller: Caller,
        trainer: UUID,
        home: UUID,
        active: bool,
        trainer_version: int,
        request: TrainerRoleRequest,
    ) -> tuple[TrainerRoleResult, TrainerRoleChange | None]:
        if not caller.master and caller.branch_id != home:
            raise Rejected(404, "not_found")
        payload = {**asdict(request), "trainer_id": trainer, "canonical_version": 1}
        fingerprint = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode()
        ).digest()
        old = self.s.execute(
            text(
                "SELECT fingerprint FROM iam_trainer_role_operations "
                "WHERE organization_id=:o AND operation_id=:i"
            ),
            {"o": caller.organization_id, "i": request.operation_id},
        ).first()
        if old:
            if bytes(old.fingerprint) != fingerprint:
                raise Rejected(409, "conflict")
            result = self.operation(caller.organization_id, request.operation_id)
            assert result is not None
            return result, None
        roles = self.iam.account_roles(request.account_id)
        binding = self.iam.trainer_binding(caller.organization_id, trainer)
        if roles.account.organization_id != caller.organization_id:
            raise Rejected(404, "not_found")
        if (binding is not None and binding.account_id != request.account_id) or (
            roles.binding is not None and roles.binding.trainer_id != trainer
        ):
            raise Rejected(409, "conflict")
        first = binding is None
        if (
            roles.account.version != request.expected_account_version
            or roles.trainer_role_epoch != request.expected_role_version
            or trainer_version != request.expected_trainer_version
        ):
            raise Rejected(409, "conflict")
        if first and not request.desired_granted:
            raise Rejected(404, "not_found")
        changed = roles.trainer_granted != request.desired_granted
        if first and request.identity_confirmed is not True:
            raise Rejected(422, "identity_confirmation_required")
        if changed and request.desired_granted:
            if not active or roles.account.state not in ("ACTIVE", "PENDING_SETUP"):
                raise Rejected(409, "conflict")
            if first and not self.ready(request.account_id):
                raise Rejected(409, "conflict")
        change = None
        version = roles.trainer_role_epoch
        if changed:
            if first:
                self.s.execute(
                    text(
                        "INSERT INTO iam_trainer_bindings "
                        "(account_id,organization_id,trainer_id) VALUES(:a,:o,:t)"
                    ),
                    {"a": request.account_id, "o": caller.organization_id, "t": trainer},
                )
            version += 1
            self.s.execute(
                text("UPDATE iam_accounts SET trainer_role_epoch=:v WHERE id=:a"),
                {"v": version, "a": request.account_id},
            )
            self.s.execute(
                text(
                    "INSERT INTO iam_trainer_role_grants "
                    "(account_id,organization_id,trainer_id,granted,role_version,origin) "
                    "VALUES(:a,:o,:t,:g,:v,'i2_link') ON CONFLICT(account_id) DO UPDATE "
                    "SET granted=EXCLUDED.granted,role_version=EXCLUDED.role_version,"
                    "changed_at=clock_timestamp()"
                ),
                {
                    "a": request.account_id,
                    "o": caller.organization_id,
                    "t": trainer,
                    "g": request.desired_granted,
                    "v": version,
                },
            )
            self.s.execute(
                text("UPDATE iam_sessions SET revoked=true WHERE account_id=:a"),
                {"a": request.account_id},
            )
            self.s.execute(
                text(
                    "UPDATE iam_mfa_contexts SET consumed=true,password_hash=NULL "
                    "WHERE account_id=:a"
                ),
                {"a": request.account_id},
            )
            self.s.execute(
                text("UPDATE iam_trainer_setup_credentials SET consumed=true WHERE account_id=:a"),
                {"a": request.account_id},
            )
            security = self.s.execute(
                text("SELECT security_version FROM iam_accounts WHERE id=:a"),
                {"a": request.account_id},
            ).scalar_one()
            change = TrainerRoleChange(
                "add" if first else ("regrant" if request.desired_granted else "revoke"),
                roles.trainer_granted,
                request.desired_granted,
                version - 1,
                version,
                roles.account.version,
                int(security),
            )
        self.s.execute(
            text(
                "INSERT INTO iam_trainer_role_operations "
                "(organization_id,operation_id,trainer_id,account_id,actor_id,target_home,fingerprint,"
                "changed,granted,committed_role_version) VALUES(:o,:i,:t,:a,:actor,:h,:f,:c,:g,:v)"
            ),
            {
                "o": caller.organization_id,
                "i": request.operation_id,
                "t": trainer,
                "a": request.account_id,
                "actor": caller.account_id,
                "h": home,
                "f": fingerprint,
                "c": changed,
                "g": request.desired_granted,
                "v": version,
            },
        )
        result = self.operation(caller.organization_id, request.operation_id)
        assert result is not None
        return result, change

    def confirm_change(self, result: TrainerRoleResult, change: TrainerRoleChange) -> None:
        current = result.current_state
        assert current.account_id is not None
        roles = self.iam.account_roles(current.account_id)
        if (
            roles.account.version != current.account_version
            or roles.account.state != current.state
            or roles.account.login_id != current.login_id
            or self.s.execute(
                text("SELECT security_version FROM iam_accounts WHERE id=:a"),
                {"a": current.account_id},
            ).scalar_one()
            != change.security_version
            or roles.binding is None
            or roles.binding.trainer_id != current.trainer_id
            or roles.trainer_role_epoch != result.committed_role_version
            or roles.trainer_granted != result.committed_granted
        ):
            raise Rejected(409, "conflict")
