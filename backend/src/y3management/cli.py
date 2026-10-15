"""Protected initial installation and explicit single-worker HTTPS development launcher."""

import argparse
import getpass
import json
import sys
from pathlib import Path

import uvicorn
from sqlalchemy import text
from sqlalchemy.engine import make_url

from y3management.config import load_settings
from y3management.database import Database
from y3management.ownership import verify_local_target
from y3management.runtime import ProcessGuard
from y3management.uow import UnitOfWork
from y3management.use_cases import Service


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    initial = commands.add_parser("bootstrap-initial-master")
    initial.add_argument("--organization", required=True)
    initial.add_argument("--login-id", required=True)
    initial.add_argument("--confirm-database", required=True)
    serve = commands.add_parser("serve")
    serve.add_argument("--cert", required=True)
    serve.add_argument("--key", required=True)
    serve.add_argument("--port", required=True, type=int)
    args = parser.parse_args()
    try:
        settings = load_settings()
        if not settings.iam_enabled:
            raise ValueError("IAM_NOT_ENABLED")
        if args.command == "serve":
            uvicorn.run(
                "y3management.main:create_app",
                factory=True,
                host="127.0.0.1",
                port=args.port,
                workers=1,
                reload=False,
                proxy_headers=False,
                ssl_certfile=args.cert,
                ssl_keyfile=args.key,
                access_log=False,
                limit_concurrency=32,
                log_config=str(Path(__file__).resolve().parents[2] / "logging.json"),
            )
            return 0
        if not sys.stdin.isatty():
            raise ValueError("INTERACTIVE_TERMINAL_REQUIRED")
        verify_local_target(settings)
        u = make_url(settings.database_url.get_secret_value())
        if args.confirm_database != u.database:
            raise ValueError("DATABASE_CONFIRMATION_REQUIRED")
        password = getpass.getpass("Initial Master password: ")
        confirmation = getpass.getpass("Confirm password: ")
        if password != confirmation:
            raise ValueError("PASSWORD_CONFIRMATION_FAILED")
        guard = ProcessGuard(settings)
        database = Database(settings)
        try:
            with database.session() as session:
                row = session.execute(
                    text("SELECT current_database(),current_user,current_schema()")
                ).one()
                if tuple(row) != (u.database, u.username, settings.database_schema):
                    raise ValueError("UNVERIFIED_BOOTSTRAP_TARGET")
            account = Service(UnitOfWork(database, settings)).bootstrap(
                args.organization, args.login_id, password
            )
            print(
                json.dumps(
                    {"account_id": str(account.id), "organization_id": str(account.organization_id)}
                )
            )
        finally:
            database.close()
            guard.close()
        return 0
    except Exception:
        print("IAM_COMMAND_FAILED", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
