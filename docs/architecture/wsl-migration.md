# WSL migration validation — 2026-09-18

User-authorized migration to `/home/shlee/Workspace/ai/01.codex/y3management_web` on Ubuntu 26.04.1 WSL2. Original Windows source is retained at `D:\Workspace\ai\01.codex.windows-backup-20260918\y3management_web`.

Python 3.13.15, uv 0.12.16, and a fresh Linux virtual environment use the unchanged uv.lock. Added backend/check.sh and extended only the integration fixture's explicit local Docker endpoint selection. Windows retains desktop-linux/npipe; WSL uses wsl-ubuntu/unix:///run/docker-wsl.sock. Compose ownership, host port, database/role, no-skip, and required-test gates remain enforced.

Verified on the native Ubuntu Docker Engine 29.8.1, Compose 5.5.1:
- `bash check.sh fast`: Ruff lint/format, mypy (13 files), 36 pytest passes, 2 Import Linter contracts kept.
- `bash check.sh db`: 3 real PostgreSQL integration tests passed, 36 deselected, no skipped tests. Includes actual connection/transaction/health and online Alembic current coverage from the existing tests.
- PostgreSQL 17.11 project services postgres-dev and postgres-test are running with separate volumes at 127.0.0.1:55432 and 55433.
- Existing FastAPI/Starlette deprecation warnings remain non-failing.

The initial migration check used the Docker Desktop socket because its WSL integration had rebound the default socket. A separate native WSL endpoint was configured and the checks above were repeated against it. Only the temporary Desktop test container/volume/network created during this migration were removed; unrelated Desktop containers were preserved.

Historical FOUNDATION-001/002 records describe their original Windows results. This validation does not retroactively change them, approve new product behavior, create business schemas, or claim production readiness. No application code, dependency versions, commits, or pushes were changed.
