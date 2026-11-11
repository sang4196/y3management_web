"""Application orchestration: one business commit, with required audit in the same UoW."""

import logging
import re
from collections.abc import Callable
from dataclasses import asdict, replace
from typing import Literal
from uuid import UUID

from y3management.audit.public import (
    Event,
    InitialCompensationSet,
    OperatorAccountEvent,
    OperatorRoleEvent,
    PasswordEmergencyEvent,
    TrainerIdentityEvent,
    TrainerRegistered,
    TrainerRoleEvent,
    TrainerStateEvent,
)
from y3management.contracts import CommitPhase, HashAdmissionRejected, Rejected
from y3management.iam.public import (
    Account,
    AccountRoles,
    Authentication,
    Caller,
    EmergencyRequest,
    EmergencySnapshot,
    EmergencyView,
    HandoffRequest,
    HandoffState,
    IdentityTransition,
    LifecycleAccount,
    OperatingRecoveryAuthority,
    OperatorCandidate,
    OperatorCommand,
    OperatorResult,
    OperatorScope,
    Preparation,
    Reservation,
    ResetState,
    Setup,
    TrainerAccountState,
    TrainerOperation,
    TrainerRoleCandidate,
    TrainerRoleRequest,
    TrainerRoleResult,
    TrainerRoleState,
)
from y3management.organization.public import AssignmentCandidate, Branch, BranchPage
from y3management.uow import UnitOfWork, Work
from y3management.workforce.public import (
    ManagedTrainer,
    RegisterTrainer,
    RegistrationResult,
    TrainerIdentityFact,
    TrainerPage,
    TrainerStateRequest,
    TrainerStateResult,
)


