"""Run the available checks in isolated Docker infrastructure without loading the local .env."""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from delivery_manifest import image_environment, load, verify_local_images

ROOT = Path(__file__).resolve().parent.parent
UTC = timezone.utc  # noqa: UP017 -- Ubuntu 22.04 server Python 3.10 compatibility


def git_output(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main() -> int:
    # Windows consoles may default to cp1251; Vite/pytest output includes Unicode.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-type", choices=("smoke", "regression"), default="smoke")
    parser.add_argument("--manifest", type=Path, help="Use only prebuilt digest images; never build")
    parser.add_argument("--namespace", default="smalvik")
    parser.add_argument("--environment", choices=("local", "staging"), default="local")
    args = parser.parse_args()
    manifest = load(args.manifest, args.namespace) if args.manifest else None
    notifications = manifest is None or "notification" in manifest["images"]
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:6]
    project = "biocad-check-" + run_id.lower()
    output = ROOT / "artifacts" / run_id
    output.mkdir(parents=True)
    (output / "allure-results").mkdir()
    sha = manifest["source_sha"] if manifest else git_output("rev-parse", "HEAD")
    dirty = "clean" if manifest else ("dirty" if git_output("status", "--porcelain") else "clean")
    version = manifest["version"] if manifest else "unreleased"
    env = os.environ.copy()
    env.update(
        {
            "APP_ENV": "local",
            "GIT_SHA": sha,
            "WORKING_TREE": dirty,
            "RUN_TYPE": args.run_type,
            "RELEASE_VERSION": version,
            "REPORT_ENV": args.environment,
            "ARTIFACTS_DIR": output.as_posix(),
            "IMAGE_TAG": project,
            "POSTGRES_USER": "biocad",
            "POSTGRES_PASSWORD": "biocad-test-only",
            "POSTGRES_DB": "biocad",
            "SESSION_SECRET": "isolated-test-only",
            "RABBITMQ_USER": "biocad",
            "RABBITMQ_PASSWORD": "biocad-test-only",
            "OPENROUTER_API_KEY": "fixture-not-secret",
            "OPENROUTER_PRIMARY_MODEL": "test/scripted",
            "OPENROUTER_FALLBACK_MODEL": "test/fallback",
            "OPENROUTER_BASE_URL": "http://llm-fixture:8090/v1",
            "ENABLE_LLM_TEST_FIXTURE": "true",
            "ASSISTANT_PROPOSAL_SECRET": "isolated-proposal-only-secret-32-characters",
            "ASSISTANT_BUDGET_USD": "100",
            "ASSISTANT_BUDGET_EPOCH": "isolated-test",
            "ASSISTANT_REQUESTS_PER_MINUTE": "1000",
            "ALLOW_DATABASE_TESTS": "1",
            "DEMO_PASSWORD": "demo-workspace",
            "SEED_DEMO_DATA": "true",
            "NOTIFICATIONS_ENABLED": "true" if notifications else "false",
            "NOTIFICATION_PUBLIC_URL": "http://web",
        }
    )
    if manifest:
        env.update(image_environment(manifest))
    compose = [
        "docker",
        "compose",
        "--ansi",
        "never",
        "--env-file",
        ".env.example",
        "-p",
        project,
        "-f",
        "infra/compose.images.yaml" if manifest else "infra/compose.yaml",
        "--profile",
        "test",
    ]
    if not manifest:
        compose.extend(["-f", "infra/compose.test.yaml"])
    if notifications:
        compose.extend(["--profile", "notifications"])
    metadata = {
        "run_id": run_id,
        "project": project,
        "base_git_sha": sha,
        "working_tree": dirty,
        "run_type": args.run_type,
        "environment": args.environment,
        "release_version": version,
        "image_digests": manifest["images"] if manifest else {},
        "llm_mode": "scripted HTTP fixture; real MCP, RabbitMQ and PostgreSQL; no paid calls",
        "commands": [],
    }

    with (output / "commands.log").open("w", encoding="utf-8") as log:

        def run(*command: str, check: bool = True) -> int:
            print("+ " + " ".join(command), flush=True)
            log.write("+ " + " ".join(command) + "\n")
            process = subprocess.Popen(
                command,
                cwd=ROOT,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            assert process.stdout is not None
            for line in process.stdout:
                print(line, end="", flush=True)
                log.write(line)
            code = process.wait()
            log.flush()
            metadata["commands"].append({"argv": list(command), "exit_code": code})
            if check and code:
                raise subprocess.CalledProcessError(code, command)
            return code

        success = False
        owned = False
        try:
            # Refuse to reuse an existing project, even in the unlikely event of a name collision.
            existing = subprocess.check_output([*compose, "ps", "-aq"], cwd=ROOT, env=env, text=True)
            if existing.strip():
                raise RuntimeError("Refusing to reuse an existing Compose project")
            owned = True
            run(*compose, "config", "--quiet")
            if manifest:
                run(*compose, "pull")
                verify_local_images(manifest)
            else:
                run(
                    *compose,
                    "build",
                    "booking",
                    "assistant",
                    "web",
                    "booking-tests",
                    "assistant-tests",
                    "web-tests",
                    "e2e",
                    *(["notification", "notification-tests"] if notifications else []),
                )
            run(
                *compose,
                "up",
                "-d",
                "--no-build",
                "--wait",
                "--wait-timeout",
                "180",
                "postgres",
                "rabbitmq",
                "llm-fixture",
                "mailpit",
                "booking",
                "assistant",
                "web",
                *(["notification"] if notifications else []),
            )
            for service in (
                "booking-tests",
                "assistant-tests",
                *(["notification-tests"] if notifications else []),
            ):
                run(*compose, "run", "--rm", "--no-deps", service, "ruff", "check", ".")
                run(*compose, "run", "--rm", "--no-deps", service, "ruff", "format", "--check", ".")
                run(*compose, "run", "--rm", "--no-deps", service)
            run(*compose, "exec", "-T", "booking", "python", "-m", "app.seed")
            for phase in ("prepare", "verify"):
                if phase == "verify":
                    run(*compose, "stop", "booking")
                    run(*compose, "restart", "postgres")
                    run(*compose, "up", "-d", "--no-build", "--wait", "postgres")
                    run(*compose, "up", "-d", "--no-build", "--wait", "booking")
                run(
                    *compose,
                    "run",
                    "--rm",
                    "--no-deps",
                    "-e",
                    f"PERSISTENCE_PHASE={phase}",
                    "booking-tests",
                    "pytest",
                    "-q",
                    "tests/integration/persistence_check.py",
                    "--alluredir=/allure-results",
                )
            if notifications:
                # Real faults affect only this disposable project's broker/SMTP services.
                recovery = [
                    "booking-tests",
                    "pytest",
                    "-q",
                    "tests/integration/notifications_recovery.py",
                    "--alluredir=/allure-results",
                ]

                def notification_phase(phase):
                    run(*compose, "run", "--rm", "--no-deps", "-e", f"NOTIFICATION_PHASE={phase}", *recovery)

                run(*compose, "stop", "rabbitmq", "notification")
                notification_phase("broker_down")
                run(*compose, "up", "-d", "--no-build", "--wait", "rabbitmq", "notification")
                notification_phase("broker_recovered")
                run(*compose, "restart", "notification")
                run(*compose, "up", "-d", "--no-build", "--wait", "notification")
                notification_phase("duplicate_after_restart")
                run(*compose, "stop", "mailpit")
                notification_phase("smtp_down")
                run(*compose, "restart", "notification")
                run(*compose, "up", "-d", "--no-build", "--wait", "notification", "mailpit")
                notification_phase("smtp_recovered")
            run(*compose, "run", "--rm", "--no-deps", "web-tests")
            run(*compose, "run", "--rm", "--no-deps", "e2e", "npx", "tsc", "--noEmit")
            run(*compose, "run", "--rm", "--no-deps", "e2e")
            success = True
        except (subprocess.CalledProcessError, RuntimeError, OSError) as exc:
            print(f"Check failed: {exc}", file=sys.stderr)
            if owned:
                run(*compose, "logs", "--no-color", "--tail", "100", check=False)
        finally:
            # Only this invocation's generated project is removed; no host paths are deleted.
            # On collision, the existing project must also be left untouched.
            if owned:
                cleanup_code = run(*compose, "down", "--volumes", "--remove-orphans", check=False)
                success = success and cleanup_code == 0
            metadata["result"] = "passed" if success else "failed"
            (output / "run.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            (output / "allure-results" / "environment.properties").write_text(
                f"environment={args.environment}\nrun_type={args.run_type}\ngit_sha={sha}\n"
                f"working_tree={dirty}\nrelease_version={version}\n",
                encoding="utf-8",
            )
    print(f"Evidence: {output.relative_to(ROOT)} ({metadata['result']})")
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
