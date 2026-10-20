"""Only composition point that attaches module-private adapters to a shared DBSession."""

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from y3management.audit.infrastructure import Audit
from y3management.audit.public import AuditPort
from y3management.config import Settings
from y3management.contracts import CommitPhase, CommitUncertain, Rejected
from y3management.database import Database
from y3management.iam.emergency import Emergency
from y3management.iam.handoff import Handoff
from y3management.iam.infrastructure import IAM
from y3management.iam.mfa import MFA
from y3management.iam.passwords import Passwords
from y3management.iam.public import EmergencyPort, HandoffPort, IAMPort, MFAPort, SecurityPort
from y3management.iam.security import Security
from y3management.organization.application import Organization
from y3management.organization.infrastructure import Organization as OrganizationRepository
from y3management.organization.public import OrganizationPort
from y3management.workforce.application import Workforce
from y3management.workforce.infrastructure import Repository as WorkforceRepository
from y3management.workforce.public import WorkforcePort


@dataclass(frozen=True)
class Work:
    iam: IAMPort
    organization: OrganizationPort
    audit: AuditPort
    security: SecurityPort
    mfa: MFAPort
    emergency: EmergencyPort
    handoff: HandoffPort
    workforce: WorkforcePort


class UnitOfWork:
    def __init__(self, database: Database, settings: Settings) -> None:
        self.database = database
        self.settings = settings
        self._passwords = Passwords()

    @contextmanager
    def open(
        self,
        *,
        commit_denial: bool = False,
        commit_observer: Callable[[CommitPhase], None] | None = None,
    ) -> Iterator[Work]:
        # The whole context is created, used and closed by one synchronous worker.
        try:
            with self.database.session() as session:
                iam = IAM(
                    session,
                    self._passwords,
                    self.settings.iam_key.get_secret_value(),
                    self.settings.iam_mode,
                )
                work = Work(
                    iam,
                    Organization(OrganizationRepository(session)),
                    Audit(session),
                    Security(
                        session,
                        self.settings.iam_key.get_secret_value(),
                        self.settings.security_state_capacity or 0,
                        self.settings.auth_session_capacity or 0,
                    ),
                    MFA(iam, self.settings.canonical_origin),
                    Emergency(MFA(iam, self.settings.canonical_origin)),
                    Handoff(Emergency(MFA(iam, self.settings.canonical_origin))),
                    Workforce(WorkforceRepository(session)),
                )
                try:
                    yield work
                except Rejected as error:
                    if commit_denial and error.status == 429:
                        session.commit()
                    raise
                if commit_observer is not None:
                    commit_observer("starting")
                try:
                    session.commit()
                except IntegrityError:
                    if commit_observer is not None:
                        commit_observer("rejected")
                    raise
                except SQLAlchemyError:
                    raise CommitUncertain() from None
                if commit_observer is not None:
                    commit_observer("confirmed")
        except IntegrityError:
            raise Rejected(409, "conflict") from None
        except SQLAlchemyError:
            raise Rejected(503, "unavailable") from None