def normalize_login(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{2,63}", value):
        raise Rejected(422, "invalid_request")
    return value.lower()


def event(
    action: str,
    caller: Caller,
    target: UUID,
    before: Account | None = None,
    after: Account | None = None,
    branch: Branch | None = None,
) -> Event:
    return Event(
        action,
        caller.organization_id,
        caller.account_id,
        target,
        before_state=before.state if before else None,
        after_state=after.state if after else None,
        before_branch=before.branch_id if before else None,
        after_branch=after.branch_id if after else None,
        actor_role="MASTER" if caller.master else "BRANCH_ADMIN",
        actor_scope="ORGANIZATION" if caller.master else "BRANCH",
        actor_branch=caller.branch_id,
        before_version=before.version if before else None,
        after_version=after.version if after else None,
        branch_code=branch.code if branch else None,
        branch_name=branch.name if branch else None,
        before_login_id=before.login_id if before and action == "login_id_change" else None,
        after_login_id=after.login_id if after and action == "login_id_change" else None,
    )


class Service:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def bootstrap(
        self,
        name: str,
        identifier: str,
        password: str,
    ) -> Account:
        identifier = normalize_login(identifier)
        if not name or len(name) > 128:
            raise Rejected(422, "invalid_request")
        with self.uow.open() as w:
            w.iam.prepare_master(identifier, password)
            w.iam.ensure_uninstalled()
            org = w.organization.create_initial(name)
            account = w.iam.bootstrap(org, identifier)
            w.audit.append(
                Event(
                    "bootstrap",
                    org,
                    None,
                    account.id,
                    actor_role="INSTALLER",
                    actor_scope="INSTALLATION",
                    after_state=account.state,
                    after_version=account.version,
                )
            )
            return account

    def csrf(self, auth: str | None, preauth: str | None) -> tuple[str, str | None]:
        if auth:
            try:
                with self.uow.open() as w:
                    a, _ = self._current_principal(w, auth)
                    return a.csrf, None
            except Rejected as error:
                if error.status != 401:
                    raise
        with self.uow.open() as w:
            p: Preparation = w.security.preparation(preauth)
            return p.csrf, p.token

    def login(
        self,
        identifier: str,
        password: str,
        preauth: str | None,
        nonce: str | None,
        auth: str | None,
    ) -> str:
        if auth:
            try:
                with self.uow.open() as w:
                    current, _ = self._current_principal(w, auth)
                    w.iam.csrf(current, nonce)
            except Rejected as error:
                if error.status != 401:
                    raise
            else:
                raise Rejected(409, "logout_required")
        identifier = normalize_login(identifier)
        with self.uow.open() as w:
            preauth_deadline = w.iam.preparation(preauth, nonce)
            w.iam.gc_sessions()
        with self.uow.open(commit_denial=True) as w:
            reservation = w.security.reserve(identifier)
        sid = None
        subject = None
        delivered = False
        try:
            with self.uow.open() as w:
                subject = w.iam.login_subject(identifier)
                if subject is not None and subject.id != reservation.account_id:
                    subject = None
                proof = w.iam.verify_login(identifier, password, reservation)
                if proof is None:
                    raise Rejected(401, "invalid_credentials")
                with self.uow.open() as security:
                    sid = security.security.allocate("session_slot")
                roles = w.iam.lock_login(proof.account_id)
                if roles.admin or roles.operator:
                    fact = None
                elif roles.binding is not None and roles.trainer_granted:
                    w.iam.preparation(preauth, nonce)
                    fact = w.workforce.lock_identity(
                        roles.account.organization_id, roles.binding.trainer_id
                    )
                    if not fact.active:
                        raise Rejected(401, "invalid_credentials")
                else:
                    raise Rejected(401, "invalid_credentials")
                token, account = w.iam.login(proof, sid, preauth, nonce, reservation)
                if roles.operator:
                    self._operator_event(
                        w,
                        "login",
                        roles.operator,
                        account,
                        account,
                        Caller(
                            account.id,
                            account.organization_id,
                            account.branch_id,
                            account.master,
                            roles.operator,
                        ),
                    )
                elif fact is not None:
                    self._identity_audit(w, "login", w.iam.identity_transition(account.id), fact)
                else:
                    caller = Caller(
                        account.id, account.organization_id, account.branch_id, account.master
                    )
                    w.audit.append(event("login", caller, account.id))
                if w.iam.account_roles(account.id) != roles:
                    raise Rejected(401, "invalid_credentials")
                if (
                    fact
                    and w.workforce.lock_identity(account.organization_id, fact.trainer_id) != fact
                ):
                    raise Rejected(401, "invalid_credentials")
                w.iam.confirm_login(proof, reservation, sid)
                assert reservation.lease_until
                w.iam.confirm_preparation(
                    preauth, nonce, deadline=min(reservation.lease_until, preauth_deadline)
                )
            with self.uow.open() as security:
                security.security.finish(reservation, True)
            delivered = True
            return token
        except HashAdmissionRejected:
            self._cancel_login(reservation, sid)
            raise
        except Rejected as error:
            if error.status == 401:
                with self.uow.open() as security:
                    security.security.finish(reservation, False)
                    security.audit.append(
                        Event(
                            "login",
                            subject.organization_id if subject else None,
                            None,
                            subject.id if subject else None,
                            success=False,
                            actor_role="LOGIN_ATTEMPT",
                        )
                    )
            raise
        finally:
            if sid is not None and not delivered:
                assert proof is not None
                # Even COMMIT ACK loss may have persisted the unreturned session.
                # Match the admitted attempt and policy before revoking an undelivered cookie.
                try:
                    with self.uow.open() as cleanup:
                        cleanup.iam.revoke_undelivered_session(
                            sid,
                            attempt_id=reservation.id,
                            account_id=proof.account_id,
                            policy=proof.policy,
                        )
                except Exception:
                    logging.getLogger(__name__).warning("session_revocation_deferred")
                self._release_login_slot(sid)

    def _release_login_slot(self, sid: UUID | None) -> None:
        # Verification may have begun: preserve the reservation for conservative lease handling.
        if sid is not None:
            try:
                with self.uow.open() as w:
                    w.security.release(sid, collect=False)
            except Exception:
                logging.getLogger("y3management").warning("security_cleanup_deferred")

    def _cancel_login(self, reservation: Reservation, sid: UUID | None) -> None:
        try:
            with self.uow.open() as w:
                w.security.cancel(reservation)
                if sid is not None:
                    w.security.release(sid, collect=False)
        except Exception:
            logging.getLogger("y3management").warning("security_cleanup_deferred")

    def me(self, auth: str | None) -> Caller:
        with self.uow.open() as w:
            a, _ = self._current_principal(w, auth)
            return a.caller

    def principal(self, auth: str | None) -> tuple[Caller, TrainerIdentityFact | None]:
        with self.uow.open() as w:
            a, fact = self._current_principal(w, auth)
            return a.caller, fact

    def branches(self, auth: str | None, offset: int, limit: int) -> BranchPage:
        with self.uow.open() as w:
            c = w.iam.authenticate(auth).caller
            if not c.master and c.branch_id is None:
                raise Rejected(403, "forbidden")
            return w.organization.list_branches(c, offset, limit)

    def branch(self, auth: str | None, ident: UUID) -> Branch:
        with self.uow.open() as w:
            c = w.iam.authenticate(auth).caller
            if not c.master and c.branch_id is None:
                raise Rejected(403, "forbidden")
            return w.organization.get_branch(c, ident)

    def create_branch(self, auth: str | None, nonce: str | None, code: str, name: str) -> Branch:
        with self.uow.open() as w:
            a = w.iam.authenticate(auth, management=True, touch=False)
            w.iam.csrf(a, nonce)
            actor_snapshot = w.roles.snapshot(a)
            w.iam.require_master(a.caller)
            b = w.organization.create_branch(a.caller, code, name)
            w.audit.append(event("branch_create", a.caller, b.id, branch=b))
            w.roles.confirm_actor(actor_snapshot, self_change=False, touch=True)
            return b

    def operator_candidate(
        self,
        auth: str | None,
        target: UUID | str,
        branch: UUID | None,
        nonce: str | None = None,
        *,
        expected_actor: UUID,
    ) -> OperatorCandidate:
        if isinstance(target, str):
            with self.uow.open() as w:
                actor = w.iam.authenticate(auth, touch=False)
                if actor.caller.account_id != expected_actor:
                    raise Rejected(409, "actor_changed")
                w.iam.csrf(actor, nonce)
                ident = w.operators.lookup(actor.caller, normalize_login(target))
        else:
            ident = target
        with self.uow.open() as w:
            actor = w.iam.authenticate(auth, management=True, target=ident, touch=False)
            if actor.caller.account_id != expected_actor:
                raise Rejected(409, "actor_changed")
            snapshot = w.roles.snapshot(actor)
            result = w.operators.candidate(actor.caller, ident, branch)
            if isinstance(target, str) and result.login_id != normalize_login(target):
                raise Rejected(404, "not_found")
            w.organization.lock_scoped_branch(actor.caller, result.branch_id)
            w.roles.confirm_actor(snapshot, self_change=False, touch=True)
            return result

    def operator_operation(
        self, auth: str | None, operation: UUID, *, expected_actor: UUID
    ) -> OperatorResult:
        with self.uow.open() as w:
            actor = w.iam.authenticate(auth, touch=False)
            if actor.caller.account_id != expected_actor:
                raise Rejected(409, "actor_changed")
            ident = w.operators.operation(actor.caller, operation).current.account_id
        with self.uow.open() as w:
            actor = w.iam.authenticate(auth, management=True, target=ident, touch=False)
            if actor.caller.account_id != expected_actor:
                raise Rejected(409, "actor_changed")
            snapshot = w.roles.snapshot(actor)
            result = replace(
                w.operators.operation(actor.caller, operation), reauthentication_required=False
            )
            w.roles.confirm_actor(snapshot, self_change=False, touch=True)
            return result

    def change_operator(
        self,
        auth: str | None,
        nonce: str | None,
        command: OperatorCommand,
        *,
        expected_actor: UUID,
    ) -> OperatorResult:
        with self.uow.open() as w:
            actor = w.iam.authenticate(
                auth, management=True, target=command.account_id, touch=False
            )
            if actor.caller.account_id != expected_actor:
                raise Rejected(409, "actor_changed")
            w.iam.csrf(actor, nonce)
            snapshot = w.roles.snapshot(actor)
            actor_proof = w.operators.actor_proof(actor.caller.account_id)
            w.roles.lock(command.account_id)
            before = w.operators.candidate(actor.caller, command.account_id, command.branch_id)
            if command.action == "move":
                w.iam.require_master(actor.caller)
            replay = w.operators.replay(actor.caller, command)
            if replay is not None:
                w.operators.verify_actor(actor_proof)
                w.roles.confirm_actor(snapshot, self_change=False)
                return replay
            branch = command.branch_id if command.action == "move" else before.branch_id
            assert branch is not None
            fact = w.organization.lock_scoped_branch(actor.caller, branch)
            grant = before.operator_grant
            changing_assignment = (command.action == "move" and branch != before.branch_id) or (
                command.action == "role"
                and command.desired_granted
                and not (grant and grant.granted)
            )
            if changing_assignment:
                w.organization.require_assignable(fact)
            w.roles.confirm_actor(snapshot, self_change=False)
            w.operators.verify_actor(actor_proof)
            result, mutation = w.operators.change(actor.caller, command)
            if mutation:
                after = mutation.after
                old = before.operator_grant
                new = after.operator_grant
                assert new is not None
                w.audit.append_operator_role(
                    OperatorRoleEvent(
                        actor.caller.organization_id,
                        command.operation_id,
                        command.account_id,
                        actor.caller.account_id,
                        "MASTER" if actor.caller.master else "BRANCH_ADMIN",
                        None if actor.caller.master else actor.caller.branch_id,
                        mutation.kind,
                        bool(old and old.granted),
                        new.granted,
                        old.scope.branch_id if old else None,
                        new.scope.branch_id,
                        old.scope.version if old else 0,
                        new.scope.version,
                        after.state,
                        after.account_version,
                    )
                )
                w.operators.confirm(mutation)
            w.organization.confirm_scoped_branch(actor.caller, fact)
            if mutation and actor.caller.account_id == command.account_id:
                w.operators.confirm_self(snapshot, mutation)
            else:
                w.operators.verify_actor(actor_proof)
                w.roles.confirm_actor(snapshot, self_change=False, touch=mutation is not None)
            return result

    def operator_branch(self, auth: str | None, ident: UUID) -> Branch:
        with self.uow.open() as w:
            actor, _ = self._current_principal(w, auth)
            snapshot = w.roles.snapshot(actor)
            branch = w.organization.operator_branch(actor.caller, ident)
            w.roles.confirm_actor(snapshot, self_change=False, touch=True)
            return branch

    def _operator_event(
        self,
        w: Work,
        kind: str,
        scope: OperatorScope,
        before: Account | None,
        after: Account,
        actor: Caller | None,
    ) -> None:
        role = "CREDENTIAL_HOLDER"
        actor_branch = None
        if actor:
            if actor.master:
                role = "MASTER"
            elif actor.branch_id:
                role, actor_branch = "BRANCH_ADMIN", actor.branch_id
            elif actor.operator:
                role, actor_branch = "OPERATOR", actor.operator.branch_id
            else:
                raise Rejected(403, "forbidden")
        w.audit.append_operator(
            OperatorAccountEvent(
                kind,
                after.organization_id,
                after.id,
                scope.branch_id,
                actor.account_id if actor else None,
                role,
                actor_branch,
                before.state if before else None,
                after.state,
                before.version if before else None,
                after.version,
            )
        )

    def read_operator(
        self, auth: str | None, target: str | UUID, nonce: str | None = None
    ) -> AccountRoles:
        with self.uow.open() as w:
            actor = w.iam.authenticate(
                auth,
                management=True,
                touch=False,
                target=target if isinstance(target, UUID) else None,
            )
            snapshot = w.roles.snapshot(actor)
            if isinstance(target, str):
                w.iam.csrf(actor, nonce)
            result = w.iam.operator_target(actor.caller, target)
            w.roles.confirm_actor(snapshot, self_change=False, touch=True)
            return result

    def issue_operator(
        self,
        auth: str | None,
        nonce: str | None,
        *,
        identifier: str | None = None,
        branch: UUID | None = None,
        target: UUID | None = None,
        expected: int | None = None,
        expected_operator: int | None = None,
    ) -> tuple[AccountRoles, Setup]:
        with self.uow.open() as w:
            actor = w.iam.authenticate(auth, touch=False)
            w.iam.csrf(actor, nonce)
        with self.uow.open() as w:
            slot = w.security.allocate("credential")
        try:
            with self.uow.open() as w:
                actor = w.iam.authenticate(auth, management=True, target=target, touch=False)
                w.iam.csrf(actor, nonce)
                snapshot = w.roles.snapshot(actor)
                before = None
                branch_fact = None
                if target is None:
                    assert identifier is not None and branch is not None
                    branch_fact = w.organization.lock_scoped_branch(actor.caller, branch)
                    w.organization.require_assignable(branch_fact)
                    account = w.iam.issue_operator(
                        actor.caller, normalize_login(identifier), branch
                    )
                    target_id = account.id
                else:
                    target_id = target
                    w.iam.lock_trainer_credentials(target_id)
                    target_roles = w.iam.operator_target(actor.caller, target_id)
                    before = target_roles.account
                    if (
                        before.version != expected
                        or target_roles.operator is None
                        or target_roles.operator.version != expected_operator
                    ):
                        raise Rejected(409, "conflict")
                roles = w.iam.operator_target(actor.caller, target_id)
                setup = w.iam.operator_setup(roles, slot, before is not None)
                result = w.iam.operator_target(actor.caller, target_id)
                assert result.operator
                self._operator_event(
                    w,
                    "issue" if before is None else "reissue",
                    result.operator,
                    before,
                    result.account,
                    actor.caller,
                )
                if branch_fact:
                    w.organization.confirm_scoped_branch(actor.caller, branch_fact)
                source = w.iam.operator_source(setup.token, False)
                if (
                    source.id != slot
                    or source.account != result.account
                    or source.operator != result.operator
                    or source.expires_at != setup.expires_at
                ):
                    raise Rejected(409, "conflict")
                w.roles.confirm_actor(
                    snapshot, self_change=False, touch=True, deadline=source.expires_at
                )
                return result, setup
        except Exception:
            self._release_login_slot(slot)
            raise

    def complete_operator(
        self, token: str, password: str, preauth: str | None, nonce: str | None
    ) -> None:
        with self.uow.open() as w:
            preauth_deadline = w.iam.preparation(preauth, nonce)
        with self.uow.open() as w:
            proof = w.iam.complete_operator(token, password, preauth, nonce)
            after = w.iam.operator_source(token, True)
            self._operator_event(
                w, "setup_complete", proof.operator, proof.account, after.account, None
            )
            final = w.iam.operator_source(token, True)
            if (
                final != after
                or final.security_version != proof.security_version
                or final.account.version != proof.account.version + 1
                or final.id != proof.id
                or final.expires_at != proof.expires_at
                or final.operator != proof.operator
                or final.policy != proof.policy
            ):
                raise Rejected(400, "invalid_setup")
            w.iam.confirm_preparation(
                preauth, nonce, deadline=min(preauth_deadline, proof.expires_at)
            )

    def issue(
        self, auth: str | None, nonce: str | None, identifier: str, branch: UUID
    ) -> tuple[Account, Setup]:
        identifier = normalize_login(identifier)
        with self.uow.open() as w:
            state_id = w.security.allocate("credential")
        try:
            with self.uow.open() as w:
                a = w.iam.authenticate(auth, management=True, touch=False)
                w.iam.csrf(a, nonce)
                actor_snapshot = w.roles.snapshot(a)
                w.iam.require_master(a.caller)
                w.organization.require_branch(a.caller, branch)
                account = w.iam.issue(a.caller, identifier, branch)
                account, setup = w.iam.setup(account, state_id, reissue=False)
                w.audit.append(event("account_issue", a.caller, account.id, after=account))
                w.roles.confirm_actor(actor_snapshot, self_change=False, touch=True)
                return account, setup
        except Exception:
            try:
                with self.uow.open() as w:
                    w.security.release(state_id)
            except Exception:
                logging.getLogger("y3management").warning("security_cleanup_deferred")
            raise

    def get_account(self, auth: str | None, ident: UUID) -> Account:
        with self.uow.open() as w:
            return w.iam.scoped_account(w.iam.authenticate(auth).caller, ident)

    def lookup(self, auth: str | None, nonce: str | None, identifier: str) -> Account:
        with self.uow.open() as w:
            a = w.iam.authenticate(auth)
            w.iam.csrf(a, nonce)
            return w.iam.lookup(a.caller, normalize_login(identifier))

    def reissue(
        self, auth: str | None, nonce: str | None, ident: UUID, version: int
    ) -> tuple[Account, Setup]:
        with self.uow.open() as w:
            state_id = w.security.allocate("credential")
        try:
            with self.uow.open() as w:
                a = w.iam.authenticate(auth, management=True, target=ident, touch=False)
                w.iam.csrf(a, nonce)
                actor_snapshot = w.roles.snapshot(a)
                before = w.iam.scoped_account(a.caller, ident)
                if before.version != version:
                    raise Rejected(409, "conflict")
                after, setup = w.iam.setup(before, state_id, reissue=True)
                w.audit.append(event("setup_reissue", a.caller, ident, before, after))
                w.roles.confirm_actor(actor_snapshot, self_change=False, touch=True)
                return after, setup
        except Exception:
            try:
                with self.uow.open() as w:
                    w.security.release(state_id)
            except Exception:
                logging.getLogger("y3management").warning("security_cleanup_deferred")
            raise

    def complete(self, token: str, password: str, preauth: str | None, nonce: str | None) -> None:
        with self.uow.open() as w:
            w.iam.preparation(preauth, nonce)
        with self.uow.open() as w:
            after = w.iam.complete(token, password, preauth, nonce)
            before = Account(
                after.id,
                after.organization_id,
                after.login_id,
                "PENDING_SETUP",
                after.branch_id,
                after.master,
                after.version - 1,
            )
            w.audit.append(
                Event(
                    "setup_complete",
                    after.organization_id,
                    None,
                    after.id,
                    actor_role="CREDENTIAL_HOLDER",
                    actor_scope="ACTIVATION",
                    before_state=before.state,
                    after_state=after.state,
                    before_branch=before.branch_id,
                    after_branch=after.branch_id,
                    before_version=before.version,
                    after_version=after.version,
                )
            )
            w.iam.confirm_setup(token)

    def change(
        self,
        auth: str | None,
        nonce: str | None,
        ident: UUID,
        version: int,
        branch: UUID | None = None,
        *,
        disable: bool = False,
    ) -> Account:
        if disable:
            return self.lifecycle_change(auth, nonce, ident, version, "account_disable")
        if branch is None:
            raise Rejected(422, "invalid_request")
        with self.uow.open() as w:
            a = w.iam.authenticate(auth, management=True, target=ident, touch=False)
            w.iam.csrf(a, nonce)
            actor_snapshot = w.roles.snapshot(a)
            before = w.iam.scoped_account(a.caller, ident)
            if before.version != version:
                raise Rejected(409, "conflict")
            w.iam.lock_credentials(ident)
            w.organization.require_branch(a.caller, branch)
            after = w.iam.change_scope(before, branch)
            if after.version != before.version:
                w.audit.append(event("scope_change", a.caller, ident, before, after))
            w.roles.confirm_actor(actor_snapshot, self_change=False, touch=True)
            return after

    def _lifecycle_view(self, w: Work, caller: Caller, ident: UUID) -> LifecycleAccount:
        roles = w.iam.lifecycle_target(caller, ident)
        account = roles.account
        trainer = roles.binding.trainer_id if roles.binding else None
        fact = self._trainer_scope(w, caller, trainer) if trainer else None
        route = None
        if account.state == "PENDING_SETUP":
            if roles.admin:
                resource = "master-accounts" if account.master else "accounts"
                route = f"/api/v1/admin/{resource}/{ident}/activation"
            elif roles.operator:
                route = f"/api/v1/admin/operator-accounts/{ident}/initial-setup"
            elif fact and fact.active and roles.trainer_granted:
                route = f"/api/v1/admin/trainers/{trainer}/initial-setup"
        return LifecycleAccount(
            **asdict(account),
            trainer_id=trainer,
            trainer_granted=roles.trainer_granted,
            setup_route=route,
            operator=roles.operator,
        )

    def lifecycle_read(
        self, auth: str | None, target: UUID | str, nonce: str | None = None
    ) -> LifecycleAccount:
        identifier = normalize_login(target) if isinstance(target, str) else None
        if isinstance(target, str):
            with self.uow.open() as w:
                actor = w.iam.authenticate(auth, touch=False)
                w.iam.csrf(actor, nonce)
                assert identifier is not None
                ident = w.iam.lifecycle_id(actor.caller, identifier)
        else:
            ident = target
        with self.uow.open() as w:
            actor = w.iam.authenticate(auth, management=True, target=ident, touch=False)
            if identifier is not None:
                w.iam.csrf(actor, nonce)
            snapshot = w.roles.snapshot(actor)
            result = self._lifecycle_view(w, actor.caller, ident)
            if identifier is not None and identifier != result.login_id:
                raise Rejected(404, "not_found")
            w.roles.confirm_actor(snapshot, self_change=False, touch=True)
            return result

    def change_login_id(
        self, auth: str | None, nonce: str | None, ident: UUID, version: int, identifier: str
    ) -> Account:
        return self.lifecycle_change(auth, nonce, ident, version, "login_id_change", identifier)

    def manage_master(
        self,
        auth: str | None,
        nonce: str | None,
        ident: UUID,
        version: int,
        action: Literal["account_disable", "account_restore", "login_id_change"],
        identifier: str | None = None,
    ) -> Account:
        return self.lifecycle_change(
            auth, nonce, ident, version, action, identifier, master_only=True
        )

    def lifecycle_change(
        self,
        auth: str | None,
        nonce: str | None,
        ident: UUID,
        version: int,
        action: Literal["account_disable", "account_restore", "login_id_change"],
        identifier: str | None = None,
        *,
        master_only: bool = False,
    ) -> LifecycleAccount:
        if action == "login_id_change":
            identifier = normalize_login(identifier or "")
        with self.uow.open() as w:
            actor = w.iam.authenticate(auth, management=True, target=ident, touch=False)
            w.iam.csrf(actor, nonce)
            snapshot = w.roles.snapshot(actor)
            if master_only:
                w.iam.master_management(actor.caller, ident)
            w.iam.require_master(actor.caller)
            w.roles.lock(ident)
            before = self._lifecycle_view(w, actor.caller, ident)
            if before.version != version:
                raise Rejected(409, "conflict")
            if action == "login_id_change":
                assert identifier is not None
                after = w.iam.change_login_id(before, identifier)
            elif action == "account_disable":
                after = w.iam.disable(before)
            else:
                after = w.iam.restore(before)
            changed = after.version != before.version
            result = before
            if changed:
                w.iam.revoke_lifecycle_sources(ident)
                expected = self._lifecycle_view(w, actor.caller, ident)
                w.audit.append(event(action, actor.caller, ident, before, after))
                result = self._lifecycle_view(w, actor.caller, ident)
                if result != expected:
                    raise Rejected(409, "conflict")
            w.roles.confirm_actor(snapshot, self_change=False, touch=changed)
            return result

    def change_password(
        self, auth: str | None, nonce: str | None, current_password: str, new_password: str
    ) -> None:
        with self.uow.open() as w:
            initial, _ = self._current_principal(w, auth)
            w.iam.csrf(initial, nonce)
            ident = initial.caller.account_id
        with self.uow.open() as w:
            proof = w.iam.prepare_password_change(ident, current_password, new_password)
            final, fact = self._current_principal(
                w, auth, management=True, target=ident, credentials=True
            )
            w.iam.csrf(final, nonce)
            if final.caller.account_id != ident:
                raise Rejected(401, "unauthorized")
            snapshot = (
                w.iam.identity_transition(ident)
                if fact is not None
                and not (final.caller.master or final.caller.branch_id or final.caller.operator)
                else None
            )
            password_actor = w.iam.password_change_actor(final, proof) if snapshot is None else None
            before, after = w.iam.change_password(proof)
            if snapshot is not None and fact is not None:
                self._identity_audit(w, "password_change", snapshot, fact)
                w.iam.confirm_identity_transition(snapshot, changed=True, authentication=final)
            else:
                if final.caller.operator:
                    self._operator_event(
                        w, "password_change", final.caller.operator, before, after, final.caller
                    )
                else:
                    w.audit.append(event("password_change", final.caller, ident, before, after))
                assert password_actor is not None
                w.iam.confirm_password_change(password_actor)

    def restore(self, auth: str | None, nonce: str | None, ident: UUID, version: int) -> Account:
        return self.lifecycle_change(auth, nonce, ident, version, "account_restore")

    def logout(self, auth: str | None, preauth: str | None, nonce: str | None) -> None:
        try:
            with self.uow.open() as w:
                a, fact = self._current_principal(w, auth)
                w.iam.csrf(a, nonce)
                snapshot = (
                    w.iam.identity_transition(a.caller.account_id)
                    if fact is not None
                    and not (a.caller.master or a.caller.branch_id or a.caller.operator)
                    else None
                )
                operator_actor = w.roles.snapshot(a) if a.caller.operator else None
                w.iam.logout(a)
                if snapshot is not None and fact is not None:
                    self._identity_audit(w, "logout", snapshot, fact)
                    w.iam.confirm_identity_transition(
                        snapshot, changed=False, authentication=a, logout=True
                    )
                else:
                    if a.caller.operator and operator_actor:
                        account = w.iam.account_roles(a.caller.account_id).account
                        self._operator_event(
                            w, "logout", a.caller.operator, account, account, a.caller
                        )
                        w.roles.confirm_actor(operator_actor, self_change=False, logout=True)
                        return
                    w.audit.append(event("logout", a.caller, a.caller.account_id))
        except Rejected as error:
            if error.status != 401:
                raise
            with self.uow.open() as w:
                w.iam.preparation(preauth, nonce, consume=True)

    def issue_master(
        self, auth: str | None, nonce: str | None, identifier: str
    ) -> tuple[Account, Setup]:
        identifier = normalize_login(identifier)
        with self.uow.open() as w:
            initial = w.iam.authenticate(auth, touch=False)
            w.iam.csrf(initial, nonce)
            w.iam.require_master(initial.caller)
        with self.uow.open() as w:
            slot = w.security.allocate("credential")
        try:
            with self.uow.open() as w:
                current = w.iam.authenticate(auth, management=True, touch=False)
                w.iam.csrf(current, nonce)
                actor_snapshot = w.roles.snapshot(current)
                account = w.iam.issue_master(current.caller, identifier)
                account, setup = w.iam.setup(account, slot, reissue=False)
                w.audit.append(event("account_issue", current.caller, account.id, after=account))
                w.roles.confirm_actor(actor_snapshot, self_change=False, touch=True)
                return account, setup
        except Exception:
            self._release_login_slot(slot)
            raise

    def get_master(self, auth: str | None, ident: UUID) -> Account:
        with self.uow.open() as w:
            current = w.iam.authenticate(auth)
            return w.iam.master_onboarding(current.caller, ident)

    def lookup_master(self, auth: str | None, nonce: str | None, identifier: str) -> Account:
        with self.uow.open() as w:
            current = w.iam.authenticate(auth)
            w.iam.csrf(current, nonce)
            return w.iam.lookup_master(current.caller, normalize_login(identifier))

    def reissue_master(
        self, auth: str | None, nonce: str | None, ident: UUID, version: int
    ) -> tuple[Account, Setup]:
        with self.uow.open() as w:
            initial = w.iam.authenticate(auth, touch=False)
            w.iam.csrf(initial, nonce)
            w.iam.master_onboarding(initial.caller, ident)
        with self.uow.open() as w:
            slot = w.security.allocate("credential")
        try:
            with self.uow.open() as w:
                current = w.iam.authenticate(auth, management=True, target=ident, touch=False)
                w.iam.csrf(current, nonce)
                actor_snapshot = w.roles.snapshot(current)
                before = w.iam.master_onboarding(current.caller, ident)
                if before.version != version:
                    raise Rejected(409, "conflict")
                after, setup = w.iam.setup(before, slot, reissue=True)
                w.audit.append(event("setup_reissue", current.caller, ident, before, after))
                w.roles.confirm_actor(actor_snapshot, self_change=False, touch=True)
                return after, setup
        except Exception:
            self._release_login_slot(slot)
            raise

    def reset_state(self, auth: str | None, ident: UUID) -> ResetState:
        with self.uow.open() as w:
            current = w.iam.authenticate(auth, management=True, target=ident, touch=False)
            snapshot = w.roles.snapshot(current)
            result = w.password_reset.reset_state(current.caller, ident)
            w.roles.confirm_actor(snapshot, self_change=False, touch=True)
            return result

    def reset_password(
        self,
        auth: str | None,
        nonce: str | None,
        ident: UUID,
        version: int,
        generation: int,
        identity_confirmed: bool,
        *,
        reissue: bool,
    ) -> Setup:
        if identity_confirmed is not True:
            raise Rejected(422, "identity_confirmation_required")
        with self.uow.open() as w:
            initial = w.iam.authenticate(auth, management=True, target=ident, touch=False)
            w.iam.csrf(initial, nonce)
            w.password_reset.reset_state(initial.caller, ident)
        with self.uow.open() as w:
            slot = w.security.allocate("password_reset")
        try:
            with self.uow.open() as w:
                current = w.iam.authenticate(auth, management=True, target=ident, touch=False)
                w.iam.csrf(current, nonce)
                snapshot = w.roles.snapshot(current)
                before, after, result, changes = w.password_reset.start_reset(
                    current.caller, ident, version, generation, slot, reissue=reissue
                )
                w.audit.append(
                    replace(
                        event(
                            "password_reset_reissue" if reissue else "password_reset_start",
                            current.caller,
                            ident,
                            before,
                            after,
                        ),
                        **asdict(changes),
                    )
                )
                w.roles.confirm_actor(snapshot, self_change=False, touch=True)
                return result
        except Exception:
            self._release_login_slot(slot)
            raise

    def complete_reset(
        self, token: str, password: str, preauth: str | None, nonce: str | None
    ) -> None:
        with self.uow.open() as w:
            preauth_deadline = w.iam.preparation(preauth, nonce)
        with self.uow.open() as w:
            proof = w.password_reset.prepare_reset(token, password)
            before, after, changes = w.password_reset.complete_reset(proof)
            w.iam.preparation(preauth, nonce, consume=True)
            w.audit.append(
                Event(
                    "password_reset_complete",
                    after.organization_id,
                    after.id,
                    after.id,
                    before_state=before.state,
                    after_state=after.state,
                    before_branch=before.branch_id,
                    after_branch=after.branch_id,
                    actor_scope="PASSWORD_RESET",
                    before_version=before.version,
                    after_version=after.version,
                    **asdict(changes),
                )
            )
            w.password_reset.confirm_complete(proof)
            assert proof.expires_at
            w.iam.confirm_preparation(
                preauth, nonce, deadline=min(preauth_deadline, proof.expires_at)
            )

    def emergency_inspect(
        self, authority: OperatingRecoveryAuthority, ident: UUID
    ) -> EmergencySnapshot:
        with self.uow.open() as w:
            return w.emergency.inspect(authority, ident)

    def emergency_status(
        self, authority: OperatingRecoveryAuthority, operation: UUID
    ) -> EmergencyView:
        with self.uow.open() as w:
            return w.emergency.status(authority, operation)

    def emergency_issue(
        self,
        authority: OperatingRecoveryAuthority,
        request: EmergencyRequest,
        deliver: Callable[[Setup], None],
        commit_observer: Callable[[CommitPhase], None] | None = None,
    ) -> None:
        with self.uow.open() as w:
            w.emergency.preflight(authority, request.account_id)
        with self.uow.open() as w:
            slot = w.security.allocate("emergency", collect=False)
        try:
            with self.uow.open(commit_observer=commit_observer) as w:
                result, audit = w.emergency.issue(authority, request, slot)
                w.audit.append_password_emergency(PasswordEmergencyEvent(**asdict(audit)))
                deliver(result)
        finally:
            self.emergency_release(slot)

    def emergency_release(self, slot: UUID) -> None:
        # Retain the original error, especially an unknown COMMIT. An unattached
        # bounded slot can be reclaimed by ordinary GC after its lease.
        try:
            with self.uow.open() as w:
                w.security.release(slot, collect=False)
        except Exception:
            try:
                logging.getLogger(__name__).warning("Emergency allocation cleanup pending")
            except Exception:
                pass  # Cleanup diagnostics cannot overwrite a business commit outcome.

    def emergency_signed_out(self, auth: str | None) -> None:
        if auth:
            try:
                with self.uow.open() as w:
                    w.iam.authenticate(auth, touch=False)
            except Rejected as error:
                if error.status != 401:
                    raise
            else:
                raise Rejected(409, "logout_required")

    def emergency_preauth(self, auth: str | None, preauth: str | None, nonce: str | None) -> None:
        self.emergency_signed_out(auth)
        with self.uow.open() as w:
            w.iam.preparation(preauth, nonce)

    def emergency_recipient(
        self, token: str, auth: str | None, preauth: str | None, nonce: str | None
    ) -> EmergencyView:
        self.emergency_preauth(auth, preauth, nonce)
        with self.uow.open() as w:
            return w.emergency.recipient(token)

    def emergency_password(
        self, token: str, password: str, auth: str | None, preauth: str | None, nonce: str | None
    ) -> None:
        self.emergency_preauth(auth, preauth, nonce)
        with self.uow.open() as w:
            proof = w.emergency.prepare_password(token, password)
            audit = w.emergency.complete_password(proof)
            w.iam.preparation(preauth, nonce, consume=True)
            w.audit.append_password_emergency(PasswordEmergencyEvent(**asdict(audit)))
            w.emergency.confirm_complete(proof)

    def handoff_state(
        self, auth: str | None, ident: UUID, operation: UUID | None = None
    ) -> HandoffState:
        with self.uow.open() as w:
            current = w.iam.authenticate(auth, management=True, target=ident, touch=False)
            return w.handoff.state(current.caller, ident, operation)

    def handoff(
        self,
        auth: str | None,
        nonce: str | None,
        ident: UUID,
        request: HandoffRequest,
        identity_confirmed: bool,
    ) -> Setup:
        if identity_confirmed is not True:
            raise Rejected(422, "identity_confirmation_required")
        with self.uow.open() as w:
            current = w.iam.authenticate(auth, management=True, target=ident, touch=False)
            w.iam.csrf(current, nonce)
            w.handoff.validate(current.caller, ident, request.supersedes_case_id)
        with self.uow.open() as w:
            slot = w.security.allocate("emergency", collect=False)
        try:
            with self.uow.open() as w:
                current = w.iam.authenticate(auth, management=True, target=ident, touch=False)
                w.iam.csrf(current, nonce)
                actor = w.roles.snapshot(current)
                result, change = w.handoff.issue(current.caller, ident, request, slot)
                w.audit.append_password_emergency(PasswordEmergencyEvent(**asdict(change)))
                # No initial touch: even an audit/lock wait cannot rescue an idle session.
                final = w.iam.authenticate(auth, management=True, target=ident, touch=False)
                w.iam.csrf(final, nonce)
                w.iam.master_management(final.caller, ident)
                w.handoff.confirm(ident, request.operation_id, slot)
                w.roles.confirm_actor(actor, self_change=False, touch=True)
            return result
        finally:
            self.emergency_release(slot)

    def register_trainer(
        self, auth: str | None, nonce: str | None, command: RegisterTrainer
    ) -> RegistrationResult:
        with self.uow.open() as w:
            c = w.workforce.normalize(command)
            a = w.iam.authenticate(auth, management=True, touch=False)
            w.iam.csrf(a, nonce)
            hint = w.workforce.hint(a.caller, c.operation_id)
            branch = w.organization.lock_scoped_branch(
                a.caller, hint.home_branch_id if hint else c.home_branch_id
            )
            if hint is None:
                w.organization.require_assignable(branch)
            result = w.workforce.register(a.caller, branch, c)
            if result.created:
                change = TrainerRegistered(
                    a.caller.organization_id,
                    c.operation_id,
                    result.trainer.id,
                    a.caller.account_id,
                    "MASTER" if a.caller.master else "BRANCH_ADMIN",
                    None if a.caller.master else a.caller.branch_id,
                    branch.branch_id,
                )
                w.audit.append_trainer_registered(change)
                w.audit.append_initial_compensation(
                    InitialCompensationSet(
                        change,
                        c.rate_percent,
                        c.fixed_amount_won,
                        c.base_salary_won,
                        c.base_salary_start_month,
                    )
                )
            final = w.iam.authenticate(auth, management=True, touch=False)
            w.iam.csrf(final, nonce)
            w.organization.confirm_scoped_branch(final.caller, branch)
            if result.created:
                w.organization.require_assignable(branch)
            w.workforce.confirm(final.caller, result)
            w.iam.authenticate(auth, management=True)
        return result

    def trainer_registration(self, auth: str | None, operation: UUID) -> RegistrationResult:
        with self.uow.open() as w:
            a = w.iam.authenticate(auth, management=True, touch=False)
            hint = w.workforce.hint(a.caller, operation)
            if hint is None:
                raise Rejected(404, "not_found")
            branch = w.organization.lock_scoped_branch(a.caller, hint.home_branch_id)
            trainer = w.workforce.get(a.caller, hint.trainer_id)
            if trainer.home_branch_id != branch.branch_id:
                raise Rejected(409, "conflict")
            final = w.iam.authenticate(auth, management=True, touch=False)
            w.organization.confirm_scoped_branch(final.caller, branch)
            result = RegistrationResult(operation, trainer, False)
            w.workforce.confirm(final.caller, result)
        return result

    def trainer(self, auth: str | None, ident: UUID) -> ManagedTrainer:
        with self.uow.open() as w:
            a = w.iam.authenticate(auth, management=True, touch=False)
            hint = w.workforce.identity(a.caller.organization_id, ident)
            branch = w.organization.lock_scoped_branch(a.caller, hint.home_branch_id)
            trainer = w.workforce.get(a.caller, ident)
            if trainer.home_branch_id != branch.branch_id:
                raise Rejected(409, "conflict")
            final = w.iam.authenticate(auth, management=True, touch=False)
            w.organization.confirm_scoped_branch(final.caller, branch)
            if w.workforce.get(final.caller, ident) != trainer:
                raise Rejected(409, "conflict")
        return trainer

    def trainers(self, auth: str | None, offset: int, limit: int) -> TrainerPage:
        with self.uow.open() as w:
            a = w.iam.authenticate(auth, management=True, touch=False)
            page = w.workforce.list(a.caller, offset, limit)
            branches = tuple(
                w.organization.lock_scoped_branch(a.caller, ident)
                for ident in sorted({t.home_branch_id for t in page.items}, key=str)
            )
            for t in sorted(page.items, key=lambda t: str(t.id)):
                if w.workforce.get(a.caller, t.id) != t:
                    raise Rejected(409, "conflict")
            final = w.iam.authenticate(auth, management=True, touch=False)
            for branch in branches:
                w.organization.confirm_scoped_branch(final.caller, branch)
            if w.workforce.list(final.caller, offset, limit) != page:
                raise Rejected(409, "conflict")
        return page

    def trainer_candidates(
        self, auth: str | None, offset: int, limit: int
    ) -> tuple[AssignmentCandidate, ...]:
        with self.uow.open() as w:
            a = w.iam.authenticate(auth, management=True, touch=False)
            candidates = w.organization.assignment_candidates(a.caller, offset, limit)
            facts = tuple(w.organization.lock_scoped_branch(a.caller, c.id) for c in candidates)
            final = w.iam.authenticate(auth, management=True, touch=False)
            for fact in facts:
                w.organization.confirm_scoped_branch(final.caller, fact)
                w.organization.require_assignable(fact)
        return candidates

    def _current_principal(
        self,
        w: Work,
        auth: str | None,
        *,
        management: bool = False,
        target: UUID | None = None,
        credentials: bool = False,
    ) -> tuple[Authentication, TrainerIdentityFact | None]:
        w.iam.installation_lock()
        a = w.iam.authenticate(
            auth, management=management, target=target, touch=False, audience="account"
        )
        if credentials:
            w.iam.lock_trainer_credentials(a.caller.account_id)
        fact = None
        if a.binding is not None and a.trainer_granted:
            fact = w.workforce.lock_identity(a.caller.organization_id, a.binding.trainer_id)
            if not fact.active and not (a.caller.master or a.caller.branch_id or a.caller.operator):
                raise Rejected(401, "unauthorized")
        final = w.iam.authenticate(
            auth, management=management, target=target, touch=False, audience="account"
        )
        if (
            final.binding != a.binding
            or final.trainer_granted != a.trainer_granted
            or final.caller != a.caller
        ):
            raise Rejected(401, "unauthorized")
        return final, fact

    def _identity_audit(
        self,
        w: Work,
        kind: str,
        before: IdentityTransition | None,
        fact: TrainerIdentityFact,
        *,
        account_id: UUID | None = None,
        caller: Caller | None = None,
        operation: UUID | None = None,
    ) -> None:
        ident = account_id if account_id is not None else (before.account.id if before else None)
        assert ident is not None
        after = w.iam.identity_transition(ident)
        role = (
            ("MASTER" if caller.master else "BRANCH_ADMIN")
            if caller
            else ("CREDENTIAL_HOLDER" if kind == "setup_complete" else "TRAINER")
        )
        actor = caller.account_id if caller else (None if kind == "setup_complete" else ident)
        w.audit.append_trainer_identity(
            TrainerIdentityEvent(
                fact.organization_id,
                ident,
                fact.trainer_id,
                kind,
                actor,
                role,
                caller.branch_id if caller else None,
                fact.home_branch_id,
                operation,
                before.account.state if before else None,
                after.account.state,
                before.account.version if before else None,
                after.account.version,
                before.security_version if before else None,
                after.security_version,
            )
        )

    def _trainer_scope(
        self, w: Work, caller: Caller, trainer: UUID, *, exclusive: bool = False
    ) -> TrainerIdentityFact:
        hint = w.workforce.identity(caller.organization_id, trainer)
        branch = w.organization.lock_scoped_branch(caller, hint.home_branch_id)
        fact = w.workforce.lock_identity(caller.organization_id, trainer, exclusive=exclusive)
        if fact.home_branch_id != branch.branch_id:
            raise Rejected(409, "conflict")
        w.organization.confirm_scoped_branch(caller, branch)
        return fact

    def trainer_account_state(self, auth: str | None, trainer: UUID) -> TrainerAccountState:
        with self.uow.open() as w:
            a = w.iam.authenticate(auth, management=True, touch=False)
            fact = self._trainer_scope(w, a.caller, trainer)
            result = w.iam.trainer_state(a.caller.organization_id, trainer)
            final = w.iam.authenticate(auth, management=True, touch=False)
            self._trainer_scope(w, final.caller, fact.trainer_id)
            return result

    def trainer_account_operation(self, auth: str | None, operation: UUID) -> TrainerOperation:
        with self.uow.open() as w:
            a = w.iam.authenticate(auth, management=True, touch=False)
            result = w.iam.trainer_operation(a.caller.organization_id, operation)
            if result is None:
                raise Rejected(404, "not_found")
            self._trainer_scope(w, a.caller, result.trainer_id)
            w.iam.authenticate(auth, management=True, touch=False)
            return result

    def issue_trainer_account(
        self,
        auth: str | None,
        nonce: str | None,
        trainer: UUID,
        operation: UUID,
        identifier: str | None,
        expected: int | None = None,
    ) -> tuple[TrainerOperation, Setup | None]:
        if identifier is not None:
            identifier = normalize_login(identifier)
        with self.uow.open() as w:
            a = w.iam.authenticate(auth, management=True, touch=False)
            w.iam.csrf(a, nonce)
            self._trainer_scope(w, a.caller, trainer)
            organization_id = a.caller.organization_id
        with self.uow.open() as w:
            slot = w.security.allocate("credential", collect=False)
        try:
            with self.uow.open() as w:
                # Stabilize the target hint before acquiring any sorted account locks.
                w.iam.installation_lock()
                binding = w.iam.trainer_binding(organization_id, trainer)
                target = binding.account_id if binding else None
                a = w.iam.authenticate(auth, management=True, target=target, touch=False)
                w.iam.csrf(a, nonce)
                if target:
                    w.iam.lock_trainer_credentials(target)
                fact = self._trainer_scope(w, a.caller, trainer, exclusive=True)
                old = w.iam.trainer_operation(a.caller.organization_id, operation)
                if old is None and not fact.active:
                    raise Rejected(409, "conflict")
                result, setup, before = w.iam.trainer_issue(
                    a.caller, trainer, fact.home_branch_id, operation, identifier, expected, slot
                )
                if setup is not None:
                    self._identity_audit(
                        w,
                        result.kind,
                        before,
                        fact,
                        account_id=result.account_id,
                        caller=a.caller,
                        operation=operation,
                    )
                final = w.iam.authenticate(auth, management=True, target=target, touch=False)
                w.iam.csrf(final, nonce)
                final_fact = self._trainer_scope(w, final.caller, trainer)
                if setup is not None:
                    if not final_fact.active:
                        raise Rejected(409, "conflict")
                    w.iam.confirm_trainer_delivery(result, slot)
                w.iam.authenticate(auth, management=True, target=target)
            return result, setup
        finally:
            with self.uow.open() as w:
                w.security.release(slot, collect=False)

    def complete_trainer_setup(
        self, token: str, password: str, preauth: str | None, nonce: str | None
    ) -> None:
        with self.uow.open() as w:
            w.iam.preparation(preauth, nonce)
        with self.uow.open() as w:
            proof = w.iam.prepare_trainer_setup(token, password)
            binding = w.iam.lock_trainer_setup(proof, preauth, nonce)
            fact = w.workforce.lock_identity(binding.organization_id, binding.trainer_id)
            if not fact.active:
                raise Rejected(400, "invalid_setup")
            before = w.iam.complete_trainer_setup(proof, preauth, nonce)
            self._identity_audit(w, "setup_complete", before, fact)
            w.iam.confirm_trainer_setup(proof)
            w.iam.confirm_preparation(preauth, nonce)

    def role_state(self, auth: str | None, trainer: UUID) -> TrainerRoleState:
        with self.uow.open() as w:
            a = w.iam.authenticate(auth, management=True, touch=False)
            self._trainer_scope(w, a.caller, trainer)
            result = w.roles.state(a.caller.organization_id, trainer)
            final = w.iam.authenticate(auth, management=True, touch=False)
            self._trainer_scope(w, final.caller, trainer)
            return result

    def role_lookup(
        self, auth: str | None, trainer: UUID, identifier: str, nonce: str | None
    ) -> TrainerRoleCandidate:
        with self.uow.open() as w:
            a = w.iam.authenticate(auth, management=True, touch=False)
            w.iam.csrf(a, nonce)
            self._trainer_scope(w, a.caller, trainer)
            hint = w.roles.lookup(a.caller.organization_id, trainer, identifier)
        with self.uow.open() as w:
            a = w.iam.authenticate(auth, management=True, target=hint.account_id, touch=False)
            w.iam.csrf(a, nonce)
            self._trainer_scope(w, a.caller, trainer)
            result = w.roles.lookup(a.caller.organization_id, trainer, identifier)
            if result.account_id != hint.account_id:
                raise Rejected(409, "conflict")
            final = w.iam.authenticate(auth, management=True, target=hint.account_id, touch=False)
            self._trainer_scope(w, final.caller, trainer)
            return result

    def role_operation(self, auth: str | None, operation: UUID) -> TrainerRoleResult:
        with self.uow.open() as w:
            a = w.iam.authenticate(auth, management=True, touch=False)
            result = w.roles.operation(a.caller.organization_id, operation)
            if result is None:
                raise Rejected(404, "not_found")
            self._trainer_scope(w, a.caller, result.current_state.trainer_id)
            final = w.iam.authenticate(auth, management=True, touch=False)
            self._trainer_scope(w, final.caller, result.current_state.trainer_id)
            return result

    def change_trainer_role(
        self,
        auth: str | None,
        nonce: str | None,
        trainer: UUID,
        request: TrainerRoleRequest,
    ) -> TrainerRoleResult:
        with self.uow.open() as w:
            a = w.iam.authenticate(auth, management=True, target=request.account_id, touch=False)
            w.iam.csrf(a, nonce)
            w.roles.lock(request.account_id)
            fact = self._trainer_scope(w, a.caller, trainer, exclusive=True)
            snapshot = w.roles.snapshot(a)
            result, change = w.roles.change(
                a.caller, trainer, fact.home_branch_id, fact.active, fact.version, request
            )
            if change is not None:
                w.audit.append_trainer_role(
                    TrainerRoleEvent(
                        a.caller.organization_id,
                        request.operation_id,
                        request.account_id,
                        trainer,
                        a.caller.account_id,
                        "MASTER" if a.caller.master else "BRANCH_ADMIN",
                        a.caller.branch_id,
                        fact.home_branch_id,
                        change.kind,
                        change.before_granted,
                        change.after_granted,
                        change.before_role_version,
                        change.after_role_version,
                        change.before_role_version,
                        change.after_role_version,
                        change.account_version,
                        change.account_version,
                        change.security_version,
                        change.security_version,
                    )
                )
                w.roles.confirm_change(result, change)
            self_change = change is not None and a.caller.account_id == request.account_id
            final_fact = self._trainer_scope(w, a.caller, trainer)
            if final_fact != fact:
                raise Rejected(409, "conflict")
            w.roles.confirm_actor(snapshot, self_change=self_change)
            return replace(result, reauthentication_required=self_change)

    def self_role_state(self, auth: str | None) -> TrainerRoleState | None:
        with self.uow.open() as w:
            a, _ = self._current_principal(w, auth)
            if a.binding is None:
                return None
            return w.roles.state(a.caller.organization_id, a.binding.trainer_id)

    def identity_profile(
        self,
        auth: str | None,
    ) -> tuple[Caller, TrainerIdentityFact | None, TrainerRoleState | None]:
        with self.uow.open() as w:
            a, fact = self._current_principal(w, auth)
            snapshot = w.roles.snapshot(a) if a.caller.operator else None
            role = (
                w.roles.state(a.caller.organization_id, a.binding.trainer_id)
                if a.binding is not None
                else None
            )
            if snapshot:
                w.roles.confirm_actor(snapshot, self_change=False, touch=True)
            return a.caller, fact, role

    def trainer_state_operation(self, auth: str | None, operation: UUID) -> TrainerStateResult:
        with self.uow.open() as w:
            a = w.iam.authenticate(auth, management=True, touch=False)
            snapshot = w.roles.snapshot(a)
            result = w.workforce.state_operation(a.caller, operation)
            if result is None:
                raise Rejected(404, "not_found")
            fact = self._trainer_scope(w, a.caller, result.trainer_id)
            if fact != result.current_state:
                raise Rejected(409, "conflict")
            w.workforce.confirm_state(a.caller, result)
            w.roles.confirm_actor(snapshot, self_change=False)
            return result

    def change_trainer_state(
        self,
        auth: str | None,
        nonce: str | None,
        trainer: UUID,
        request: TrainerStateRequest,
    ) -> TrainerStateResult:
        with self.uow.open() as w:
            a = w.iam.authenticate(auth, management=True, touch=False)
            w.iam.csrf(a, nonce)
            self._trainer_scope(w, a.caller, trainer)
            hint = w.iam.trainer_binding(a.caller.organization_id, trainer)
        with self.uow.open() as w:
            a = w.iam.authenticate(
                auth, management=True, target=hint.account_id if hint else None, touch=False
            )
            w.iam.csrf(a, nonce)
            binding = w.iam.trainer_binding(a.caller.organization_id, trainer)
            if binding != hint:
                raise Rejected(409, "conflict")
            snapshot = w.roles.snapshot(a)
            fact = self._trainer_scope(w, a.caller, trainer, exclusive=True)
            branch = w.organization.lock_scoped_branch(a.caller, fact.home_branch_id)
            result, change = w.workforce.change_state(a.caller, branch, fact, request)
            if change is not None:
                if not change.after_active and binding is not None:
                    w.iam.revoke_trainer_only_sessions(binding)
                w.audit.append_trainer_state(
                    TrainerStateEvent(
                        change.organization_id,
                        change.operation_id,
                        change.trainer_id,
                        binding.account_id if binding else None,
                        a.caller.account_id,
                        "MASTER" if a.caller.master else "BRANCH_ADMIN",
                        a.caller.branch_id,
                        fact.home_branch_id,
                        change.before_active,
                        change.after_active,
                        change.before_version,
                        change.after_version,
                        change.recorded_at,
                    )
                )
            w.organization.confirm_scoped_branch(a.caller, branch)
            w.workforce.confirm_state(a.caller, result)
            if self._trainer_scope(w, a.caller, trainer) != result.current_state:
                raise Rejected(409, "conflict")
            w.roles.confirm_actor(snapshot, self_change=False)
            return result
