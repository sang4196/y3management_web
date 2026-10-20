# ruff: noqa: F811
"""Real trusted HTTPS browser acceptance; no certificate bypass or global trust writes."""

import hashlib
import json
import re
import secrets
import shutil
import socket
import ssl
import subprocess
import time
import urllib.request
from pathlib import Path

import pytest

from tests.browser_result import REQUIRED, validate_browser_report
from tests.conftest import _qa_write, qa_register_process, qa_root, qa_stop_process
from tests.test_iam import child_env, iam  # noqa: F401
from tests.test_iam_mfa import mfa  # noqa: F401
from y3management.config import Settings
from y3management.database import Database

pytestmark = pytest.mark.postgres


def test_actual_https_browser(iam: tuple[Settings, Database, str], tmp_path: Path) -> None:  # noqa: F811
    settings, _, password = iam
    run_browser(settings, password, tmp_path)


def test_actual_https_mfa_browser(mfa: tuple[Settings, Database, str, str], tmp_path: Path) -> None:
    settings, _, password, token = mfa
    run_browser(settings, password, tmp_path, token)


def run_browser(
    settings: Settings,
    password: str,
    tmp_path: Path,
    token: str | None = None,
    *,
    emergency_db: Database | None = None,
) -> None:
    root = tmp_path / "https-browser"
    root.mkdir(mode=0o700)
    if token and emergency_db is None:
        for name in (
            "management.cjs",
            "management-checks.json",
            "reset.cjs",
            "reset-checks.json",
            "master-management.cjs",
            "master-management-checks.json",
        ):
            shutil.copyfile(Path(__file__).parent / "browser" / name, root / name)

    def command(args: list[str]) -> None:
        result = subprocess.run(args, capture_output=True, timeout=30)
        assert result.returncode == 0, "HTTPS prerequisite command failed (details suppressed)"

    def trust() -> dict[str, str]:
        return {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for base in ["/etc/ssl/certs", "/home/shlee/.pki", "/home/shlee/.local/share/pki"]
            for p in Path(base).rglob("*")
            if p.is_file() and not p.is_symlink()
        }

    before = trust()
    command(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(root / "ca.key"),
            "-out",
            str(root / "ca.crt"),
            "-days",
            "2",
            "-subj",
            "/CN=S1 Test CA",
            "-addext",
            "keyUsage=critical,keyCertSign,cRLSign",
        ]
    )
    command(
        [
            "openssl",
            "req",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-keyout",
            str(root / "server.key"),
            "-out",
            str(root / "server.csr"),
            "-subj",
            "/CN=localhost",
        ]
    )
    (root / "ext").write_text(
        "subjectAltName=DNS:localhost,IP:127.0.0.1\nextendedKeyUsage=serverAuth\nbasicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\nsubjectKeyIdentifier=hash\nauthorityKeyIdentifier=keyid,issuer\n"
    )
    command(
        [
            "openssl",
            "x509",
            "-req",
            "-in",
            str(root / "server.csr"),
            "-CA",
            str(root / "ca.crt"),
            "-CAkey",
            str(root / "ca.key"),
            "-CAcreateserial",
            "-out",
            str(root / "server.crt"),
            "-days",
            "2",
            "-extfile",
            str(root / "ext"),
        ]
    )
    for f in root.glob("*.key"):
        f.chmod(0o600)
    nss = root / "shadow-home/.local/share/pki/nssdb"
    nss.mkdir(parents=True)
    package = subprocess.run(
        ["apt", "download", "libnss3-tools"], cwd=root, capture_output=True, timeout=30
    )
    assert package.returncode == 0, "NSS tools download failed"
    command(["dpkg-deb", "-x", str(next(root.glob("*.deb"))), str(root / "nss-tools")])
    certutil = str(root / "nss-tools/usr/bin/certutil")
    command([certutil, "-N", "-d", "sql:" + str(nss), "--empty-password"])
    command(
        [
            certutil,
            "-A",
            "-d",
            "sql:" + str(nss),
            "-n",
            "s1-ca",
            "-t",
            "C,,",
            "-i",
            str(root / "ca.crt"),
        ]
    )
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    origin = f"https://localhost:{port}"
    env = child_env(settings)
    env["Y3_CANONICAL_ORIGIN"] = origin
    inputs = {
        "origin": origin,
        "enrollmentToken": token,
        "masterPassword": password,
        "branchPassword": "브라우저 가상 암호 " + secrets.token_urlsafe(24),
    }
    (root / "input.json").write_text(json.dumps(inputs))
    (root / "input.json").chmod(0o600)
    shutil.copy(
        Path(__file__).parent
        / (
            "browser/emergency.cjs"
            if emergency_db
            else ("browser/mfa.cjs" if token else "browser/s1.cjs")
        ),
        root / "browser.cjs",
    )
    shutil.copy(
        Path(__file__).parent
        / (
            "browser/emergency-checks.json"
            if emergency_db
            else ("browser/mfa-checks.json" if token else "browser/required-checks.json")
        ),
        root / "required-checks.json",
    )
    log = (root / "server.log").open("wb")
    server = subprocess.Popen(
        [
            str(Path.cwd() / ".venv/bin/python"),
            "-m",
            "y3management.cli",
            "serve",
            "--cert",
            str(root / "server.crt"),
            "--key",
            str(root / "server.key"),
            "--port",
            str(port),
        ],
        env=env,
        stdout=log,
        stderr=log,
    )
    qa_register_process(server, port=port)
    try:
        context = ssl.create_default_context(cafile=str(root / "ca.crt"))
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=context)
        )
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline:
            assert server.poll() is None, "HTTPS server stopped"
            try:
                with opener.open(origin + "/health/live", timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError as error:
                reason = getattr(error, "reason", error)
                (root / "readiness-error.json").write_text(
                    json.dumps(
                        {
                            "type": type(reason).__name__,
                            "verify_code": getattr(reason, "verify_code", None),
                        }
                    )
                )
                time.sleep(0.1)
        else:
            raise AssertionError("HTTPS server not ready")
        # The real ASGI lifespan, not just a helper lock, rejects a second OS process.
        with socket.socket() as second_socket:
            second_socket.bind(("127.0.0.1", 0))
            second_port = second_socket.getsockname()[1]
        second = subprocess.run(
            [
                str(Path.cwd() / ".venv/bin/python"),
                "-m",
                "y3management.cli",
                "serve",
                "--cert",
                str(root / "server.crt"),
                "--key",
                str(root / "server.key"),
                "--port",
                str(second_port),
            ],
            env=env,
            capture_output=True,
            timeout=20,
        )
        (root / "second-startup.log").write_bytes(second.stdout + second.stderr)
        assert second.returncode != 0
        with opener.open(origin + "/health/live", timeout=2) as response:
            assert response.status == 200
        (root / "startup-results.json").write_text(
            json.dumps(
                {
                    "second_os_process_denied": True,
                    "original_still_healthy": True,
                    "same_database_and_schema_different_port": True,
                }
            )
        )
        browser = Path("/home/shlee/.cache/ms-playwright/chromium-1234/chrome-linux64")
        playwright = Path(
            "/home/shlee/Workspace/ai/01.codex/sj_company/node_modules/playwright-core"
        )
        node = Path("/home/shlee/.local/share/node/node-v22.23.2-linux-x64/bin/node")
        for name in ["browser-binaries", "playwright-core", "browser-tmp"]:
            (root / name).mkdir()
        (root / "node-host").touch()
        args = [
            "bwrap",
            "--unshare-user",
            "--unshare-pid",
            "--unshare-ipc",
            "--ro-bind",
            "/",
            "/",
            "--bind",
            str(root / "shadow-home"),
            "/home/shlee",
            "--bind",
            str(root),
            str(root),
            "--bind",
            str(root / "browser-tmp"),
            "/tmp",
            "--ro-bind",
            str(browser),
            str(root / "browser-binaries"),
            "--ro-bind",
            str(playwright),
            str(root / "playwright-core"),
            "--ro-bind",
            str(node),
            str(root / "node-host"),
            "--proc",
            "/proc",
            "--dev",
            "/dev",
            "--setenv",
            "TMPDIR",
            "/tmp",
            "--setenv",
            "NODE_EXTRA_CA_CERTS",
            str(root / "ca.crt"),
            "--setenv",
            "Y3_BROWSER_RUN",
            str(root),
            "--chdir",
            str(root),
            "--die-with-parent",
            str(root / "node-host"),
            str(root / "browser.cjs"),
        ]
        if emergency_db is not None:
            from tests.test_iam_emergency import cli_execute, operator, request

            browser_process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            qa_register_process(browser_process)
            try:
                local = settings.model_copy(update={"canonical_origin": origin})
                private = root / "operator"
                service, principal, ident = operator(local, emergency_db, private)
                previous = None
                from typing import Literal

                factors: tuple[Literal["password", "passkey", "both"], ...] = (
                    "password",
                    "passkey",
                    "both",
                )
                for index, factor in enumerate(factors):
                    deadline = time.monotonic() + 60
                    while not (root / f"emergency-issue-ready-{index}").exists():
                        assert browser_process.poll() is None, "Emergency browser form flow failed"
                        assert time.monotonic() < deadline, "Emergency browser form flow timed out"
                        time.sleep(0.1)
                    qa_stop_process(server)
                    execution = request(service, principal, ident, factor, previous)
                    delivery = cli_execute(local, private, execution)
                    previous = execution.operation_id
                    server = subprocess.Popen(server.args, env=env, stdout=log, stderr=log)
                    qa_register_process(server, port=port)
                    deadline = time.monotonic() + 25
                    while True:
                        assert server.poll() is None, "Emergency HTTPS restart failed"
                        try:
                            with opener.open(origin + "/health/live", timeout=1) as response:
                                if response.status == 200:
                                    break
                        except OSError:
                            assert time.monotonic() < deadline, "Emergency HTTPS restart timed out"
                            time.sleep(0.1)
                    destination = root / f"emergency-delivery-{index}"
                    shutil.copyfile(delivery, destination)
                    destination.chmod(0o600)
                    (root / f"emergency-issued-ready-{index}").write_text("ready")
                stdout, stderr = browser_process.communicate(timeout=60)
                result = subprocess.CompletedProcess(
                    args, browser_process.returncode, stdout, stderr
                )
            finally:
                qa_stop_process(browser_process)
        else:
            result = subprocess.run(args, capture_output=True, timeout=90)
        (root / "browser.log").write_bytes(result.stdout + result.stderr)
        stage_match = re.search(rb"MFA_BROWSER_FAILED stage=([a-z-]+)", result.stderr)
        safe_stage = stage_match.group(1).decode() if stage_match else "unspecified"
        if emergency_db is not None and result.returncode != 0:
            diagnostic = re.search(rb"EMERGENCY_DIAGNOSTIC=(.*)", result.stderr)
            if diagnostic:
                _qa_write(
                    qa_root() / "latest-emergency-failure.json",
                    {"stage": safe_stage, "diagnostic": json.loads(diagnostic.group(1))},
                )
        assert result.returncode == 0, "Actual HTTPS browser failed at " + safe_stage
        report = json.loads((root / "browser-results.json").read_text())
        # Keep only the current safe verdict; raw logs/profiles/credentials are disposable.
        checks = report.get("checks", {})
        version = str(report.get("browser", ""))
        required = json.loads((root / "required-checks.json").read_text()) if token else REQUIRED
        safe: dict[str, object] = {
            "checks": {
                name: isinstance(checks, dict) and checks.get(name) is True for name in required
            },
            "browser": version if re.fullmatch(r"\d+(\.\d+){1,3}", version) else "unknown",
            "scope": "actual trusted HTTPS browser",
            "run_id": root.parents[2].name,
        }
        evidence = (
            "latest-emergency-browser.json"
            if emergency_db
            else ("latest-mfa-browser.json" if token else "latest-browser.json")
        )
        _qa_write(qa_root() / evidence, safe)
        if token and emergency_db is None:
            management = report.get("management", {})
            expected = json.loads((root / "management-checks.json").read_text())
            _qa_write(
                qa_root() / "latest-management-browser.json",
                {
                    "checks": {name: management.get(name) is True for name in expected},
                    "browser": safe["browser"],
                    "run_id": safe["run_id"],
                    "scope": "actual trusted HTTPS management browser",
                },
            )
            reset = report.get("reset", {})
            reset_expected = json.loads((root / "reset-checks.json").read_text())
            _qa_write(
                qa_root() / "latest-reset-browser.json",
                {
                    "checks": {name: reset.get(name) is True for name in reset_expected},
                    "browser": safe["browser"],
                    "run_id": safe["run_id"],
                    "scope": "actual trusted HTTPS password reset browser",
                },
            )
            master_management = report.get("masterManagement", {})
            master_expected = json.loads((root / "master-management-checks.json").read_text())
            _qa_write(
                qa_root() / "latest-master-management-browser.json",
                {
                    "checks": {
                        name: master_management.get(name) is True for name in master_expected
                    },
                    "browser": safe["browser"],
                    "run_id": safe["run_id"],
                    "scope": "actual trusted HTTPS other-Master management browser",
                },
            )
            assert set(master_management) == set(master_expected) and all(
                master_management[k] is True for k in master_expected
            )
            assert set(reset) == set(reset_expected) and all(
                reset[k] is True for k in reset_expected
            )
            assert set(management) == set(expected) and all(management[k] is True for k in expected)
            assert set(checks) == set(required) and all(checks[name] is True for name in required)
        elif emergency_db is not None:
            assert set(checks) == set(required) and all(checks[name] is True for name in required)
        else:
            validate_browser_report(report)
        assert trust() == before
        print("Browser evidence: " + str(root / "browser-results.json"))
    finally:
        qa_stop_process(server)
        log.close()
        (root / "input.json").unlink(missing_ok=True)
        with socket.socket() as sock:
            assert sock.connect_ex(("127.0.0.1", port)) != 0
        assert trust() == before
