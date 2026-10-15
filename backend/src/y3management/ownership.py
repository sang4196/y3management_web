"""Verify this repository's dedicated local Compose target before bootstrap."""

import json
import subprocess
from pathlib import Path

from sqlalchemy.engine import make_url

from y3management.config import Settings


def verify_local_target(settings: Settings) -> None:
    u = make_url(settings.database_url.get_secret_value())
    service = "postgres-test" if settings.environment == "test" else "postgres-dev"
    port = 55433 if settings.environment == "test" else 55432
    if (
        settings.environment not in {"test", "development"}
        or u.host not in {"127.0.0.1", "localhost", "::1"}
        or u.port != port
    ):
        raise ValueError("UNVERIFIED_BOOTSTRAP_TARGET")
    compose = Path(__file__).resolve().parents[2] / "compose.yaml"
    base = ["docker", "--context", "wsl-ubuntu"]

    def output(args: list[str]) -> str:
        return subprocess.check_output(
            args, text=True, stderr=subprocess.DEVNULL, timeout=10
        ).strip()

    endpoint = output(
        base + ["context", "inspect", "wsl-ubuntu", "--format", "{{.Endpoints.docker.Host}}"]
    )
    if endpoint != "unix:///run/docker-wsl.sock":
        raise ValueError("UNVERIFIED_BOOTSTRAP_TARGET")
    ident = output(base + ["compose", "-f", str(compose), "ps", "-q", service])
    if not ident or "\n" in ident:
        raise ValueError("UNVERIFIED_BOOTSTRAP_TARGET")
    labels = json.loads(output(base + ["inspect", "--format", "{{json .Config.Labels}}", ident]))
    ports = json.loads(
        output(base + ["inspect", "--format", "{{json .NetworkSettings.Ports}}", ident])
    )
    if (
        labels.get("com.docker.compose.project") != "y3management-foundation"
        or labels.get("com.docker.compose.service") != service
        or labels.get("com.docker.compose.project.working_dir") != str(compose.parent)
        or {"HostIp": "127.0.0.1", "HostPort": str(port)} not in ports["5432/tcp"]
    ):
        raise ValueError("UNVERIFIED_BOOTSTRAP_TARGET")
