"""Administrator-only bootstrap of the isolated BIOCAD delivery area (does not edit Nginx)."""

import argparse
import json
import os
import pwd
import re
import secrets
import shutil
import socket
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

from delivery_manifest import NAMESPACE

ROOT = Path("/opt/biocad")
SOURCE = Path(__file__).resolve().parent.parent
USER = "biocad-deploy"
HOME = Path("/var/lib/biocad-deploy")
FILES = (
    ".env.example",
    "scripts/check.py",
    "scripts/delivery_manifest.py",
    "scripts/deploy_server.py",
    "infra/compose.release.yaml",
    "infra/compose.host.yaml",
    "infra/compose.images.yaml",
    "infra/compose.traefik.yaml",
)


def write(path: Path, value: str, mode: int) -> None:
    path.write_text(value, encoding="utf-8")
    path.chmod(mode)
    os.chown(path, 0, 0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-key", type=Path, required=True)
    parser.add_argument("--namespace", default="smalvik")
    parser.add_argument("--production-url", default="https://biocad.smalvik.dev")
    parser.add_argument("--staging-port", type=int, default=18081)
    parser.add_argument("--production-port", type=int, default=18080)
    parser.add_argument("--ingress-network", help="Existing Traefik network, only production Web joins")
    args = parser.parse_args()
    if os.geteuid() != 0:
        parser.error("Run as the administrator after reviewing the shared-host inventory")
    if not NAMESPACE.fullmatch(args.namespace):
        parser.error("Invalid namespace")
    url = urlsplit(args.production_url)
    if url.scheme != "https" or not url.hostname or url.username or url.password or url.path not in ("", "/"):
        parser.error("A bare HTTPS production origin is required")
    public_key = args.public_key.read_text().strip()
    if not re.fullmatch(r"ssh-ed25519 [A-Za-z0-9+/]+={0,3}(?: [A-Za-z0-9@._-]+)?", public_key):
        parser.error("Expected one dedicated ed25519 public key")
    settings = {
        "namespace": args.namespace,
        "production_url": args.production_url.rstrip("/"),
        "staging_port": args.staging_port,
        "production_port": args.production_port,
    }
    if args.ingress_network:
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_.-]+", args.ingress_network):
            parser.error("Invalid ingress network name")
        subprocess.run(
            ["docker", "network", "inspect", args.ingress_network], check=True, stdout=subprocess.DEVNULL
        )
        settings["ingress_network"] = args.ingress_network
    installed = (ROOT / "settings.json").exists()
    if ROOT.is_symlink() or (ROOT.exists() and any(ROOT.iterdir()) and not installed):
        parser.error("Refusing to take over an existing /opt/biocad directory")
    if installed and json.loads((ROOT / "settings.json").read_text()) != settings:
        parser.error("Existing installation settings differ; review them explicitly")
    if args.staging_port == args.production_port or not all(
        1024 < p < 65536 for p in (args.staging_port, args.production_port)
    ):
        parser.error("Choose two distinct unprivileged unused ports")
    for environment in ("staging", "production"):
        existing = subprocess.check_output(
            [
                "docker",
                "ps",
                "-aq",
                "--filter",
                "label=com.docker.compose.project=biocad-" + environment,
            ],
            text=True,
        ).strip()
        if existing and not installed:
            parser.error("A BIOCAD-named Compose project already exists; refusing to adopt it")
        if not installed:
            prefix = "biocad-" + environment + "_"
            for resource in ("volume", "network"):
                names = subprocess.check_output(
                    ["docker", resource, "ls", "--format", "{{.Name}}"], text=True
                )
                if any(name.startswith(prefix) for name in names.splitlines()):
                    parser.error("Preexisting BIOCAD-named storage/network found; refusing to adopt it")
        if not existing:
            with socket.socket() as probe:
                probe.bind(("127.0.0.1", settings[environment + "_port"]))
    subprocess.run(["docker", "compose", "version"], check=True)
    subprocess.run(["visudo", "-V"], check=True, stdout=subprocess.DEVNULL)
    try:
        account = pwd.getpwnam(USER)
        if account.pw_dir != str(HOME) or not installed:
            parser.error("Refusing to modify a preexisting account")
    except KeyError:
        subprocess.run(
            ["useradd", "--system", "--create-home", "--home-dir", str(HOME), "--shell", "/bin/sh", USER],
            check=True,
        )
    os.umask(0o077)
    ROOT.mkdir(mode=0o700, exist_ok=True)
    for name in FILES:
        destination = ROOT / "tooling" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SOURCE / name, destination)
        destination.chmod(0o600)
        os.chown(destination, 0, 0)
    for environment in ("staging", "production"):
        directory = ROOT / environment
        directory.mkdir(mode=0o700, exist_ok=True)
        write(directory / ".biocad-owned", "biocad-workspace\n", 0o600)
        if not (directory / "secrets.json").exists():
            values = {
                "POSTGRES_PASSWORD": secrets.token_urlsafe(36),
                "SESSION_SECRET": secrets.token_urlsafe(48),
                "RABBITMQ_PASSWORD": secrets.token_urlsafe(36),
                "DEMO_PASSWORD": "demo-workspace",
            }
            write(directory / "secrets.json", json.dumps(values, indent=2) + "\n", 0o600)
        values = json.loads((directory / "secrets.json").read_text())
        if "ASSISTANT_PROPOSAL_SECRET" not in values:
            values["ASSISTANT_PROPOSAL_SECRET"] = secrets.token_urlsafe(48)
            write(directory / "secrets.json", json.dumps(values, indent=2) + "\n", 0o600)
    write(ROOT / "settings.json", json.dumps(settings, indent=2) + "\n", 0o600)
    write(
        Path("/usr/local/sbin/biocad-deploy"),
        '#!/bin/sh\nset -eu\n[ "$#" -eq 0 ] || exit 126\n'
        "exec /usr/bin/python3 /opt/biocad/tooling/scripts/deploy_server.py\n",
        0o755,
    )
    write(
        Path("/usr/local/bin/biocad-ssh-entry"),
        '#!/bin/sh\nset -eu\n[ -z "${SSH_ORIGINAL_COMMAND:-}" ] || exit 126\n'
        "exec sudo -n /usr/local/sbin/biocad-deploy\n",
        0o755,
    )
    sudoers = ROOT / "sudoers.pending"
    write(sudoers, 'biocad-deploy ALL=(root) NOPASSWD: /usr/local/sbin/biocad-deploy ""\n', 0o440)
    subprocess.run(["visudo", "-cf", str(sudoers)], check=True)
    shutil.copyfile(sudoers, "/etc/sudoers.d/biocad-deploy")
    Path("/etc/sudoers.d/biocad-deploy").chmod(0o440)
    # Root owns the home and public authorization, so the account cannot replace its forced command.
    HOME.chmod(0o755)
    os.chown(HOME, 0, 0)
    ssh = HOME / ".ssh"
    ssh.mkdir(mode=0o755, exist_ok=True)
    ssh.chmod(0o755)
    os.chown(ssh, 0, 0)
    write(
        ssh / "authorized_keys",
        'restrict,command="/usr/local/bin/biocad-ssh-entry" ' + public_key + "\n",
        0o644,
    )
    print(
        "BIOCAD dispatcher installed. No Nginx config, existing containers or Docker daemon settings changed."
    )


if __name__ == "__main__":
    main()
