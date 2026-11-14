"""Build each source SHA once, push candidates, and record registry digests (no deployment)."""

import argparse
import json
import re
import subprocess
from pathlib import Path

from delivery_manifest import NAMESPACE, SERVICES, validate

ROOT = Path(__file__).resolve().parent.parent
BUILDS = {
    "booking": (".", "services/booking/Dockerfile", "runtime"),
    "assistant": ("services/assistant", "services/assistant/Dockerfile", "runtime"),
    "web": ("apps/web", "apps/web/Dockerfile", "runtime"),
    "booking-tests": (".", "services/booking/Dockerfile", "test"),
    "assistant-tests": ("services/assistant", "services/assistant/Dockerfile", "test"),
    "web-tests": ("apps/web", "apps/web/Dockerfile", "test"),
    "e2e": ("tests/e2e", "tests/e2e/Dockerfile", None),
}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def release_version() -> str:
    tags = [t for t in git("tag").splitlines() if re.fullmatch(r"v1\.\d+\.\d+", t)]
    if not tags:
        return "1.0.0"
    last = max(tags, key=lambda t: tuple(map(int, t[1:].split("."))))
    base = git("merge-base", last, "HEAD")
    subjects = git("log", "--no-merges", "--format=%s", f"{base}..HEAD").splitlines()
    if not subjects:
        return last[1:]
    _, minor, patch = map(int, last[1:].split("."))
    if any(re.match(r"feat(?:\([^)]*\))?!?:", s) for s in subjects):
        return f"1.{minor + 1}.0"
    return f"1.{minor}.{patch + 1}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--namespace", required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/candidate.json")
    args = parser.parse_args()
    if not NAMESPACE.fullmatch(args.namespace):
        parser.error("Invalid Docker Hub namespace")
    if git("status", "--porcelain", "--untracked-files=no"):
        parser.error("Only a committed source tree may be packaged")
    sha, version = git("rev-parse", "HEAD"), release_version()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    manifest = {"schema": 1, "source_sha": sha, "version": version, "images": {}}
    for service in SERVICES:
        repository = f"{args.namespace}/biocad-{service}"
        tag = f"{repository}:sha-{sha}"
        existing = subprocess.run(
            ["docker", "buildx", "imagetools", "inspect", tag, "--format", "{{json .Manifest}}"],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        if existing.returncode == 0:
            digest = json.loads(existing.stdout)["digest"]
            print(f"Reusing immutable candidate {tag}", flush=True)
        else:
            context, dockerfile, target = BUILDS[service]
            metadata = args.output.parent / f"build-{service}.json"
            command = [
                "docker",
                "buildx",
                "build",
                "--platform",
                "linux/amd64",
                "--provenance=true",
                "--push",
                "--file",
                dockerfile,
                "--tag",
                tag,
                "--metadata-file",
                str(metadata),
                "--build-arg",
                f"GIT_SHA={sha}",
                "--build-arg",
                f"RELEASE_VERSION={version}",
                "--label",
                f"org.opencontainers.image.revision={sha}",
                "--label",
                f"org.opencontainers.image.version={version}",
                "--label",
                "org.opencontainers.image.source=https://github.com/smalvik/biocad-workspace",
            ]
            if target:
                command.extend(["--target", target])
            subprocess.run([*command, context], cwd=ROOT, check=True)
            digest = json.loads(metadata.read_text())["containerimage.digest"]
        manifest["images"][service] = f"{repository}@{digest}"
    validate(manifest, args.namespace)
    args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Candidate {sha}: planned release {version}; no version/latest tags published")


if __name__ == "__main__":
    main()
