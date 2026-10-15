"""Short independent security transactions. No account/session business locks here."""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from y3management.contracts import Rejected
from y3management.iam.public import Preparation, Reservation


class Security:
    def __init__(self, session: Session, key: str, capacity: int, session_capacity: int) -> None:
        self.s = session
        self.key = key.encode()
        self.capacity = capacity
        self.session_capacity = session_capacity

    def now(self) -> datetime:
        value: datetime = self.s.execute(text("SELECT clock_timestamp()")).scalar_one()
        return value

    def _guard(self) -> datetime:
        self.s.execute(text("SELECT id FROM iam_security_control WHERE id=1 FOR UPDATE")).one()
        now = self.now()
        # Consumed/expired transient children only, SKIP LOCKED avoids business lock waits.
        for table in ("iam_preparations", "iam_credentials"):
            rows = self.s.execute(
                text(
                    f"SELECT id FROM {table} WHERE consumed OR expires_at<=:n "
                    "ORDER BY id FOR UPDATE SKIP LOCKED"
                ),
                {"n": now},
            ).scalars()
            for ident in list(rows):
                self.s.execute(text("DELETE FROM iam_security_states WHERE id=:id"), {"id": ident})
        self.s.execute(
            text("""DELETE FROM iam_security_states WHERE kind='attempt' AND
           (expires_at<=:n OR id IN (SELECT id FROM iam_attempts WHERE outcome='success'))"""),
            {"n": now},
        )
        # No live child attempt/cooldown may be evicted to make room for an attacker.
        self.s.execute(
            text("""DELETE FROM iam_security_states s WHERE kind='budget'
          AND expires_at<=:n AND NOT EXISTS
          (SELECT 1 FROM iam_budgets b JOIN iam_attempts a ON a.key=b.key
           WHERE b.state_id=s.id)"""),
            {"n": now},
        )
        self.s.execute(
            text(
                "DELETE FROM iam_security_states WHERE kind='session_slot' "
                "AND NOT EXISTS (SELECT 1 FROM iam_sessions a WHERE a.id=iam_security_states.id) "
                "AND expires_at<=:n"
            ),
            {"n": now},
        )
        self.s.execute(
            text("""DELETE FROM iam_security_states s
          WHERE s.kind IN ('preparation','credential','session_slot')
          AND s.created_at<=:lease_end
          AND NOT EXISTS (SELECT 1 FROM iam_preparations p WHERE p.id=s.id)
          AND NOT EXISTS (SELECT 1 FROM iam_credentials c WHERE c.id=s.id)
          AND NOT EXISTS (SELECT 1 FROM iam_sessions a WHERE a.id=s.id)"""),
            {"lease_end": now - timedelta(seconds=30)},
        )
        return now

    def _allocate(self, kind: str, expires: datetime) -> UUID:
        if kind == "session_slot":
            count = int(
                self.s.execute(
                    text("SELECT count(*) FROM iam_security_states WHERE kind='session_slot'")
                ).scalar_one()
            )
            limit = self.session_capacity
        else:
            count = int(
                self.s.execute(
                    text("SELECT count(*) FROM iam_security_states WHERE kind<>'session_slot'")
                ).scalar_one()
            )
            limit = self.capacity
        if count >= limit:
            raise Rejected(503, "unavailable")
        ident = uuid4()
        self.s.execute(
            text("INSERT INTO iam_security_states(id,kind,expires_at) VALUES(:id,:kind,:expires)"),
            {"id": ident, "kind": kind, "expires": expires},
        )
        return ident

    def allocate(self, kind: str) -> UUID:
        now = self._guard()
        minutes = 480 if kind == "session_slot" else 30
        return self._allocate(kind, now + timedelta(minutes=minutes))

    def release(self, ident: UUID) -> None:
        self._guard()
        self.s.execute(
            text(
                "DELETE FROM iam_security_states s WHERE id=:id "
                "AND NOT EXISTS (SELECT 1 FROM iam_credentials c WHERE c.id=s.id) "
                "AND NOT EXISTS (SELECT 1 FROM iam_sessions a WHERE a.id=s.id) "
                "AND NOT EXISTS (SELECT 1 FROM iam_preparations p WHERE p.id=s.id)"
            ),
            {"id": ident},
        )

    def preparation(self, raw: str | None) -> Preparation:
        now = self._guard()
        if raw:
            row = self.s.execute(
                text(
                    "SELECT csrf FROM iam_preparations WHERE digest=:d "
                    "AND NOT consumed AND expires_at>:n"
                ),
                {"d": hashlib.sha256(raw.encode()).digest(), "n": now},
            ).first()
            if row:
                return Preparation(raw, str(row.csrf))
        token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
        # Five minutes is technical preauth lifetime; never product AuthSession TTL.
        expiry = now + timedelta(minutes=5)
        ident = self._allocate("preparation", expiry)
        self.s.execute(
            text("INSERT INTO iam_preparations VALUES(:id,:d,:csrf,:e,false)"),
            {"id": ident, "d": hashlib.sha256(token.encode()).digest(), "csrf": csrf, "e": expiry},
        )
        return Preparation(token, csrf)

    def reserve(self, login_id: str) -> Reservation:
        now = self._guard()
        key = hmac.digest(self.key, login_id.encode(), "sha256")
        row = self.s.execute(
            text("SELECT state_id,cooldown FROM iam_budgets WHERE key=:k FOR UPDATE"), {"k": key}
        ).first()
        if row is None:
            state_id = self._allocate("budget", now + timedelta(minutes=16))
            self.s.execute(
                text("INSERT INTO iam_budgets VALUES(:k,:id,NULL)"), {"k": key, "id": state_id}
            )
        else:
            state_id = row.state_id
            if row.cooldown and row.cooldown > now:
                raise Rejected(429, "try_later", max(1, int((row.cooldown - now).total_seconds())))
        self.s.execute(
            text(
                "UPDATE iam_attempts SET outcome='failure',finished_at=lease_until "
                "WHERE key=:k AND outcome='pending' AND lease_until<=:n"
            ),
            {"k": key, "n": now},
        )
        failed = int(
            self.s.execute(
                text(
                    "SELECT count(*) FROM iam_attempts WHERE key=:k "
                    "AND outcome='failure' AND finished_at>:start"
                ),
                {"k": key, "start": now - timedelta(minutes=15)},
            ).scalar_one()
        )
        if failed >= 5:
            expiry = now + timedelta(minutes=15)
            self.s.execute(
                text("UPDATE iam_budgets SET cooldown=:e WHERE key=:k"), {"k": key, "e": expiry}
            )
            self.s.execute(
                text(
                    "UPDATE iam_security_states SET expires_at=GREATEST(expires_at,:e) WHERE id=:id"
                ),
                {"id": state_id, "e": expiry},
            )
            # Caller commits this denial, so abandoned-worker penalties persist.
            raise Rejected(429, "try_later", 900)
        pending = int(
            self.s.execute(
                text("SELECT count(*) FROM iam_attempts WHERE key=:k AND outcome='pending'"),
                {"k": key},
            ).scalar_one()
        )
        if pending + failed >= 5:
            raise Rejected(429, "try_later", 1)
        expires = now + timedelta(minutes=16)
        ident = self._allocate("attempt", expires)
        self.s.execute(
            text("INSERT INTO iam_attempts VALUES(:id,:k,'pending',:lease,NULL)"),
            {"id": ident, "k": key, "lease": now + timedelta(seconds=30)},
        )
        self.s.execute(
            text("UPDATE iam_security_states SET expires_at=GREATEST(expires_at,:e) WHERE id=:id"),
            {"id": state_id, "e": expires},
        )
        return Reservation(key, ident)

    def finish(self, reservation: Reservation, success: bool) -> None:
        now = self._guard()
        row = self.s.execute(
            text("SELECT outcome,lease_until FROM iam_attempts WHERE id=:i AND key=:k FOR UPDATE"),
            {"i": reservation.id, "k": reservation.key},
        ).first()
        if row is None or row.outcome != "pending" or row.lease_until <= now:
            raise Rejected(503, "unavailable")
        self.s.execute(
            text("UPDATE iam_attempts SET outcome=:o,finished_at=:n WHERE id=:i"),
            {"o": "success" if success else "failure", "n": now, "i": reservation.id},
        )
        failed = int(
            self.s.execute(
                text(
                    "SELECT count(*) FROM iam_attempts WHERE key=:k "
                    "AND outcome='failure' AND finished_at>:start"
                ),
                {"k": reservation.key, "start": now - timedelta(minutes=15)},
            ).scalar_one()
        )
        if failed >= 5:
            self.s.execute(
                text("UPDATE iam_budgets SET cooldown=:e WHERE key=:k"),
                {"k": reservation.key, "e": now + timedelta(minutes=15)},
            )

    def cancel(self, reservation: Reservation) -> None:
        # Capacity rejection before credential verification is not a failed password.
        self._guard()
        self.s.execute(
            text(
                "DELETE FROM iam_security_states WHERE id=:i AND id IN "
                "(SELECT id FROM iam_attempts WHERE outcome='pending' AND key=:k)"
            ),
            {"i": reservation.id, "k": reservation.key},
        )
