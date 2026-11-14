"""Root-owned SSH forced command. Only allowlisted JSON operations; no remote shell."""

import fcntl
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
from datetime import datetime, timezone
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlsplit
from uuid import uuid4

from delivery_manifest import RUNTIME, SHA, image_environment, load, validate, verify_local_images

ROOT = Path("/opt/biocad")
TOOLS = ROOT / "tooling"
UTC = timezone.utc  # noqa: UP017 -- Ubuntu 22.04 server Python 3.10 compatibility


def atomic_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(".pending")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.chmod(0o600)
    temporary.replace(path)


def compose(environment: str, manifest: dict, settings: dict) -> tuple[list[str], dict]:
    if environment not in {"staging", "production"}:
        raise ValueError("Unexpected environment")
    directory = ROOT / environment
    if (directory / ".biocad-owned").read_text().strip() != "biocad-workspace":
        raise ValueError("Missing deployment ownership marker")
    secrets = json.loads((directory / "secrets.json").read_text())
    env = os.environ.copy()
    env.update(secrets)
    env.update(image_environment(manifest))
    env.update(APP_ENV=environment, WEB_HOST_PORT=str(settings[environment + "_port"]))
    command = [
        "docker",
        "compose",
        "--ansi",
        "never",
        "--env-file",
        "/dev/null",
        "-p",
        "biocad-" + environment,
        "-f",
        str(TOOLS / "infra/compose.release.yaml"),
        "-f",
        str(TOOLS / "infra/compose.host.yaml"),
    ]
    if environment == "production" and settings.get("ingress_network"):
        env.update(
            INGRESS_NETWORK=settings["ingress_network"],
            PUBLIC_HOST=urlsplit(settings["production_url"]).hostname,
        )
        command.extend(["-f", str(TOOLS / "infra/compose.traefik.yaml")])
    return command, env


def run(command: list[str], env: dict, **kwargs) -> subprocess.CompletedProcess:
    # Do not log expanded Compose configuration, environment or container inspection.
    return subprocess.run(command, env=env, check=True, timeout=600, **kwargs)


def backup(environment: str, manifest: dict, settings: dict) -> str | None:
    command, env = compose(environment, manifest, settings)
    existing = run([*command, "ps", "-aq", "postgres"], env, capture_output=True, text=True).stdout.strip()
    if not existing:
        return None
    run([*command, "up", "-d", "--no-build", "--wait", "postgres"], env, stdout=sys.stderr)
    directory = ROOT / environment / "backups"
    directory.mkdir(mode=0o700, exist_ok=True)
    path = directory / (datetime.now(UTC).strftime("%Y%m%dT%H%M%S") + "-" + uuid4().hex[:6] + ".dump")
    with path.open("xb") as output:
        path.chmod(0o600)
        run(
            [*command, "exec", "-T", "postgres", "pg_dump", "-U", "biocad", "-d", "biocad", "-Fc"],
            env,
            stdout=output,
        )
        output.flush()
        os.fsync(output.fileno())
    with path.open("rb") as source:
        run(
            [*command, "exec", "-T", "postgres", "pg_restore", "--list"],
            env,
            stdin=source,
            stdout=subprocess.DEVNULL,
        )
    return path.name


