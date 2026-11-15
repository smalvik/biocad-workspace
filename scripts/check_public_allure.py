"""Verify public reports are served inline and match the deployed release manifest."""

import argparse
import hashlib
import json
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from delivery_manifest import load
from publish_allure import MAX_HTML


def check(base_url: str, manifest: dict) -> None:
    origin = urlsplit(base_url)
    if (
        origin.scheme not in {"http", "https"}
        or origin.path not in {"", "/"}
        or origin.query
        or origin.fragment
    ):
        raise ValueError("Expected a bare application origin")
    base = base_url.rstrip("/")
    with urllib.request.urlopen(base + "/allure/latest.json", timeout=30) as response:
        publication = json.loads(response.read(65536))
    if publication["manifest"] != manifest:
        raise ValueError("Public report source does not match the deployed release")
    for path in ("/allure/", "/allure/v" + manifest["version"] + "/"):
        with urllib.request.urlopen(base + path, timeout=60) as response:
            if response.headers.get_content_type() != "text/html":
                raise ValueError("Report must be HTML")
            if response.headers.get("Content-Disposition", "").lower() != "inline":
                raise ValueError("Report must open inline, not download")
            body = response.read(MAX_HTML + 1)
        if hashlib.sha256(body).hexdigest() != publication["reports"]["index.html"]:
            raise ValueError("Served report differs from the published artifact")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("artifacts/public-allure/allure-results"))
    args = parser.parse_args()
    manifest = load(args.manifest, "smalvik")
    ident = str(uuid4())
    result = {
        "uuid": ident,
        "name": "Public Allure inline/source/checksum smoke",
        "fullName": "delivery.public_allure",
        "start": int(time.time() * 1000),
        "labels": [
            {"name": name, "value": value}
            for name, value in {
                "suite": "delivery-allure",
                "run_type": "smoke",
                "environment": args.base_url,
                "git_sha": manifest["source_sha"],
                "release_version": manifest["version"],
            }.items()
        ],
    }
    try:
        check(args.base_url, manifest)
        result["status"] = "passed"
        print("PASS: public Allure inline HTML, source and checksum")
    except Exception:
        result["status"] = "failed"
        raise
    finally:
        result["stop"] = int(time.time() * 1000)
        args.output.mkdir(parents=True, exist_ok=True)
        (args.output / (ident + "-result.json")).write_text(json.dumps(result), encoding="utf-8")


if __name__ == "__main__":
    main()
