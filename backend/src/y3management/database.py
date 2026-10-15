"""SQLAlchemy sessions are database resources, not completed PTSession records."""

from collections.abc import Iterator
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import contextmanager
from threading import Lock

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session as DatabaseSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from y3management.config import Settings


class Database:
    def __init__(self, settings: Settings) -> None:
        options = {
            "connect_timeout": settings.db_connect_timeout_seconds,
            "options": (
                f"-c statement_timeout={settings.db_statement_timeout_ms} "
                f"-c lock_timeout={settings.db_statement_timeout_ms} "
                f"-c search_path={settings.database_schema},pg_catalog"
            ),
        }
        self.engine = create_engine(
            settings.database_url.get_secret_value(),
            connect_args=options,
            pool_timeout=settings.db_pool_timeout_seconds,
            hide_parameters=True,
            echo=False,
        )
        self.session_factory = sessionmaker(
            self.engine,
            expire_on_commit=False,
            close_resets_only=False,
        )
        # Separate, unpooled probe: it cannot exhaust the future business pool.
        self._probe_engine = create_engine(
            settings.database_url.get_secret_value(),
            connect_args=options,
            poolclass=NullPool,
            hide_parameters=True,
            echo=False,
        )
        self._timeout = settings.readiness_timeout_seconds
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="db-readiness")
        self._lock = Lock()
        self._pending: Future[bool] | None = None
        self._closed = False

    @contextmanager
    def session(self) -> Iterator[DatabaseSession]:
        """Independent lifetime, no automatic commit. Caller owns begin/commit."""
        with self.session_factory() as db_session:
            yield db_session
        # Session.close rolls back any unfinished transaction, including on exceptions.

    def _probe(self) -> bool:
        try:
            with self._probe_engine.connect() as connection:
                return bool(connection.execute(text("SELECT 1")).scalar_one() == 1)
        except Exception:
            # Never return or log driver exceptions (may contain DSN and credentials).
            return False

    def is_ready(self) -> bool:
        with self._lock:
            if self._closed:
                return False
            if self._pending is None or self._pending.done():
                self._pending = self._executor.submit(self._probe)
            pending = self._pending
        try:
            return pending.result(timeout=self._timeout)
        except Exception:
            return False

    def close(self) -> None:
        with self._lock:
            self._closed = True
        # A running driver call cannot be killed by Python. Do not queue new work.
        self._executor.shutdown(wait=False, cancel_futures=True)
        self.engine.dispose()
        self._probe_engine.dispose()
