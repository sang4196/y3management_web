"""Framework-free shared failures; never include submitted values."""

from typing import Literal

type CommitPhase = Literal["starting", "confirmed", "rejected"]


class Rejected(Exception):
    def __init__(self, status: int, detail: str, retry_after: int | None = None) -> None:
        super().__init__(detail)
        self.status = status
        self.detail = detail
        self.retry_after = retry_after


class HashAdmissionRejected(Rejected):
    """No password verification began; externally identical to generic capacity failure."""

    def __init__(self) -> None:
        super().__init__(503, "unavailable")


class CommitUncertain(Rejected):
    """The server cannot prove whether COMMIT was applied; never retry the command blindly."""

    def __init__(self) -> None:
        super().__init__(503, "commit_outcome_unknown")
