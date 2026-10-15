"""Pinned offline corpus and bounded Argon2 work, private to IAM."""

import hashlib
import json
import secrets
import threading
import unicodedata
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError
from pwdlib.hashers.argon2 import Argon2Hasher

from y3management.contracts import HashAdmissionRejected, Rejected

ARTIFACT_MANIFEST_SHA256 = "770d4b7aa4d5f75744d5e9b0e8036ad1964ea6747f4768eac490f4cedf95e445"


class Passwords:
    def __init__(self) -> None:
        root = Path(__file__).with_name("data")
        raw = (root / "artifact-manifest.json").read_bytes()
        if hashlib.sha256(raw).hexdigest() != ARTIFACT_MANIFEST_SHA256:
            raise ValueError("CORPUS_INTEGRITY_FAILED")
        manifest: dict[str, str] = json.loads(raw)
        for name, checksum in manifest.items():
            if hashlib.sha256((root / name).read_bytes()).hexdigest() != checksum:
                raise ValueError("CORPUS_INTEGRITY_FAILED")
        self.blocked_digests = frozenset(
            (root / "blocked-sha256.txt").read_text(encoding="ascii").splitlines()
        )
        self.seeds = frozenset((root / "seeds.txt").read_text(encoding="utf-8").splitlines())
        if (
            len(self.blocked_digests) != 55169
            or any(
                len(value) != 64 or not set(value) <= set("0123456789abcdef")
                for value in self.blocked_digests
            )
            or len(self.seeds) != 4
        ):
            raise ValueError("CORPUS_INTEGRITY_FAILED")
        self._hasher = PasswordHash((Argon2Hasher(time_cost=3, memory_cost=65536, parallelism=4),))
        self._slots = threading.BoundedSemaphore(2)
        # No static default password or account: randomized timing equalizer only.
        self._dummy = self._hasher.hash(secrets.token_urlsafe(32))

    @contextmanager
    def capacity(self) -> Iterator[None]:
        if not self._slots.acquire(blocking=False):
            raise HashAdmissionRejected()
        try:
            yield
        finally:
            self._slots.release()

    def policy(self, value: str, login_id: str) -> str:
        p = unicodedata.normalize("NFC", value)
        if not 15 <= len(p) <= 128 or "\x00" in p:
            raise Rejected(422, "password_policy")
        if hashlib.sha256(p.encode("utf-8")).hexdigest() in self.blocked_digests or p in {
            "correct horse battery staple",
            "correcthorsebatterystaple",
        }:
            raise Rejected(422, "password_policy")
        punctuation = ("", "!", "!!", "@", "#", "$", "?", ".")
        for end in punctuation:
            if end and not p.endswith(end):
                continue
            body = p[: -len(end)] if end else p
            if any(len(body) % n == 0 and body == body[:n] * (len(body) // n) for n in range(1, 5)):
                raise Rejected(422, "password_policy")
            if any(body == seed * count for seed in self.seeds for count in range(2, 17)):
                raise Rejected(422, "password_policy")
        year = datetime.now(UTC).year
        roots = {"y3management", "y3gym", "와이쓰리", login_id.casefold()}
        suffixes = {
            "",
            "123",
            "1234",
            "12345",
            "123456",
            "123456789",
            "password",
            "비밀번호",
            "관리자비밀번호",
            *(str(y) for y in range(year - 1, year + 2)),
        }
        if p.casefold() in {
            r + s + e for r in roots for s in suffixes for e in (*punctuation, "1234", "1234!")
        }:
            raise Rejected(422, "password_policy")
        return p  # NFC only; no trim or case conversion of the hash input.

    def create(self, value: str, login_id: str) -> str:
        normalized = self.policy(value, login_id)
        with self.capacity():
            return self._hasher.hash(normalized)

    def verify(self, value: str, encoded: str | None) -> tuple[bool, str | None]:
        p = unicodedata.normalize("NFC", value)
        if len(p) > 128:
            p = "invalid-length"
        with self.capacity():
            try:
                valid, updated = self._hasher.verify_and_update(p, encoded or self._dummy)
            except UnknownHashError:
                # Corrupt persisted credentials must fail closed, never act as dummy success.
                raise Rejected(503, "unavailable") from None
        return (valid and encoded is not None), updated
