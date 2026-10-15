"""Application orchestration: one business commit, with required audit in the same UoW."""

import logging
import re
from uuid import UUID

from y3management.audit.public import Event
from y3management.contracts import HashAdmissionRejected, Rejected
from y3management.iam.public import Account, Caller, Preparation, Reservation, Setup
from y3management.organization.public import Branch, BranchPage
from y3management.uow import UnitOfWork


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
    )


class Service:
    def __init__(self, uow: UnitOfWork) -> None:
        self.uow = uow

    def bootstrap(self, name: str, identifier: str, password: str) -> Account:
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
                    a = w.iam.authenticate(auth, touch=False)
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
                proof = w.iam.verify_login(identifier, password)
                if proof is None:
                    raise Rejected(401, "invalid_credentials")
                # Only unlocked read snapshots exist here; security locks end before business locks.
                with self.uow.open() as security:
                    sid = security.security.allocate("session_slot")
                token, account = w.iam.login(proof, sid, preauth, nonce)
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
            return w.iam.authenticate(auth, touch=False).caller

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
                a = w.iam.authenticate(auth, touch=False)
                w.iam.csrf(a, nonce)
                w.iam.logout(a)
                w.audit.append(event("logout", a.caller, a.caller.account_id))
        except Rejected as error:
            if error.status != 401:
                raise
            with self.uow.open() as w:
                w.iam.preparation(preauth, nonce, consume=True)