def smoke(url: str, manifest: dict, environment: str, report: Path) -> None:
    """Readiness and demo auth; production additionally verifies real HTTPS session use."""
    result = {
        "uuid": str(uuid4()),
        "name": f"{environment}: HTTPS/session/readiness deployment smoke",
        "fullName": "delivery.smoke." + environment,
        "start": int(time.time() * 1000),
        "labels": [
            {"name": name, "value": value}
            for name, value in {
                "suite": "deployment",
                "run_type": "smoke",
                "environment": environment,
                "git_sha": manifest["source_sha"],
                "release_version": manifest["version"],
            }.items()
        ],
    }
    try:
        jar = CookieJar()
        client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

        def request(path: str, data=None, headers=None):
            body = json.dumps(data).encode() if data is not None else None
            req = urllib.request.Request(
                url.rstrip("/") + path,
                data=body,
                headers={"Content-Type": "application/json", **(headers or {})},
            )
            for attempt in range(24):
                try:
                    with client.open(req, timeout=30) as response:
                        return response.read(), response.headers
                except (URLError, TimeoutError):
                    # Allow the existing proxy to discover a new route and issue its first TLS certificate.
                    # Only the first read-only page request retries. Wrong SHA/cookies fail immediately.
                    if path != "/" or attempt == 23:
                        raise
                    time.sleep(5)

        page, _ = request("/")
        assert b'<div id="root">' in page, "React document missing"
        web, _ = request("/version.json")
        assert json.loads(web)["git_sha"] == manifest["source_sha"], "Wrong Web SHA"
        health, _ = request("/api/v1/healthz")
        assert json.loads(health)["version"] == manifest["source_sha"], "Wrong Booking SHA"
        ready, _ = request("/api/v1/readyz")
        assert json.loads(ready)["checks"]["postgres"] is True
        assistant, _ = request("/api/v1/assistant/healthz")
        assert json.loads(assistant)["version"] == manifest["source_sha"], "Wrong Assistant SHA"
        body, headers = request("/api/v1/auth/login", {"username": "e01", "password": "demo-workspace"})
        cookie = headers.get("Set-Cookie", "").lower()
        assert "secure" in cookie and "httponly" in cookie and "samesite=lax" in cookie
        if url.startswith("https://"):
            profile, _ = request("/api/v1/auth/me")
            assert json.loads(profile)["employee"]["id"] == "e01"
            floors, _ = request("/api/v1/floors")
            assert len(json.loads(floors)["items"]) == 2
            request("/api/v1/auth/logout", {}, {"X-CSRF-Token": json.loads(body)["csrf_token"]})
        result["status"] = "passed"
    except Exception:
        result["status"] = "failed"
        result["statusDetails"] = {"message": "Deployment smoke failed; no authentication data retained"}
        raise
    finally:
        result["stop"] = int(time.time() * 1000)
        output = report / "smoke/allure-results"
        output.mkdir(parents=True, exist_ok=True)
        atomic_json(output / (result["uuid"] + "-result.json"), result)


def deploy(environment: str, manifest: dict, settings: dict, report: Path) -> dict:
    directory = ROOT / environment
    current = directory / "current.json"
    previous = load(current, settings["namespace"]) if current.exists() else None
    command, env = compose(environment, manifest, settings)
    backup_name = backup(environment, previous or manifest, settings)
    # Pull failure does not change running services.
    run([*command, "pull"], env, stdout=sys.stderr)
    verify_local_images(manifest, RUNTIME)
    url = (
        settings["production_url"]
        if environment == "production"
        else f"http://127.0.0.1:{settings['staging_port']}"
    )
    try:
        run([*command, "up", "-d", "--no-build", "--wait", "--wait-timeout", "180"], env, stdout=sys.stderr)
        smoke(url, manifest, environment, report)
    except Exception:
        if previous:
            old_command, old_env = compose(environment, previous, settings)
            run(
                [*old_command, "up", "-d", "--no-build", "--wait", "--wait-timeout", "180"],
                old_env,
                stdout=sys.stderr,
            )
            smoke(url, previous, environment, report / "rollback")
        else:
            # A failed first install has no previous image set. Preserve its database, stop its app.
            run([*command, "stop", "web", "booking", "assistant"], env, stdout=sys.stderr)
        # Never restore DB automatically: that would discard bookings made after backup.
        raise
    if previous and previous != manifest:
        atomic_json(directory / "previous.json", previous)
    atomic_json(current, manifest)
    return {"environment": environment, "status": "passed", "backup": backup_name, "manifest": manifest}


