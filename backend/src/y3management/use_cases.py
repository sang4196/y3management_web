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
    TrainerIdentityEvent,
    TrainerRegistered,
    TrainerRoleEvent,
)
from y3management.contracts import CommitPhase, HashAdmissionRejected, Rejected
from y3management.iam.public import (
    Account,
    Authentication,
    Caller,
    Ceremony,
    EmergencyRequest,
    EmergencySnapshot,
    EmergencyView,
    HandoffRequest,
    HandoffState,
    IdentityTransition,
    KeyList,
    OperatingRecoveryAuthority,
    Preparation,
    RecoveryState,
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
        deliver: Callable[[Setup], None] | None = None,
    ) -> Account:
        identifier = normalize_login(identifier)
        if not name or len(name) > 128:
            raise Rejected(422, "invalid_request")
        state_id = None
        if self.uow.settings.iam_mode == "mfa":
            if deliver is None:
                raise Rejected(403, "installation_delivery_required")
            with self.uow.open() as w:
                state_id = w.security.allocate("mfa")
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
            if state_id is not None and deliver is not None:
                deliver(w.mfa.installation(account, state_id))
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
        if self.uow.settings.iam_mode == "mfa":
            result = self.login_entry(
                identifier, password, preauth, nonce, auth, expected_mfa=False
            )
            if isinstance(result, Ceremony):
                raise Rejected(403, "mfa_required")
            return result
        # Retain the limited S1 transaction, lock and uncertain-commit cleanup contract.
        if auth:
            try:
                with self.uow.open() as w:
                    current = w.iam.authenticate(auth, touch=False)
                    w.iam.csrf(current, nonce)
            except Rejected as error:
                if error.status != 401:
                    raise
            else:
                raise Rejected(409, "logout_required")
        identifier = normalize_login(identifier)
        # Only invalid/absent AuthSession takes the preparation-CSRF path.
        with self.uow.open() as w:
            w.iam.preparation(preauth, nonce)
        with self.uow.open() as w:
            w.iam.gc_sessions()
        with self.uow.open(commit_denial=True) as w:
            reservation = w.security.reserve(identifier)
        sid: UUID | None = None
        subject: Account | None = None
        try:
            with self.uow.open() as w:
                subject = w.iam.login_subject(identifier)
                if subject is not None and subject.id != reservation.account_id:
                    subject = None
                proof = w.iam.verify_login(identifier, password, reservation)
                if proof is None:
                    raise Rejected(401, "invalid_credentials")
                # S1 is the existing administrator-only development path.
                if not w.iam.account_roles(proof.account_id).admin:
                    raise Rejected(401, "invalid_credentials")
                # Only unlocked read snapshots exist here; security locks end before business locks.
                with self.uow.open() as security:
                    sid = security.security.allocate("session_slot")
                token, account = w.iam.login(proof, sid, preauth, nonce, reservation)
                caller = Caller(
                    account.id, account.organization_id, account.branch_id, account.master
                )
                w.audit.append(event("login", caller, account.id))
            # Finish only after closing business locks. A storage failure here never returns cookie.
            with self.uow.open() as security:
                security.security.finish(reservation, True)
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
                    if sid is not None:
                        security.security.release(sid)
            else:
                self._release_login_slot(sid)
            raise
        except Exception:
            self._release_login_slot(sid)
            raise

    def login_entry(
        self,
        identifier: str,
        password: str,
        preauth: str | None,
        nonce: str | None,
        auth: str | None,
        *,
        expected_mfa: bool | None = None,
    ) -> str | Ceremony:
        if self.uow.settings.iam_mode == "s1_password":
            if expected_mfa is True:
                raise Rejected(403, "mfa_unavailable")
            return self.login(identifier, password, preauth, nonce, auth)
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
            w.iam.preparation(preauth, nonce)
            w.iam.gc_sessions()
        with self.uow.open(commit_denial=True) as w:
            reservation = w.security.reserve(identifier)
        sid = None
        subject = None
        delivered = False
        mfa_path = False
        try:
            with self.uow.open() as w:
                subject = w.iam.login_subject(identifier)
                if subject is not None and subject.id != reservation.account_id:
                    subject = None
                proof = w.iam.verify_login(identifier, password, reservation)
                if proof is None:
                    raise Rejected(401, "invalid_credentials")
                roles = w.iam.account_roles(proof.account_id)
                mfa_path = roles.admin and self.uow.settings.iam_mode == "mfa"
                if expected_mfa is not None and expected_mfa != mfa_path:
                    raise Rejected(403, "mfa_required")
                with self.uow.open() as security:
                    if mfa_path:
                        security.security.mfa_stage(reservation, "waiting")
                    sid = security.security.allocate("mfa" if mfa_path else "session_slot")
                if mfa_path:
                    result = w.mfa.begin_login(proof, reservation, sid)
                    w.iam.preparation(preauth, nonce, consume=True)
                else:
                    roles = w.iam.lock_login(proof.account_id)
                    if roles.admin:
                        if self.uow.settings.iam_mode == "mfa":
                            raise Rejected(401, "invalid_credentials")
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
                    if fact is not None:
                        self._identity_audit(
                            w, "login", w.iam.identity_transition(account.id), fact
                        )
                    else:
                        caller = Caller(
                            account.id, account.organization_id, account.branch_id, account.master
                        )
                        w.audit.append(event("login", caller, account.id))
                    w.iam.confirm_login(proof, reservation, sid)
                    w.iam.confirm_preparation(preauth, nonce)
            if mfa_path:
                delivered = True
                return result
            with self.uow.open() as security:
                security.security.finish(reservation, True)
            delivered = True
            return token
        except HashAdmissionRejected:
            self._cancel_login(reservation, sid)
            raise
        except Rejected as error:
            if error.status == 401:
                if mfa_path:
                    self.fail_mfa(reservation)
                else:
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
                # Even COMMIT ACK loss may have persisted the unreturned session.
                # This id is ours; a missing row is a safe no-op (MFA slots included).
                with self.uow.open() as cleanup:
                    cleanup.iam.revoke_undelivered_session(sid)
                self._release_login_slot(sid)

    def _release_login_slot(self, sid: UUID | None) -> None:
        # Verification may have begun: preserve the reservation for conservative lease handling.
        if sid is not None:
            try:
                with self.uow.open() as w:
                    w.security.release(sid)
            except Exception:
                logging.getLogger("y3management").warning("security_cleanup_deferred")

    def _cancel_login(self, reservation: Reservation, sid: UUID | None) -> None:
        try:
            with self.uow.open() as w:
                w.security.cancel(reservation)
                if sid is not None:
                    w.security.release(sid)
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
            a = w.iam.authenticate(auth, management=True)
            w.iam.csrf(a, nonce)
            w.iam.require_master(a.caller)
            b = w.organization.create_branch(a.caller, code, name)
            w.audit.append(event("branch_create", a.caller, b.id, branch=b))
            return b

    def issue(
        self, auth: str | None, nonce: str | None, identifier: str, branch: UUID
    ) -> tuple[Account, Setup]:
        identifier = normalize_login(identifier)
        with self.uow.open() as w:
            state_id = w.security.allocate("credential")
        try:
            with self.uow.open() as w:
                a = w.iam.authenticate(auth, management=True)
                w.iam.csrf(a, nonce)
                w.iam.require_master(a.caller)
                w.organization.require_branch(a.caller, branch)
                account = w.iam.issue(a.caller, identifier, branch)
                account, setup = w.iam.setup(account, state_id, reissue=False)
                w.audit.append(event("account_issue", a.caller, account.id, after=account))
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
                a = w.iam.authenticate(auth, management=True, target=ident)
                w.iam.csrf(a, nonce)
                before = w.iam.scoped_account(a.caller, ident)
                if before.version != version:
                    raise Rejected(409, "conflict")
                after, setup = w.iam.setup(before, state_id, reissue=True)
                w.audit.append(event("setup_reissue", a.caller, ident, before, after))
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
        with self.uow.open() as w:
            a = w.iam.authenticate(auth, management=True, target=ident)
            w.iam.csrf(a, nonce)
            before = w.iam.scoped_account(a.caller, ident)
            if before.version != version:
                raise Rejected(409, "conflict")
            w.iam.lock_credentials(ident)
            if not disable:
                if branch is None:
                    raise Rejected(422, "invalid_request")
                w.organization.require_branch(a.caller, branch)
            after = w.iam.change(before, branch, disable)
            if after.version != before.version:
                w.audit.append(
                    event(
                        "account_disable" if disable else "scope_change",
                        a.caller,
                        ident,
                        before,
                        after,
                    )
                )
            return after

    def change_login_id(
        self, auth: str | None, nonce: str | None, ident: UUID, version: int, identifier: str
    ) -> Account:
        identifier = normalize_login(identifier)
        with self.uow.open() as w:
            a = w.iam.authenticate(auth, management=True, target=ident, touch=False)
            w.iam.csrf(a, nonce)
            before = w.iam.scoped_account(a.caller, ident)
            if before.version != version:
                raise Rejected(409, "conflict")
            after = w.iam.change_login_id(before, identifier)
            if after.version != before.version:
                final = w.iam.authenticate(auth, management=True, target=ident, touch=True)
                w.iam.csrf(final, nonce)
                w.audit.append(event("login_id_change", final.caller, ident, before, after))
            return after

    def manage_master(
        self,
        auth: str | None,
        nonce: str | None,
        ident: UUID,
        version: int,
        action: Literal["account_disable", "account_restore", "login_id_change"],
        identifier: str | None = None,
    ) -> Account:
        self.require_mfa()
        if action == "login_id_change":
            identifier = normalize_login(identifier or "")
        with self.uow.open() as w:
            actor = w.iam.authenticate(auth, management=True, target=ident, touch=False)
            w.iam.csrf(actor, nonce)
            before = w.iam.master_management(actor.caller, ident)
            if before.version != version:
                raise Rejected(409, "conflict")
            if action == "login_id_change":
                assert identifier is not None
                after = w.iam.change_login_id(before, identifier)
            elif action == "account_disable":
                after = w.iam.change(before, None, True)
            else:
                w.iam.lock_credentials(ident)
                after = w.iam.restore(before)
            if after.version != before.version:
                w.iam.revoke_management_sources(ident)
                final = w.iam.authenticate(auth, management=True, target=ident, touch=True)
                w.iam.csrf(final, nonce)
                w.iam.master_management(final.caller, ident)
                w.audit.append(event(action, final.caller, ident, before, after))
            return after

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
                if fact is not None and not (final.caller.master or final.caller.branch_id)
                else None
            )
            before, after = w.iam.change_password(proof)
            if snapshot is not None and fact is not None:
                self._identity_audit(w, "password_change", snapshot, fact)
                w.iam.confirm_identity_transition(snapshot, changed=True, authentication=final)
            else:
                w.audit.append(event("password_change", final.caller, ident, before, after))

    def restore(self, auth: str | None, nonce: str | None, ident: UUID, version: int) -> Account:
        with self.uow.open() as w:
            authentication = w.iam.authenticate(auth, management=True, target=ident)
            w.iam.csrf(authentication, nonce)
            before = w.iam.scoped_account(authentication.caller, ident)
            if before.version != version:
                raise Rejected(409, "conflict")
            w.iam.lock_credentials(ident)
            after = w.iam.restore(before)
            w.audit.append(event("account_restore", authentication.caller, ident, before, after))
            return after

    def logout(self, auth: str | None, preauth: str | None, nonce: str | None) -> None:
        try:
            with self.uow.open() as w:
                a, fact = self._current_principal(w, auth)
                w.iam.csrf(a, nonce)
                snapshot = (
                    w.iam.identity_transition(a.caller.account_id)
                    if fact is not None and not (a.caller.master or a.caller.branch_id)
                    else None
                )
                w.iam.logout(a)
                if snapshot is not None and fact is not None:
                    self._identity_audit(w, "logout", snapshot, fact)
                    w.iam.confirm_identity_transition(
                        snapshot, changed=False, authentication=a, logout=True
                    )
                else:
                    w.audit.append(event("logout", a.caller, a.caller.account_id))
        except Rejected as error:
            if error.status != 401:
                raise
            with self.uow.open() as w:
                w.iam.preparation(preauth, nonce, consume=True)

    def require_mfa(self) -> None:
        if self.uow.settings.iam_mode != "mfa":
            raise Rejected(403, "mfa_unavailable")

    def begin_enrollment(
        self, token: str, password: str | None, preauth: str | None, nonce: str | None
    ) -> Ceremony:
        self.require_mfa()
        with self.uow.open() as w:
            w.iam.preparation(preauth, nonce)
        slot = None
        if password is not None:
            with self.uow.open() as w:
                slot = w.security.allocate("mfa")
        try:
            with self.uow.open() as w:
                result = (
                    w.mfa.begin_setup(token, password, slot)
                    if password is not None and slot is not None
                    else w.mfa.begin_install(token)
                )
                w.iam.preparation(preauth, nonce, consume=True)
            return result
        except Exception:
            self._release_login_slot(slot)
            raise

    def begin_passkey(self, auth: str | None, nonce: str | None) -> Ceremony:
        self.require_mfa()
        with self.uow.open() as w:
            initial = w.iam.authenticate(auth, touch=False)
            w.iam.csrf(initial, nonce)
        with self.uow.open() as w:
            slot = w.security.allocate("mfa")
        try:
            with self.uow.open() as w:
                current = w.iam.authenticate(auth, management=True)
                w.iam.csrf(current, nonce)
                return w.mfa.begin_add(current, slot)
        except Exception:
            self._release_login_slot(slot)
            raise

    def register_passkey(
        self,
        token: str | None,
        nonce: str | None,
        payload: str,
        auth: str | None,
        *,
        additional: bool,
        recovery: bool = False,
    ) -> None:
        self.require_mfa()
        initial = None
        if additional:
            with self.uow.open() as w:
                initial = w.iam.authenticate(auth, touch=False)
        with self.uow.open() as w:
            proof = w.mfa.verify_registration(token, nonce, payload)
        allowed = {"recovery"} if recovery else ({"add"} if additional else {"install", "setup"})
        if proof.purpose not in allowed:
            raise Rejected(401, "invalid_ceremony")
        with self.uow.open() as w:
            current = w.iam.authenticate(auth, management=True) if additional else None
            if current is not None and initial is not None:
                w.iam.csrf(current, initial.csrf)
                if current.session_id != initial.session_id:
                    raise Rejected(401, "unauthorized")
            account, changes = w.mfa.register(token, nonce, proof, current)
            if proof.purpose == "setup":
                w.audit.append(
                    Event(
                        "setup_complete",
                        account.organization_id,
                        None,
                        account.id,
                        actor_role="CREDENTIAL_HOLDER",
                        actor_scope="ACTIVATION",
                        before_state="PENDING_SETUP",
                        after_state=account.state,
                        before_branch=account.branch_id,
                        after_branch=account.branch_id,
                        before_version=account.version - 1,
                        after_version=account.version,
                    )
                )
            w.audit.append(
                Event(
                    "recovery_complete" if recovery else "passkey_register",
                    account.organization_id,
                    current.caller.account_id if current else None,
                    account.id,
                    actor_role="ADMIN" if current else "CREDENTIAL_HOLDER",
                    actor_scope="SELF" if current else ("RECOVERY" if recovery else "ONBOARDING"),
                    after_state=account.state,
                    after_version=account.version,
                    **asdict(changes),
                )
            )

    def begin_mfa_login(
        self,
        identifier: str,
        password: str,
        preauth: str | None,
        nonce: str | None,
        auth: str | None,
    ) -> Ceremony:
        self.require_mfa()
        result = self.login_entry(identifier, password, preauth, nonce, auth, expected_mfa=True)
        if not isinstance(result, Ceremony):
            raise Rejected(403, "mfa_required")
        return result

    def fail_mfa(self, reservation: Reservation) -> None:
        with self.uow.open() as w:
            subject = w.mfa.failure_subject(reservation)
            w.security.finish(reservation, False)
            w.audit.append(
                Event(
                    "login",
                    subject.organization_id if subject else None,
                    None,
                    subject.id if subject else None,
                    success=False,
                    actor_role="LOGIN_ATTEMPT",
                )
            )

    def finish_mfa_login(self, token: str | None, nonce: str | None, payload: str) -> str:
        self.require_mfa()
        with self.uow.open() as w:
            reservation = w.mfa.reservation(token, nonce)
        with self.uow.open() as w:
            w.security.mfa_stage(reservation, "verifying")
        sid = None
        try:
            with self.uow.open() as w:
                sid = w.security.allocate("session_slot")
            with self.uow.open() as w:
                raw, account = w.mfa.authenticate(token, nonce, payload, sid)
                w.audit.append(
                    event(
                        "login",
                        Caller(
                            account.id, account.organization_id, account.branch_id, account.master
                        ),
                        account.id,
                    )
                )
            with self.uow.open() as w:
                w.security.finish(reservation, True)
            return raw
        except Exception as error:
            # Includes unknown business COMMIT and finish ACK: never send the cookie.
            if sid is not None:
                try:
                    with self.uow.open() as w:
                        w.mfa.revoke_undelivered(sid)
                    self._release_login_slot(sid)
                except Exception:
                    logging.getLogger("y3management").error("mfa_session_cleanup_deferred")
                    raise Rejected(503, "mfa_cleanup_deferred") from None
            if isinstance(error, Rejected) and error.status == 401:
                self.fail_mfa(reservation)
            raise

    def passkeys(self, auth: str | None) -> KeyList:
        self.require_mfa()
        with self.uow.open() as w:
            current = w.iam.authenticate(auth, management=True)
            return w.mfa.keys(current.caller.account_id)

    def delete_passkey(
        self, auth: str | None, nonce: str | None, key_id: UUID, version: int
    ) -> None:
        self.require_mfa()
        with self.uow.open() as w:
            initial = w.iam.authenticate(auth, touch=False)
            w.iam.csrf(initial, nonce)
        with self.uow.open() as w:
            current = w.iam.authenticate(auth, management=True, target=initial.caller.account_id)
            w.iam.csrf(current, nonce)
            before, after, changes = w.mfa.delete_key(current.caller.account_id, key_id, version)
            w.audit.append(
                replace(
                    event("passkey_delete", current.caller, after.id, before, after),
                    **asdict(changes),
                )
            )

    def issue_master(
        self, auth: str | None, nonce: str | None, identifier: str
    ) -> tuple[Account, Setup]:
        self.require_mfa()
        identifier = normalize_login(identifier)
        with self.uow.open() as w:
            initial = w.iam.authenticate(auth, touch=False)
            w.iam.csrf(initial, nonce)
            w.iam.require_master(initial.caller)
        with self.uow.open() as w:
            slot = w.security.allocate("credential")
        try:
            with self.uow.open() as w:
                current = w.iam.authenticate(auth, management=True)
                w.iam.csrf(current, nonce)
                account = w.iam.issue_master(current.caller, identifier)
                account, setup = w.iam.setup(account, slot, reissue=False)
                w.audit.append(event("account_issue", current.caller, account.id, after=account))
                return account, setup
        except Exception:
            self._release_login_slot(slot)
            raise

    def get_master(self, auth: str | None, ident: UUID) -> Account:
        self.require_mfa()
        with self.uow.open() as w:
            current = w.iam.authenticate(auth)
            return w.iam.master_onboarding(current.caller, ident)

    def lookup_master(self, auth: str | None, nonce: str | None, identifier: str) -> Account:
        self.require_mfa()
        with self.uow.open() as w:
            current = w.iam.authenticate(auth)
            w.iam.csrf(current, nonce)
            return w.iam.lookup_master(current.caller, normalize_login(identifier))

    def reissue_master(
        self, auth: str | None, nonce: str | None, ident: UUID, version: int
    ) -> tuple[Account, Setup]:
        self.require_mfa()
        with self.uow.open() as w:
            initial = w.iam.authenticate(auth, touch=False)
            w.iam.csrf(initial, nonce)
            w.iam.master_onboarding(initial.caller, ident)
        with self.uow.open() as w:
            slot = w.security.allocate("credential")
        try:
            with self.uow.open() as w:
                current = w.iam.authenticate(auth, management=True, target=ident)
                w.iam.csrf(current, nonce)
                before = w.iam.master_onboarding(current.caller, ident)
                if before.version != version:
                    raise Rejected(409, "conflict")
                after, setup = w.iam.setup(before, slot, reissue=True)
                w.audit.append(event("setup_reissue", current.caller, ident, before, after))
                return after, setup
        except Exception:
            self._release_login_slot(slot)
            raise

    def recovery_state(self, auth: str | None, ident: UUID) -> RecoveryState:
        self.require_mfa()
        with self.uow.open() as w:
            current = w.iam.authenticate(auth, management=True, target=ident)
            return w.mfa.recovery_state(current.caller, ident)

    def recover(
        self,
        auth: str | None,
        nonce: str | None,
        ident: UUID,
        version: int,
        key_version: int,
        identity_confirmed: bool,
        *,
        reissue: bool,
    ) -> Setup:
        self.require_mfa()
        if identity_confirmed is not True:
            raise Rejected(422, "identity_confirmation_required")
        with self.uow.open() as w:
            initial = w.iam.authenticate(auth, management=True, target=ident, touch=False)
            w.iam.csrf(initial, nonce)
            w.mfa.recovery_state(initial.caller, ident)
        with self.uow.open() as w:
            slot = w.security.allocate("recovery")
        try:
            with self.uow.open() as w:
                current = w.iam.authenticate(auth, management=True, target=ident)
                w.iam.csrf(current, nonce)
                before, after, result, changes = w.mfa.start_recovery(
                    current.caller, ident, version, key_version, slot, reissue=reissue
                )
                w.audit.append(
                    replace(
                        event(
                            "recovery_reissue" if reissue else "recovery_start",
                            current.caller,
                            ident,
                            before,
                            after,
                        ),
                        **asdict(changes),
                    )
                )
                return result
        except Exception:
            self._release_login_slot(slot)
            raise

    def begin_recovery(self, token: str, preauth: str | None, nonce: str | None) -> Ceremony:
        self.require_mfa()
        with self.uow.open() as w:
            w.iam.preparation(preauth, nonce)
        with self.uow.open() as w:
            slot = w.security.allocate("mfa")
        try:
            with self.uow.open() as w:
                result = w.mfa.begin_recovery(token, slot)
                w.iam.preparation(preauth, nonce, consume=True)
                return result
        except Exception:
            self._release_login_slot(slot)
            raise

    def reset_state(self, auth: str | None, ident: UUID) -> ResetState:
        self.require_mfa()
        with self.uow.open() as w:
            current = w.iam.authenticate(auth, management=True, target=ident)
            return w.mfa.reset_state(current.caller, ident)

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
        self.require_mfa()
        if identity_confirmed is not True:
            raise Rejected(422, "identity_confirmation_required")
        with self.uow.open() as w:
            initial = w.iam.authenticate(auth, management=True, target=ident, touch=False)
            w.iam.csrf(initial, nonce)
            w.mfa.reset_state(initial.caller, ident)
        with self.uow.open() as w:
            slot = w.security.allocate("password_reset")
        try:
            with self.uow.open() as w:
                current = w.iam.authenticate(auth, management=True, target=ident)
                w.iam.csrf(current, nonce)
                before, after, result, changes = w.mfa.start_reset(
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
                return result
        except Exception:
            self._release_login_slot(slot)
            raise

    def complete_reset(
        self, token: str, password: str, preauth: str | None, nonce: str | None
    ) -> None:
        self.require_mfa()
        with self.uow.open() as w:
            w.iam.preparation(preauth, nonce)
        with self.uow.open() as w:
            proof = w.mfa.prepare_reset(token, password)
            before, after, changes = w.mfa.complete_reset(proof)
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

    def emergency_inspect(
        self, authority: OperatingRecoveryAuthority, ident: UUID
    ) -> EmergencySnapshot:
        self.require_mfa()
        with self.uow.open() as w:
            return w.emergency.inspect(authority, ident)

    def emergency_status(
        self, authority: OperatingRecoveryAuthority, operation: UUID
    ) -> EmergencyView:
        self.require_mfa()
        with self.uow.open() as w:
            return w.emergency.status(authority, operation)

    def emergency_issue(
        self,
        authority: OperatingRecoveryAuthority,
        request: EmergencyRequest,
        deliver: Callable[[Setup], None],
        commit_observer: Callable[[CommitPhase], None] | None = None,
    ) -> None:
        self.require_mfa()
        with self.uow.open() as w:
            w.emergency.preflight(authority, request.account_id)
        with self.uow.open() as w:
            slot = w.security.allocate("emergency", collect=False)
        try:
            with self.uow.open(commit_observer=commit_observer) as w:
                result, audit = w.emergency.issue(authority, request, slot)
                w.audit.append(Event(**asdict(audit)))
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
        self.require_mfa()
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

    def emergency_begin(
        self,
        token: str,
        password: str | None,
        auth: str | None,
        preauth: str | None,
        nonce: str | None,
    ) -> Ceremony:
        self.emergency_preauth(auth, preauth, nonce)
        with self.uow.open() as w:
            slot = w.security.allocate("mfa", collect=False)
        try:
            with self.uow.open() as w:
                result = w.emergency.begin(token, password, slot)
                w.iam.preparation(preauth, nonce, consume=True)
                return result
        finally:
            self.emergency_release(slot)

    def emergency_password(
        self, token: str, password: str, auth: str | None, preauth: str | None, nonce: str | None
    ) -> None:
        self.emergency_preauth(auth, preauth, nonce)
        with self.uow.open() as w:
            audit = w.emergency.password(token, password)
            w.iam.preparation(preauth, nonce, consume=True)
            w.audit.append(Event(**asdict(audit)))

    def emergency_complete(
        self, token: str | None, nonce: str | None, payload: str, auth: str | None = None
    ) -> None:
        self.emergency_signed_out(auth)
        with self.uow.open() as w:
            proof = w.mfa.verify_registration(token, nonce, payload)
        if proof.purpose != "emergency":
            raise Rejected(401, "invalid_ceremony")
        with self.uow.open() as w:
            w.audit.append(Event(**asdict(w.emergency.complete(token, nonce, proof))))

    def handoff_state(
        self, auth: str | None, ident: UUID, operation: UUID | None = None
    ) -> HandoffState:
        self.require_mfa()
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
        self.require_mfa()
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
                result, change = w.handoff.issue(current.caller, ident, request, slot)
                w.audit.append(Event(**asdict(change)))
                # No initial touch: even an audit/lock wait cannot rescue an idle session.
                final = w.iam.authenticate(auth, management=True, target=ident, touch=False)
                w.iam.csrf(final, nonce)
                w.iam.master_management(final.caller, ident)
                w.handoff.confirm(ident, request.operation_id, slot)
                w.iam.authenticate(auth, management=True, target=ident)
            return result
        finally:
            self.emergency_release(slot)

    def register_trainer(
        self, auth: str | None, nonce: str | None, command: RegisterTrainer
    ) -> RegistrationResult:
        self.require_mfa()
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
        self.require_mfa()
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
        self.require_mfa()
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
        self.require_mfa()
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
        self.require_mfa()
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
            if not fact.active and not (a.caller.master or a.caller.branch_id):
                raise Rejected(401, "unauthorized")
        final = w.iam.authenticate(
            auth, management=management, target=target, touch=False, audience="account"
        )
        if final.binding != a.binding or final.trainer_granted != a.trainer_granted:
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
        self.require_mfa()
        with self.uow.open() as w:
            a = w.iam.authenticate(auth, management=True, touch=False)
            fact = self._trainer_scope(w, a.caller, trainer)
            result = w.iam.trainer_state(a.caller.organization_id, trainer)
            final = w.iam.authenticate(auth, management=True, touch=False)
            self._trainer_scope(w, final.caller, fact.trainer_id)
            return result

    def trainer_account_operation(self, auth: str | None, operation: UUID) -> TrainerOperation:
        self.require_mfa()
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
        self.require_mfa()
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
        self.require_mfa()
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
        self.require_mfa()
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
        self.require_mfa()
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
        self.require_mfa()
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
            role = (
                w.roles.state(a.caller.organization_id, a.binding.trainer_id)
                if a.binding is not None
                else None
            )
            return a.caller, fact, role
