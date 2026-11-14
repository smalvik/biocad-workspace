"""Run the available checks in isolated Docker infrastructure without loading the local .env."""

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent


def git_output(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main() -> int:
    # Windows consoles may default to cp1251; Vite/pytest output includes Unicode.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-type", choices=("smoke", "regression"), default="smoke")
    args = parser.parse_args()
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:6]
    project = "biocad-check-" + run_id.lower()
    output = ROOT / "artifacts" / run_id
    output.mkdir(parents=True)
    (output / "allure-results").mkdir()
    sha = git_output("rev-parse", "HEAD")
    dirty = "dirty" if git_output("status", "--porcelain") else "clean"
    env = os.environ.copy()
    env.update(
        {
            "APP_ENV": "local",
            "GIT_SHA": sha,
            "WORKING_TREE": dirty,
            "RUN_TYPE": args.run_type,
            "RELEASE_VERSION": "unreleased",
            "ARTIFACTS_DIR": output.as_posix(),
            "IMAGE_TAG": project,
            "POSTGRES_USER": "biocad",
            "POSTGRES_PASSWORD": "biocad-test-only",
            "POSTGRES_DB": "biocad",
            "SESSION_SECRET": "isolated-test-only",
            "RABBITMQ_USER": "biocad",
            "RABBITMQ_PASSWORD": "biocad-test-only",
            "OPENROUTER_API_KEY": "",
            "OPENROUTER_PRIMARY_MODEL": "",
            "OPENROUTER_FALLBACK_MODEL": "",
            "ALLOW_DATABASE_TESTS": "1",
            "DEMO_PASSWORD": "demo-workspace",
            "SEED_DEMO_DATA": "true",
        }
    )
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
        "infra/compose.yaml",
        "-f",
        "infra/compose.test.yaml",
        "--profile",
        "test",
    ]
    metadata = {
        "run_id": run_id,
        "project": project,
        "base_git_sha": sha,
        "working_tree": dirty,
        "run_type": args.run_type,
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
                "mailpit",
                "booking",
                "assistant",
                "web",
            )
            for service in ("booking-tests", "assistant-tests"):
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
                f"environment=local\nrun_type={args.run_type}\ngit_sha={sha}\n"
                f"working_tree={dirty}\nrelease_version=unreleased\n",
                encoding="utf-8",
            )
    print(f"Evidence: {output.relative_to(ROOT)} ({metadata['result']})")
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
