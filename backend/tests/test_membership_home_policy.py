"""Local contract regression: source-only write ACK never becomes a post-move read grant."""

from collections.abc import Callable
from dataclasses import asdict, replace
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest

from y3management.contracts import Rejected
from y3management.iam.public import Caller, OperatorScope
from y3management.membership.application import Membership
from y3management.membership.public import (
    Member,
    MemberCommand,
    MemberMutation,
    MemberResult,
    MemberValues,
)
from y3management.organization.public import MemberBranchFact


class Memory:
    def __init__(self) -> None:
        self.org, self.actor, self.source, self.target, self.ident = [uuid4() for _ in range(5)]
        self.before = Member(
            self.ident,
            1,
            MemberValues("가상 회원", "01020000000"),
            self.source,
            False,
            datetime.now(UTC),
        )
        self.current = self.before
        self.rows: dict[UUID, tuple[MemberResult, UUID, bytes]] = {}
        self.prepared = 0
        self.facts = {
            self.source: MemberBranchFact(self.org, self.source, False, 1, "출발"),
            self.target: MemberBranchFact(self.org, self.target, True, 1, "목적"),
        }

    def home(self, org: UUID, ident: UUID) -> UUID:
        assert org == self.org and ident == self.ident
        return self.current.home_branch_id

    def get(self, org: UUID, ident: UUID) -> Member:
        assert org == self.org and ident == self.ident
        return self.current

    def operation(self, org: UUID, ident: UUID) -> Any:
        assert org == self.org
        row = self.rows.get(ident)
        return (replace(row[0], current_member=self.current), row[1], row[2]) if row else None

    def prepare(
        self,
        caller: Caller,
        c: MemberCommand,
        before: Member,
        home: UUID,
        active: bool,
        actor_role: str,
        actor_branch: UUID | None,
        changed: bool,
        fingerprint: bytes,
    ) -> Any:
        assert actor_role in {"MASTER", "BRANCH_ADMIN"}
        self.prepared += 1
        self.current = replace(
            before, version=before.version + int(changed), home_branch_id=home, active=active
        )
        result = MemberResult(c.operation_id, c.kind, changed, self.current, self.current)
        self.rows[c.operation_id] = (result, caller.account_id, fingerprint)
        mutation = MemberMutation(
            self.org,
            c.operation_id,
            self.ident,
            caller.account_id,
            actor_role,
            actor_branch,
            home,
            c.kind,
            before.version,
            self.current.version,
            changed,
            self.current.recorded_at,
        )
        return result, mutation if changed else None

    def lock_member_home_pair(self, caller: Caller, source: UUID, target: UUID) -> Any:
        assert caller.master or caller.branch_id == source
        return self.facts[source], self.facts[target]

    def lock_member_branch(self, caller: Caller, ident: UUID) -> MemberBranchFact:
        return self.facts[ident]


def setup() -> tuple[Memory, Membership, Caller, MemberCommand]:
    m = Memory()
    app = Membership(m, m)  # type: ignore[arg-type]
    caller = Caller(m.actor, m.org, m.source, False)
    command = MemberCommand(uuid4(), "move_home", m.ident, 1, home_branch_id=m.target)
    return m, app, caller, command


def test_inactive_source_ba_gets_minimal_ack_then_loses_receipt_and_replay_access() -> None:
    m, app, caller, command = setup()
    ack, mutation, proof = app.move_home(caller, command)
    assert mutation is not None and proof is not None
    app.confirm_move(caller, ack, proof)
    assert m.current.active is False and m.current.values == m.before.values
    assert m.current.home_branch_id == m.target and m.current.version == 2
    assert set(asdict(ack)) == {
        "operation_id",
        "changed",
        "member_id",
        "committed_member_version",
        "kind",
    }
    actions: list[Callable[[], object]] = [
        lambda: app.move_operation(caller, command.operation_id),
        lambda: app.move_home(caller, command),
    ]
    for action in actions:
        with pytest.raises(Rejected) as error:
            action()
        assert error.value.status == 404
    assert m.prepared == 1


def test_current_authority_and_original_actor_are_both_required_for_move_receipt() -> None:
    m, app, caller, command = setup()
    ack, _, _ = app.move_home(caller, command)
    with pytest.raises(Rejected):
        app.move_operation(Caller(uuid4(), m.org, None, True), command.operation_id)
    current = Caller(m.actor, m.org, m.target, False)
    assert app.move_operation(current, command.operation_id) == ack
    assert app.move_home(current, command)[0] == ack
    assert m.prepared == 1


def test_old_member_receipt_does_not_label_committed_source_with_current_target_metadata() -> None:
    m, app, caller, _ = setup()
    operation = uuid4()
    m.current = replace(m.before, version=2, home_branch_id=m.target)
    m.rows[operation] = (
        MemberResult(operation, "create", True, m.before, m.before),
        m.actor,
        b"unused",
    )
    result = app.operation(replace(caller, master=True), operation)
    assert result.committed_member.home_branch_id == m.source
    assert (
        result.committed_member.home_branch_name is None
        and result.committed_member.home_active is None
    )
    assert (
        result.current_member.home_branch_id == m.target
        and result.current_member.home_branch_name == "목적"
    )


def test_same_active_home_is_cas_noop_and_inactive_destination_still_rejected() -> None:
    m, app, caller, command = setup()
    m.facts[m.source] = replace(m.facts[m.source], active=True)
    same = replace(command, home_branch_id=m.source)
    ack, mutation, proof = app.move_home(caller, same)
    assert not ack.changed and mutation is None and m.current.version == 1
    app.confirm_move(caller, ack, proof)
    with pytest.raises(Rejected) as stale:
        app.move_home(caller, replace(same, operation_id=uuid4(), expected_member_version=2))
    assert stale.value.status == 409
    m.facts[m.source] = replace(m.facts[m.source], active=False)
    with pytest.raises(Rejected, match="branch_inactive"):
        app.move_home(caller, replace(same, operation_id=uuid4()))
    m.facts[m.target] = replace(m.facts[m.target], active=False)
    with pytest.raises(Rejected, match="branch_inactive"):
        app.move_home(caller, replace(command, operation_id=uuid4()))


def test_operator_edit_scope_never_grants_home_move_authority() -> None:
    m, app, caller, command = setup()
    operator = replace(caller, branch_id=None, operator=OperatorScope(m.source, 1))
    with pytest.raises(Rejected) as error:
        app.move_home(operator, command)
    assert error.value.status == 404 and m.prepared == 0
