"""Protected initial installation and explicit single-worker HTTPS development launcher."""

import argparse
import getpass
import json
import os
import stat
import sys
from dataclasses import asdict
from pathlib import Path
from uuid import UUID

import uvicorn
from sqlalchemy import text
from sqlalchemy.engine import make_url

from y3management.config import Settings, load_settings
from y3management.contracts import CommitPhase, CommitUncertain
from y3management.database import Database
from y3management.iam.public import Setup
from y3management.operating import authority, execution
from y3management.ownership import verify_local_target
from y3management.runtime import ProcessGuard
from y3management.uow import UnitOfWork
from y3management.use_cases import Service


class PrivateEnrollmentFile:
    """Linux descriptor-relative creation: no symlink components or secret stdout."""

    def __init__(self, path: str, origin: str, *, emergency: bool = False) -> None:
        self.route = "/emergency-recover" if emergency else "/enroll"
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
        data = (self.origin + self.route + "#token=" + setup.token + "\n").encode()
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


def emergency_diagnostic(message: str) -> None:
    try:
        try:
            fd = sys.stderr.fileno()
        except (AttributeError, OSError, ValueError):
            print(message, file=sys.stderr, flush=True)
        else:
            # Do not leave failed diagnostic bytes buffered for interpreter shutdown.
            sys.stderr.flush()
            remaining = (message + "\n").encode()
            while remaining:
                written = os.write(fd, remaining)
                if written <= 0:
                    break
                remaining = remaining[written:]
    except (Exception, KeyboardInterrupt, SystemExit):
        # A lost diagnostic must not reclassify an already committed operation.
        pass


def emergency_receipt(value: dict[str, object]) -> None:
    payload = json.dumps(value, default=str) + "\n"
    try:
        fd = sys.stdout.fileno()
    except (AttributeError, OSError, ValueError):
        print(payload, end="", flush=True)
    else:
        # Unbuffered receipt avoids a second EPIPE at interpreter shutdown
        # overwriting the explicit reconciliation exit code.
        sys.stdout.flush()
        remaining = payload.encode()
        while remaining:
            written = os.write(fd, remaining)
            if written <= 0:
                raise OSError("RECEIPT_WRITE_FAILED")
            remaining = remaining[written:]


def emergency_command(args: argparse.Namespace, settings: Settings) -> int:
    phase = "precommit"
    outcome = 0
    guard: ProcessGuard | None = None
    database: Database | None = None
    delivery: PrivateEnrollmentFile | None = None
    result: dict[str, object] | None = None

    def observed(event: CommitPhase) -> None:
        nonlocal phase
        phase = {"starting": "committing", "confirmed": "committed", "rejected": "precommit"}[event]

    try:
        if (
            (
                args.operation == "inspect"
                and (
                    not args.account_id
                    or args.operation_id
                    or args.request_file
                    or args.output_file
                )
            )
            or (
                args.operation == "status"
                and (
                    not args.operation_id
                    or args.account_id
                    or args.request_file
                    or args.output_file
                )
            )
            or (
                args.operation == "execute"
                and (
                    not args.request_file
                    or not args.output_file
                    or args.account_id
                    or args.operation_id
                )
            )
        ):
            raise ValueError("OPERATING_ARGUMENTS_REQUIRED")
        if args.confirm_schema != settings.database_schema:
            raise ValueError("SCHEMA_CONFIRMATION_REQUIRED")
        principal = authority(settings, args.organization_id, args.operation)
        request = execution(settings, args.request_file) if args.operation == "execute" else None
        if request and request.organization_id != args.organization_id:
            raise ValueError("ORGANIZATION_CONFIRMATION_REQUIRED")
        guard = ProcessGuard(settings)
        database = Database(settings)
        u = make_url(settings.database_url.get_secret_value())
        with database.session() as session:
            row = session.execute(
                text("SELECT current_database(),current_user,current_schema()")
            ).one()
            if tuple(row) != (u.database, u.username, settings.database_schema):
                raise ValueError("UNVERIFIED_OPERATING_TARGET")
        service = Service(UnitOfWork(database, settings))
        if args.operation == "inspect":
            result = asdict(service.emergency_inspect(principal, args.account_id))
        elif args.operation == "status":
            result = asdict(service.emergency_status(principal, args.operation_id))
        elif request is not None:
            delivery = PrivateEnrollmentFile(
                args.output_file, settings.canonical_origin, emergency=True
            )
            service.emergency_issue(principal, request, delivery.deliver, commit_observer=observed)
            phase = "committed"
            result = {"operation_id": str(request.operation_id), "status": "issued"}
    except CommitUncertain:
        if args.operation == "execute":
            phase = "unknown"
            outcome = 2
            emergency_diagnostic("EMERGENCY_COMMIT_UNKNOWN_RETAIN_PRIVATE_FILE_CHECK_STATUS")
        else:
            outcome = 1
            emergency_diagnostic("EMERGENCY_READ_FAILED")
    except (Exception, KeyboardInterrupt, SystemExit):
        if phase == "committing":
            phase = "unknown"
        outcome = 2 if phase != "precommit" else 1
        emergency_diagnostic(
            {
                "committed": "EMERGENCY_COMMITTED_CHECK_STATUS",
                "unknown": "EMERGENCY_COMMIT_UNKNOWN_RETAIN_PRIVATE_FILE_CHECK_STATUS",
                "precommit": "EMERGENCY_COMMAND_FAILED",
            }[phase]
        )
    finally:
        if delivery is not None:
            try:
                delivery.close(remove=phase == "precommit")
            except (Exception, KeyboardInterrupt, SystemExit):
                outcome = 2 if phase != "precommit" else 1
                emergency_diagnostic(
                    "EMERGENCY_" + phase.upper() + "_OUTPUT_CLOSE_FAILED_CHECK_STATUS"
                )
        # Every owned resource gets its cleanup attempt even if a prior close failed.
        for resource in (database, guard):
            if resource is not None:
                try:
                    resource.close()
                except (Exception, KeyboardInterrupt, SystemExit):
                    outcome = 2 if phase != "precommit" else 1
                    emergency_diagnostic(
                        "EMERGENCY_" + phase.upper() + "_CLEANUP_FAILED_CHECK_STATUS"
                    )
    if outcome == 0 and result is not None:
        try:
            emergency_receipt(result)
        except (Exception, KeyboardInterrupt, SystemExit):
            outcome = 2 if phase == "committed" else 1
            emergency_diagnostic(
                "EMERGENCY_COMMITTED_RECEIPT_LOST_CHECK_STATUS"
                if phase == "committed"
                else "EMERGENCY_READ_RECEIPT_FAILED"
            )
    return outcome


def main() -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    initial = commands.add_parser("bootstrap-initial-master")
    initial.add_argument("--organization", required=True)
    initial.add_argument("--login-id", required=True)
    initial.add_argument("--confirm-database", required=True)
    initial.add_argument("--enrollment-file")
    emergency = commands.add_parser("emergency-recovery")
    emergency.add_argument("operation", choices=("inspect", "execute", "status"))
    emergency.add_argument("--organization-id", required=True, type=UUID)
    emergency.add_argument("--confirm-database", required=True)
    emergency.add_argument("--confirm-schema", required=True)
    emergency.add_argument("--account-id", type=UUID)
    emergency.add_argument("--operation-id", type=UUID)
    emergency.add_argument("--request-file")
    emergency.add_argument("--output-file")
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
        if args.command == "emergency-recovery":
            return emergency_command(args, settings)
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
