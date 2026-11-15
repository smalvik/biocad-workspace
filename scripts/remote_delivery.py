"""Send JSON to the fixed SSH dispatcher. Keys/host trust come only from CI secrets."""

import argparse
import json
import os
import re
import subprocess
import tarfile
import tempfile
from pathlib import Path

from delivery_manifest import load


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=("stage", "production", "report", "status", "rollback", "publish-allure")
    )
    parser.add_argument("--manifest", type=Path, default=Path("artifacts/candidate.json"))
    parser.add_argument("--namespace", default="smalvik")
    parser.add_argument("--environment", choices=("staging", "production"), default="production")
    parser.add_argument("--output", type=Path, default=Path("artifacts/server"))
    args = parser.parse_args()
    host, user = os.environ["DEPLOY_HOST"], os.environ["DEPLOY_USER"]
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9.-]*", host) or not re.fullmatch(r"[a-z_][a-z0-9_-]*", user):
        parser.error("Invalid host/user")
    request = {"action": args.action}
    if args.action in {"stage", "production", "report", "publish-allure"}:
        manifest = load(args.manifest, args.namespace)
        request.update(
            {"source_sha": manifest["source_sha"]} if args.action == "report" else {"manifest": manifest}
        )
    if args.action == "rollback":
        request["environment"] = args.environment
    with tempfile.TemporaryDirectory(prefix="biocad-ssh-") as directory:
        key, known = Path(directory) / "identity", Path(directory) / "known_hosts"
        key.write_text(os.environ["DEPLOY_SSH_KEY"].replace("\r\n", "\n").rstrip() + "\n")
        key.chmod(0o600)
        known.write_text(os.environ["DEPLOY_KNOWN_HOSTS"].rstrip() + "\n")
        command = [
            "ssh",
            "-T",
            "-i",
            str(key),
            "-o",
            "IdentitiesOnly=yes",
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=yes",
            "-o",
            f"UserKnownHostsFile={known}",
            "-o",
            "ConnectTimeout=15",
            "-o",
            "ServerAliveInterval=20",
            "-o",
            "ServerAliveCountMax=6",
            f"{user}@{host}",
        ]
        if args.action == "report":
            args.output.mkdir(parents=True, exist_ok=True)
            archive = Path(directory) / "report.tar.gz"
            with archive.open("wb") as stream:
                subprocess.run(
                    command, input=json.dumps(request).encode(), stdout=stream, check=True, timeout=120
                )
            with tarfile.open(archive) as bundle:
                bundle.extractall(args.output, filter="data")
        else:
            result = subprocess.run(
                command, input=json.dumps(request).encode(), check=True, timeout=2400, capture_output=True
            )
            args.output.mkdir(parents=True, exist_ok=True)
            (args.output / (args.action + ".json")).write_bytes(result.stdout)
            print(f"Server {args.action}: passed")


if __name__ == "__main__":
    main()
