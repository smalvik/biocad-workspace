"""After production smoke, add version/latest aliases to the already tested digests."""

import argparse
import json
import subprocess
from pathlib import Path

from delivery_manifest import load, runtime_services


def inspect(reference: str) -> str | None:
    result = subprocess.run(
        ["docker", "buildx", "imagetools", "inspect", reference, "--format", "{{json .Manifest}}"],
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)["digest"] if result.returncode == 0 else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("artifacts/candidate.json"))
    parser.add_argument("--namespace", default="smalvik")
    args = parser.parse_args()
    manifest = load(args.manifest, args.namespace)
    for service in runtime_services(manifest):
        reference = manifest["images"][service]
        repository, digest = reference.split("@")
        tag = f"{repository}:v{manifest['version']}"
        existing = inspect(tag)
        if existing and existing != digest:
            raise SystemExit(f"Refusing to overwrite existing version {tag}")
    for suffix in ("v" + manifest["version"], "latest"):
        for service in runtime_services(manifest):
            reference = manifest["images"][service]
            repository, digest = reference.split("@")
            tag = repository + ":" + suffix
            subprocess.run(
                ["docker", "buildx", "imagetools", "create", "--prefer-index=false", "--tag", tag, reference],
                check=True,
            )
            if inspect(tag) != digest:
                raise SystemExit(f"Promoted digest mismatch: {tag}")
    print(f"Promoted exact checked digests to v{manifest['version']} and latest")


if __name__ == "__main__":
    main()
