"""Base plan policy; no Settlement or historical employment inference."""

import hashlib
import json
from dataclasses import asdict, replace
from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from y3management.contracts import Rejected
from y3management.iam.public import Caller
from y3management.workforce.base_infrastructure import BaseRepository
from y3management.workforce.public import (
    BaseCommand,
    BaseFact,
    BasePage,
    BaseQuery,
    BaseResult,
    BaseSnapshot,
    PreparedBase,
    TrainerIdentityFact,
)
from y3management.workforce.validation import money, month


def business_month(clock: datetime) -> str:
    local = clock.astimezone(ZoneInfo("Asia/Seoul"))
    return f"{local.year:04d}-{local.month:02d}"


class BaseSchedules:
    def __init__(self, base_repository: BaseRepository) -> None:
        self.base_repo = base_repository

    def _base_scope(self, caller: Caller, fact: TrainerIdentityFact) -> None:
        if not caller.master and caller.branch_id is None:
            raise Rejected(403, "forbidden")
        if caller.organization_id != fact.organization_id or (
            not caller.master and caller.branch_id != fact.home_branch_id
        ):
            raise Rejected(404, "not_found")

    def _base_fingerprint(self, caller: Caller, trainer: UUID, request: BaseCommand) -> bytes:
        return hashlib.sha256(
            json.dumps(
                {
                    **asdict(request),
                    "actor_id": caller.account_id,
                    "trainer_id": trainer,
                    "canonical_version": 1,
                },
                sort_keys=True,
                default=str,
                separators=(",", ":"),
            ).encode()
        ).digest()

    def base_head(self, caller: Caller, trainer: UUID) -> BaseSnapshot:
        fact = self.base_repo.identity(caller.organization_id, trainer)
        self._base_scope(caller, fact)
        version = self.base_repo.ledger(caller.organization_id, trainer)
        anchor = self.base_repo.anchor(caller.organization_id, trainer)
        return BaseSnapshot(
            trainer, fact.home_branch_id, fact.version, version, anchor, None, (), 0
        )

    def base_history_token(
        self,
        snapshot: BaseSnapshot,
        offset: int,
        limit: int,
        expected_ledger: int | None,
        expected_month: str | None,
        clock: datetime,
    ) -> str:
        if (
            offset < 0
            or not 1 <= limit <= 100
            or (offset and (expected_ledger is None or expected_month is None))
        ):
            raise Rejected(422, "invalid_request")
        if expected_month is not None:
            month(expected_month)
        current_month = business_month(clock)
        if (expected_ledger is not None and expected_ledger != snapshot.base_ledger_version) or (
            expected_month is not None and expected_month != current_month
        ):
            raise Rejected(409, "conflict")
        return current_month

    def base_snapshot(self, caller: Caller, trainer: UUID, query: BaseQuery) -> BaseSnapshot:
        month(query.basis_month)
        if query.offset < 0 or not 1 <= query.limit <= 100:
            raise Rejected(422, "invalid_request")
        snapshot, fact = self.base_repo.snapshot(caller.organization_id, trainer, query)
        self._base_scope(caller, fact)
        return snapshot

    def base_page(self, snapshot: BaseSnapshot, query: BaseQuery, clock: datetime) -> BasePage:
        if query.expected_server_business_month is not None:
            month(query.expected_server_business_month)
        if query.expected_basis_month is not None:
            month(query.expected_basis_month)
        current_month = business_month(clock)
        if query.offset and (
            query.expected_base_ledger_version is None
            or query.expected_server_business_month is None
            or query.expected_basis_month is None
        ):
            raise Rejected(422, "invalid_request")
        if (
            (
                query.expected_base_ledger_version is not None
                and query.expected_base_ledger_version != snapshot.base_ledger_version
            )
            or (
                query.expected_server_business_month is not None
                and query.expected_server_business_month != current_month
            )
            or (
                query.expected_basis_month is not None
                and query.expected_basis_month != query.basis_month
            )
        ):
            raise Rejected(409, "conflict")

        def eligibility(fact: BaseFact) -> BaseFact:
            return replace(
                fact,
                cancellable=not fact.is_initial
                and fact.active
                and fact.start_month > current_month,
            )

        return BasePage(
            snapshot.trainer_id,
            snapshot.home_branch_id,
            snapshot.trainer_version,
            snapshot.base_ledger_version,
            query.basis_month,
            current_month,
            clock,
            snapshot.anchor,
            eligibility(snapshot.projection) if snapshot.projection else None,
            tuple(eligibility(f) for f in snapshot.items),
            snapshot.total,
        )

    def base_operation_target(self, organization: UUID, operation: UUID) -> UUID | None:
        return self.base_repo.operation_target(organization, operation)

    def base_operation(self, caller: Caller, operation: UUID) -> BaseResult | None:
        found = self.base_repo.operation(caller.organization_id, operation)
        if found is None:
            return None
        result, actor, _ = found
        if actor != caller.account_id:
            raise Rejected(404, "not_found")
        self._base_scope(caller, self.base_repo.identity(caller.organization_id, result.trainer_id))
        return result

    def base_replay(self, caller: Caller, trainer: UUID, request: BaseCommand) -> BaseResult | None:
        found = self.base_repo.operation(caller.organization_id, request.operation_id)
        if found is None:
            return None
        result, actor, digest = found
        self._base_scope(caller, self.base_repo.identity(caller.organization_id, trainer))
        if actor != caller.account_id or digest != self._base_fingerprint(caller, trainer, request):
            raise Rejected(409, "operation_conflict")
        return result

    def prepare_base(
        self, caller: Caller, fact: TrainerIdentityFact, request: BaseCommand
    ) -> PreparedBase:
        self._base_scope(caller, fact)
        if (
            type(request.expected_base_ledger_version) is not int
            or request.expected_base_ledger_version < 1
            or type(request.expected_trainer_version) is not int
            or request.expected_trainer_version < 1
        ):
            raise Rejected(422, "invalid_request")
        if request.kind == "create":
            if (
                request.start_month is None
                or request.planned_amount_won is None
                or request.change_id is not None
                or request.expected_change_revision is not None
            ):
                raise Rejected(422, "invalid_request")
            month(request.start_month)
            money(request.planned_amount_won)
        elif request.kind in ("edit", "cancel"):
            if (
                request.change_id is None
                or type(request.expected_change_revision) is not int
                or request.expected_change_revision < 1
                or request.start_month is not None
            ):
                raise Rejected(422, "invalid_request")
            if request.kind == "edit":
                if request.planned_amount_won is None:
                    raise Rejected(422, "invalid_request")
                money(request.planned_amount_won)
            elif request.planned_amount_won is not None:
                raise Rejected(422, "invalid_request")
        else:
            raise Rejected(422, "invalid_request")
        return self.base_repo.prepare(
            caller, fact, request, self._base_fingerprint(caller, fact.trainer_id, request)
        )

    def confirm_base(self, prepared: PreparedBase, caller: Caller) -> None:
        m = prepared.mutation
        fact = self.base_repo.identity(m.organization_id, m.trainer_id)
        self._base_scope(caller, fact)
        if (
            fact.version != prepared.expected_trainer_version
            or fact.home_branch_id != m.target_home
            or self.base_repo.ledger(m.organization_id, m.trainer_id) != m.after_ledger_version
            or self.base_repo.change(m.organization_id, m.trainer_id, m.change_id)
            != BaseFact(
                m.change_id,
                f"{m.start_month.year:04d}-{m.start_month.month:02d}",
                m.after_amount,
                m.after_revision,
                m.after_active,
            )
        ):
            raise Rejected(409, "conflict")

    def seal_base(self, prepared: PreparedBase, clock: datetime) -> BaseResult:
        if prepared.mutation.start_month <= month(business_month(clock)):
            raise Rejected(409, "schedule_no_longer_future")
        return self.base_repo.seal(prepared, clock, business_month(clock))