def stage(manifest: dict, settings: dict, report: Path) -> dict:
    # Preserve other apps: refuse a heavy test run when host resources are low.
    if shutil.disk_usage(ROOT).free < 6 * 1024**3:
        raise RuntimeError("At least 6 GiB of free disk is required before pulling regression images")
    memory = next(
        line for line in Path("/proc/meminfo").read_text().splitlines() if line.startswith("MemAvailable:")
    )
    if int(memory.split()[1]) < 4 * 1024**2:
        raise RuntimeError("At least 4 GiB of available RAM is required for bounded isolated regression")
    candidate = report / "candidate.json"
    atomic_json(candidate, manifest)
    before = set((TOOLS / "artifacts").glob("*/run.json")) if (TOOLS / "artifacts").exists() else set()
    with (report / "regression.log").open("w") as log:
        process = subprocess.run(
            [
                sys.executable,
                str(TOOLS / "scripts/check.py"),
                "--run-type",
                "regression",
                "--environment",
                "staging",
                "--namespace",
                settings["namespace"],
                "--manifest",
                str(candidate),
            ],
            cwd=TOOLS,
            stdout=log,
            stderr=subprocess.STDOUT,
            timeout=1800,
        )
    created = set((TOOLS / "artifacts").glob("*/run.json")) - before
    for result in created:
        shutil.copytree(result.parent, report / result.parent.name)
    if process.returncode:
        raise RuntimeError(
            "Isolated staging regression failed; report is available through the report action"
        )
    result = deploy("staging", manifest, settings, report)
    atomic_json(report / "staging.json", result)
    return result


def dispatch(request: dict, settings: dict) -> dict | None:
    action = request.get("action")
    if action in {"stage", "production"}:
        if set(request) != {"action", "manifest"}:
            raise ValueError("Unexpected deploy request fields")
        manifest = validate(request["manifest"], settings["namespace"])
        report = ROOT / "reports" / manifest["source_sha"]
        report.mkdir(mode=0o700, parents=True, exist_ok=True)
        if action == "stage":
            return stage(manifest, settings, report)
        attestation = json.loads((report / "staging.json").read_text())
        current_stage = load(ROOT / "staging/current.json", settings["namespace"])
        if (
            attestation["status"] != "passed"
            or attestation["manifest"] != manifest
            or current_stage != manifest
        ):
            raise ValueError("Exact manifest must pass staging before production")
        result = deploy("production", manifest, settings, report / "production")
        atomic_json(report / "production.json", result)
        return result
    if action == "rollback" and set(request) == {"action", "environment"}:
        environment = request["environment"]
        if environment not in {"staging", "production"}:
            raise ValueError("Unexpected environment")
        manifest = load(ROOT / environment / "previous.json", settings["namespace"])
        return deploy(
            environment, manifest, settings, ROOT / "reports" / manifest["source_sha"] / "manual-rollback"
        )
    if action == "report" and set(request) == {"action", "source_sha"}:
        if not isinstance(request["source_sha"], str) or not SHA.fullmatch(request["source_sha"]):
            raise ValueError("Invalid report SHA")
        path = ROOT / "reports" / request["source_sha"]
        if not path.is_dir():
            raise ValueError("No report for this SHA")
        # No secrets.json, backups, arbitrary paths or symlink targets enter reports.
        with tarfile.open(fileobj=sys.stdout.buffer, mode="w|gz", dereference=False) as archive:
            archive.add(path, arcname=request["source_sha"])
        return None
    if action == "status" and set(request) == {"action"}:
        return {
            e: json.loads((ROOT / e / "current.json").read_text())
            if (ROOT / e / "current.json").exists()
            else None
            for e in ("staging", "production")
        }
    raise ValueError("Unsupported operation or unexpected fields")


def main() -> int:
    if os.geteuid() != 0 or os.environ.get("SSH_ORIGINAL_COMMAND"):
        raise SystemExit("Only the root-owned, no-argument forced command is supported")
    os.umask(0o077)
    raw = sys.stdin.buffer.read(65537)
    if len(raw) > 65536:
        raise SystemExit("Request too large")
    settings = json.loads((ROOT / "settings.json").read_text())
    with (ROOT / "deploy.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            result = dispatch(json.loads(raw), settings)
            if result is not None:
                print(json.dumps(result))
            return 0
        except Exception as exc:
            # Never print auth responses, secret environment, arbitrary exception values.
            print(
                f"Delivery operation failed ({type(exc).__name__}); inspect the project report on the server",
                file=sys.stderr,
            )
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
