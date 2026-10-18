"""Protected initial installation and explicit single-worker HTTPS development launcher."""

import argparse
import getpass
import json
import os
import stat
import sys
from pathlib import Path

import uvicorn
from sqlalchemy import text
from sqlalchemy.engine import make_url

from y3management.config import load_settings
from y3management.contracts import CommitUncertain
from y3management.database import Database
from y3management.iam.public import Setup
from y3management.ownership import verify_local_target
from y3management.runtime import ProcessGuard
from y3management.uow import UnitOfWork
from y3management.use_cases import Service


class PrivateEnrollmentFile:
    """Linux descriptor-relative creation: no symlink components or secret stdout."""

    def __init__(self, path: str, origin: str) -> None:
        target = Path(path)
        if not target.is_absolute() or ".." in target.parts:
            raise ValueError("PRIVATE_ABSOLUTE_PATH_REQUIRED")
        self.origin = origin
        self.name = target.name
        self.fd = -1
        self.directory = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
        try:
            for component in target.parent.parts[1:]:
                next_fd = os.open(
                    component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=self.directory
                )
                os.close(self.directory)
                self.directory = next_fd
            metadata = os.fstat(self.directory)
            if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) != 0o700:
                raise ValueError("PRIVATE_OWNED_0700_PARENT_REQUIRED")
            self.fd = os.open(
                self.name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=self.directory,
            )
            self.inode = os.fstat(self.fd).st_ino
            os.fchmod(self.fd, 0o600)
            metadata = os.fstat(self.fd)
            if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) != 0o600:
                raise ValueError("PRIVATE_OWNED_0600_FILE_REQUIRED")
        except Exception:
            try:
                if self.fd >= 0:
                    try:
                        created = os.fstat(self.fd)
                        current = os.stat(self.name, dir_fd=self.directory, follow_symlinks=False)
                        if current.st_ino == created.st_ino and current.st_uid == os.getuid():
                            os.unlink(self.name, dir_fd=self.directory)
                    finally:
                        os.close(self.fd)
            finally:
                os.close(self.directory)
            raise

    def deliver(self, setup: Setup) -> None:
        data = (self.origin + "/enroll#token=" + setup.token + "\n").encode()
        with os.fdopen(os.dup(self.fd), "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.fsync(self.directory)

    def close(self, *, remove: bool) -> None:
        try:
            if remove:
                current = os.stat(self.name, dir_fd=self.directory, follow_symlinks=False)
                if current.st_ino == self.inode and current.st_uid == os.getuid():
                    os.unlink(self.name, dir_fd=self.directory)
                    os.fsync(self.directory)
        finally:
            os.close(self.fd)
            os.close(self.directory)


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    initial = commands.add_parser("bootstrap-initial-master")
    initial.add_argument("--organization", required=True)
    initial.add_argument("--login-id", required=True)
    initial.add_argument("--confirm-database", required=True)
    initial.add_argument("--enrollment-file")
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
            delivery = None
            if settings.iam_mode == "mfa":
                if not args.enrollment_file:
                    raise ValueError("ENROLLMENT_FILE_REQUIRED")
                delivery = PrivateEnrollmentFile(args.enrollment_file, settings.canonical_origin)
            elif args.enrollment_file:
                raise ValueError("ENROLLMENT_REQUIRES_MFA_MODE")
            retain = False
            try:
                account = Service(UnitOfWork(database, settings)).bootstrap(
                    args.organization,
                    args.login_id,
                    password,
                    delivery.deliver if delivery else None,
                )
                retain = True
            except CommitUncertain:
                retain = True
                print("INSTALLATION_COMMIT_UNKNOWN_RETAIN_PRIVATE_FILE", file=sys.stderr)
                return 2
            finally:
                if delivery:
                    delivery.close(remove=not retain)
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
