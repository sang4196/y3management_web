"""Only composition point that attaches module-private adapters to a shared DBSession."""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from y3management.audit.infrastructure import Audit
from y3management.audit.public import AuditPort
from y3management.config import Settings
from y3management.contracts import Rejected
from y3management.database import Database
from y3management.iam.infrastructure import IAM
from y3management.iam.passwords import Passwords
from y3management.iam.public import IAMPort, SecurityPort
from y3management.iam.security import Security
from y3management.organization.application import Organization
from y3management.organization.infrastructure import Organization as OrganizationRepository
from y3management.organization.public import OrganizationPort


@dataclass(frozen=True)
class Work:
    iam: IAMPort
    organization: OrganizationPort
    audit: AuditPort
    security: SecurityPort


class UnitOfWork:
    def __init__(self, database: Database, settings: Settings) -> None:
        self.database = database
        self.settings = settings
        self._passwords = Passwords()

    @contextmanager
    def open(self, *, commit_denial: bool = False) -> Iterator[Work]:
        # The whole context is created, used and closed by one synchronous worker.
        try:
            with self.database.session() as session:
                work = Work(
                    IAM(session, self._passwords, self.settings.iam_key.get_secret_value()),
                    Organization(OrganizationRepository(session)),
                    Audit(session),
                    Security(
                        session,
                        self.settings.iam_key.get_secret_value(),
                        self.settings.security_state_capacity or 0,
                        self.settings.auth_session_capacity or 0,
                    ),
                )
                try:
                    yield work
                except Rejected as error:
                    if commit_denial and error.status == 429:
                        session.commit()
                    raise
                session.commit()
        except IntegrityError:
            raise Rejected(409, "conflict") from None
        except SQLAlchemyError:
            raise Rejected(503, "unavailable") from None
