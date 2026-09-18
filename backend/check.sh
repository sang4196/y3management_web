#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
case "${1:-fast}" in
  fast)
    uv run --locked ruff check
    uv run --locked ruff format --check
    uv run --locked mypy
    uv run --locked pytest -m "not postgres"
    uv run --locked lint-imports --no-cache
    ;;
  db)
    uv run --locked --env-file "${2:-.env.example}" pytest -m postgres --require-postgres
    ;;
  *) echo "Usage: bash check.sh [fast|db [env-file]]" >&2; exit 2 ;;
esac
