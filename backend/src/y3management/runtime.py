"""One WSL application process per database identity, including direct ASGI launch."""

import hashlib
import os
import stat
from pathlib import Path

from sqlalchemy.engine import make_url

from y3management.config import Settings


class ProcessGuard:
    def __init__(self, settings: Settings) -> None:
        if os.name != "posix":
            raise ValueError("S1_WSL_REQUIRED")
        import fcntl

        if settings.worker_count != 1:
            raise ValueError("SINGLE_WORKER_REQUIRED")
        # Deliberately not configurable per launch: alternate directories bypass exclusion.
        root = Path("/tmp/y3management-runtime")
        root.mkdir(mode=0o700, exist_ok=True)
        st = root.lstat()
        if not stat.S_ISDIR(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o077:
            raise ValueError("UNSAFE_RUNTIME_DIRECTORY")
        u = make_url(settings.database_url.get_secret_value())
        identity = f"{u.port}/{u.database}/{settings.database_schema}"
        name = hashlib.sha256(identity.encode()).hexdigest() + ".lock"
        self._fd = os.open(root / name, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        st = os.fstat(self._fd)
        if st.st_uid != os.getuid() or st.st_mode & 0o077:
            os.close(self._fd)
            raise ValueError("UNSAFE_RUNTIME_LOCK")
        try:
            fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(self._fd)
            raise ValueError("SINGLE_PROCESS_REQUIRED") from None

    def close(self) -> None:
        os.close(self._fd)
