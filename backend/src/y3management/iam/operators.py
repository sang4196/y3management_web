"""IAM-owned Operator transitions and immutable, currently authorized receipts."""

import hashlib
import hmac
import json
from dataclasses import asdict, replace
from datetime import timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import text

from y3management.contracts import Rejected
from y3management.iam.infrastructure import IAM, login_id
from y3management.iam.public import (
    Caller,
    OperatorCandidate,
    OperatorCommand,
    OperatorMutation,
    OperatorResult,
    OperatorTransitionProof,
    RoleActorSnapshot,
)


class OperatorRoles:
    def __init__(self, iam: IAM) -> None:
        self.iam = iam
        self.s = iam.s

    def lookup(self, caller: Caller, identifier: str) -> UUID:
        self._manager(caller)
        ident = self.s.execute(
            text("SELECT id FROM iam_accounts WHERE organization_id=:o AND login_id=:l"),
            {"o": caller.organization_id, "l": login_id(identifier)},
        ).scalar_one_or_none()
        if ident is None:
            raise Rejected(404, "not_found")
        return UUID(str(ident))

    def _manager(self, caller: Caller) -> None:
        if not caller.master and caller.branch_id is None:
            raise Rejected(403, "forbidden")

    def candidate(self, caller: Caller, ident: UUID, branch: UUID | None) -> OperatorCandidate:
        self._manager(caller)
        roles = self.iam.account_roles(ident)
        grant = roles.operator_grant
        work_branch = grant.scope.branch_id if grant else branch
        if (
            roles.account.organization_id != caller.organization_id
            or work_branch is None
            or (not caller.master and caller.branch_id != work_branch)
        ):
            raise Rejected(404, "not_found")
        row = self.s.execute(
            text(
                "SELECT password_hash IS NOT NULL AS ready, recovery_pending,"
                "password_reset_pending FROM iam_accounts WHERE id=:a"
            ),
            {"a": ident},
        ).one()
        ready = bool(row.ready and not row.recovery_pending and not row.password_reset_pending)
        eligible = (
            roles.account.state in ("ACTIVE", "PENDING_SETUP")
            if grant
            else (roles.account.state == "ACTIVE" and ready)
        )
        return OperatorCandidate(
            ident,
            roles.account.login_id,
            roles.account.state,
            ready,
            roles.account.version,
            grant,
            work_branch,
            eligible and not bool(grant and grant.granted),
            bool(grant and grant.granted),
            bool(caller.master and grant),
        )

    def _fingerprint(self, caller: Caller, command: OperatorCommand) -> bytes:
        return hashlib.sha256(
            json.dumps(
                {**asdict(command), "actor_id": caller.account_id, "canonical_version": 1},
                sort_keys=True,
                default=str,
            ).encode()
        ).digest()

    def _receipt(self, caller: Caller, operation: UUID) -> dict[str, Any] | None:
        self._manager(caller)
        row = (
            self.s.execute(
                text(
                    "SELECT * FROM iam_operator_role_operations WHERE organization_id=:o "
                    "AND operation_id=:i AND actor_id=:a"
                ),
                {"o": caller.organization_id, "i": operation, "a": caller.account_id},
            )
            .mappings()
            .first()
        )
        return dict(row) if row else None

    def _result(self, caller: Caller, row: dict[str, Any]) -> OperatorResult:
        current = self.candidate(caller, row["account_id"], None)
        return OperatorResult(
            row["operation_id"],
            row["changed"],
            row["granted"],
            row["committed_version"],
            row["branch_id"],
            current,
            bool(row["changed"] and caller.account_id == row["account_id"]),
        )

    def operation(self, caller: Caller, operation: UUID) -> OperatorResult:
        row = self._receipt(caller, operation)
        if row is None:
            raise Rejected(404, "not_found")
        return self._result(caller, row)

    def replay(self, caller: Caller, command: OperatorCommand) -> OperatorResult | None:
        # Scope and original ownership are always checked before returning historical facts.
        self.candidate(caller, command.account_id, command.branch_id)
        row = self._receipt(caller, command.operation_id)
        if row is None:
            return None
        if bytes(row["fingerprint"]) != self._fingerprint(caller, command):
            raise Rejected(409, "conflict")
        return replace(self._result(caller, row), reauthentication_required=False)

    def _facts(self, ident: UUID) -> dict[str, list[dict[str, Any]]]:
        facts = self.iam._password_change_facts(ident)
        for table in (
            "iam_mfa_contexts",
            "iam_recovery_credentials",
            "iam_reset_credentials",
            "iam_emergency_credentials",
            "iam_password_emergency_credentials",
        ):
            facts[table] = [
                dict(row)
                for row in self.s.execute(
                    text(f"SELECT * FROM {table} WHERE account_id=:a ORDER BY id"), {"a": ident}
                ).mappings()
            ]
        for table in (
            "iam_emergency_cases",
            "iam_password_emergency_cases",
            "iam_policy_account_transitions",
        ):
            facts[table] = [
                dict(row)
                for row in self.s.execute(
                    text(f"SELECT * FROM {table} WHERE account_id=:a ORDER BY 1"), {"a": ident}
                ).mappings()
            ]
        account = facts["iam_accounts"][0]
        budget_key = (
            bytes(account["login_budget_key"])
            if account["login_budget_key"] is not None
            else hmac.digest(self.iam.key, account["login_id"].encode(), "sha256")
        )
        for table in ("iam_budgets", "iam_attempts"):
            facts[table] = [
                dict(row)
                for row in self.s.execute(
                    text(f"SELECT * FROM {table} WHERE key=:k ORDER BY 1"), {"k": budget_key}
                ).mappings()
            ]
        return facts

    def change(
        self, caller: Caller, command: OperatorCommand
    ) -> tuple[OperatorResult, OperatorMutation | None]:
        before = self.candidate(caller, command.account_id, command.branch_id)
        grant = before.operator_grant
        version = grant.scope.version if grant else 0
        if (
            before.account_version != command.expected_account_version
            or version != command.expected_operator_version
        ):
            raise Rejected(409, "conflict")
        destination = before.branch_id
        granted = bool(grant and grant.granted)
        kind = "add" if grant is None else ("regrant" if command.desired_granted else "revoke")
        if command.action == "move":
            self.iam.require_master(caller)
            if not grant or command.branch_id is None:
                raise Rejected(409, "conflict")
            destination = command.branch_id
            desired = grant.granted
            changed = destination != before.branch_id
            kind = "move"
        else:
            if grant and command.branch_id is not None and command.branch_id != before.branch_id:
                raise Rejected(409, "conflict")
            desired = command.desired_granted
            if grant is None and not desired:
                raise Rejected(404, "not_found")
            changed = granted != desired
            if changed and desired and not before.can_grant:
                raise Rejected(409, "conflict")
        mutation = None
        if changed:
            expected = self._facts(command.account_id)
            new_grant = dict(
                account_id=command.account_id,
                organization_id=caller.organization_id,
                branch_id=destination,
                granted=desired,
                version=version + 1,
            )
            expected["iam_operator_grants"] = [new_grant]
            for session in expected["iam_sessions"]:
                session["revoked"] = True
            sources = [
                "iam_operator_setup_credentials",
                "iam_trainer_setup_credentials",
                "iam_mfa_contexts",
            ]
            if command.action == "move":
                sources += [
                    "iam_credentials",
                    "iam_recovery_credentials",
                    "iam_reset_credentials",
                    "iam_emergency_credentials",
                    "iam_password_emergency_credentials",
                ]
            for table in sources:
                for row in expected[table]:
                    row["consumed"] = True
                    if table == "iam_mfa_contexts":
                        row["password_hash"] = None
            proof = OperatorTransitionProof(
                command.account_id, self.iam._password_change_digest(expected)
            )
            self.s.execute(
                text("""INSERT INTO iam_operator_grants
                (account_id,organization_id,branch_id,granted,version) VALUES
                (:account_id,:organization_id,:branch_id,:granted,:version)
                ON CONFLICT(account_id) DO UPDATE SET branch_id=excluded.branch_id,
                granted=excluded.granted,version=excluded.version"""),
                new_grant,
            )
            self.s.execute(
                text("UPDATE iam_sessions SET revoked=true WHERE account_id=:a"),
                {"a": command.account_id},
            )
            for table in sources:
                extra = ",password_hash=NULL" if table == "iam_mfa_contexts" else ""
                self.s.execute(
                    text(f"UPDATE {table} SET consumed=true{extra} WHERE account_id=:a"),
                    {"a": command.account_id},
                )
            after = self.candidate(caller, command.account_id, None)
            mutation = OperatorMutation(before, after, kind, proof)
            version += 1
        self.s.execute(
            text("""INSERT INTO iam_operator_role_operations
            (organization_id,operation_id,account_id,actor_id,fingerprint,action,changed,granted,branch_id,committed_version)
            VALUES(:o,:i,:a,:actor,:f,:action,:changed,:g,:b,:v)"""),
            {
                "o": caller.organization_id,
                "i": command.operation_id,
                "a": command.account_id,
                "actor": caller.account_id,
                "f": self._fingerprint(caller, command),
                "action": command.action,
                "changed": changed,
                "g": desired,
                "b": destination,
                "v": version,
            },
        )
        return self.operation(caller, command.operation_id), mutation

    def actor_proof(self, ident: UUID) -> OperatorTransitionProof:
        return OperatorTransitionProof(ident, self.iam._password_change_digest(self._facts(ident)))

    def verify_actor(self, proof: OperatorTransitionProof) -> None:
        if self.iam._password_change_digest(self._facts(proof.account_id)) != proof.expected_digest:
            raise Rejected(401, "unauthorized")

    def confirm(self, mutation: OperatorMutation) -> None:
        proof = mutation.proof
        if self.iam._password_change_digest(self._facts(proof.account_id)) != proof.expected_digest:
            raise Rejected(409, "conflict")

    def confirm_self(self, snapshot: RoleActorSnapshot, mutation: OperatorMutation) -> None:
        auth = snapshot.authentication
        self.iam.check_policy(snapshot.policy)
        if auth.caller.account_id != mutation.proof.account_id:
            raise Rejected(401, "unauthorized")
        self.confirm(mutation)
        now = self.iam.now()
        if snapshot.expires_at <= now or snapshot.last_activity + timedelta(minutes=30) <= now:
            raise Rejected(401, "unauthorized")
