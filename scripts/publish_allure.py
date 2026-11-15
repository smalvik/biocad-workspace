"""Publish only checksum-verified HTML assets from this project's published releases."""

import argparse
import hashlib
import json
import os
import re
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

from delivery_manifest import load, validate

REPOSITORY = "smalvik/biocad-workspace"
API = "https://api.github.com/repos/" + REPOSITORY
DOWNLOAD = "https://github.com/" + REPOSITORY + "/releases/download/"
MAX_HTML = 24 * 1024 * 1024


def download(url: str, limit: int, digest: str | None = None) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "BIOCAD-Allure-Publisher"})
    with urllib.request.urlopen(request, timeout=60) as response:
        final = urlsplit(response.url)
        if final.scheme != "https" or final.hostname not in {
            "api.github.com",
            "github.com",
            "release-assets.githubusercontent.com",
            "objects.githubusercontent.com",
        }:
            raise ValueError("Unexpected release download origin")
        body = response.read(limit + 1)
    if len(body) > limit:
        raise ValueError("Release asset exceeds size limit")
    if digest is not None:
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
            raise ValueError("Release asset requires a SHA256 digest")
        if "sha256:" + hashlib.sha256(body).hexdigest() != digest:
            raise ValueError("Release asset checksum mismatch")
    return body


def publish(manifest: dict, directory: Path) -> dict:
    validate(manifest, "smalvik")
    tag = "v" + manifest["version"]
    release = json.loads(download(API + "/releases/tags/" + tag, 256 * 1024))
    if release["tag_name"] != tag or release["draft"] or release["prerelease"] or not release["published_at"]:
        raise ValueError("Only a published stable release is accepted")
    assets = {asset["name"]: asset for asset in release["assets"]}

    def asset(name: str, limit: int) -> bytes:
        record = assets[name]
        expected = DOWNLOAD + tag + "/" + name
        if record["state"] != "uploaded" or record["browser_download_url"] != expected:
            raise ValueError("Unexpected release asset")
        digest = record.get("digest")
        if not isinstance(digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
            raise ValueError("Release asset requires a SHA256 digest")
        body = download(expected, limit, digest)
        if len(body) != record["size"]:
            raise ValueError("Release asset size mismatch")
        return body

    if json.loads(asset("candidate.json", 65536)) != manifest:
        raise ValueError("Published manifest must match deployed images")
    reports = {"index.html": asset("index.html", MAX_HTML)}
    if "live-llm-allure.html" in assets:
        reports["live/index.html"] = asset("live-llm-allure.html", MAX_HTML)
    for body in reports.values():
        if b"<html" not in body[:4096].lower() or b"Allure" not in body[:4096]:
            raise ValueError("Expected a generated standalone Allure HTML document")
    publication = {
        "manifest": manifest,
        "reports": {name: hashlib.sha256(body).hexdigest() for name, body in reports.items()},
    }
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("An existing owned publication directory is required")
    version = directory / tag
    if version.is_symlink():
        raise ValueError("Report version must not be a symlink")
    # The staging directory is outside the public mount; incomplete files are never served.
    with tempfile.TemporaryDirectory(prefix=".allure-", dir=directory.parent) as temporary:
        staging = Path(temporary) / tag
        staging.mkdir(mode=0o755)
        for name, body in reports.items():
            path = staging / name
            path.parent.mkdir(mode=0o755, exist_ok=True)
            path.parent.chmod(0o755)
            path.write_bytes(body)
            path.chmod(0o644)
        metadata = staging / "publication.json"
        metadata.write_text(json.dumps(publication, indent=2) + "\n", encoding="utf-8")
        metadata.chmod(0o644)
        if version.exists():
            existing = json.loads((version / "publication.json").read_text())
            if (
                existing["manifest"] != manifest
                or not set(existing["reports"]).issubset(reports)
                or any(
                    publication["reports"][name] != digest
                    or hashlib.sha256((version / name).read_bytes()).hexdigest() != digest
                    for name, digest in existing["reports"].items()
                )
            ):
                raise ValueError("Existing version reports are immutable")
            # A later, separately verified live acceptance may be added once, never replaced.
            if "live/index.html" in reports and "live/index.html" not in existing["reports"]:
                if (version / "live").exists() or (version / "live").is_symlink():
                    raise ValueError("Unexpected existing live report directory")
                (staging / "live").rename(version / "live")
                os.replace(metadata, version / "publication.json")
        else:
            staging.chmod(0o755)
            staging.rename(version)
        # Each replacement is atomic; a failed download leaves the previous index intact.
        latest = Path(temporary) / "index.html"
        latest.write_bytes(reports["index.html"])
        latest.chmod(0o644)
        os.replace(latest, directory / "index.html")
        pointer = Path(temporary) / "latest.json"
        pointer.write_text(json.dumps(publication, indent=2) + "\n", encoding="utf-8")
        pointer.chmod(0o644)
        os.replace(pointer, directory / "latest.json")
    return {
        "status": "passed",
        "version": tag,
        "source_sha": manifest["source_sha"],
        "reports": list(reports),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    print(json.dumps(publish(load(args.manifest, "smalvik"), args.directory)))


if __name__ == "__main__":
    main()
