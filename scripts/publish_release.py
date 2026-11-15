"""Publish delivery evidence only after production smoke and immutable tag promotion."""

import argparse
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from delivery_manifest import load

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--manifest", type=Path, default=Path("artifacts/candidate.json"))
parser.add_argument("--namespace", default="smalvik")
args = parser.parse_args()
manifest = load(args.manifest, args.namespace)
tag = "v" + manifest["version"]
sha = manifest["source_sha"]
root = Path("artifacts/release")
root.mkdir(parents=True, exist_ok=True)
run_url = f"https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
notes = (
    f"# BIOCAD Workspace {tag}\n\n"
    "Fictional demo environment. This is an incremental delivery, not completion of all PRD capabilities. "
    "[Implemented capabilities and known gaps]"
    f"(https://github.com/{os.environ['GITHUB_REPOSITORY']}/blob/{sha}/docs/context/CURRENT_STATE.md) "
    "are recorded at the exact source snapshot.\n\n"
    f"Source: `{sha}`. [Checks, staging regression, production smoke and Allure artifacts]({run_url}).\n\n"
    f"[Application]({os.environ['PUBLIC_URL']}). "
    f"[View Allure in browser]({os.environ['PUBLIC_URL']}/allure/v{manifest['version']}/). "
    "Deployed images are the exact staging-tested digests:\n\n"
    + "\n".join(f"- {service}: `{reference}`" for service, reference in manifest["images"].items())
    + "\n\nTask change notes included in this source snapshot:\n\n"
)
for path in sorted(Path("docs/changes").glob("WB-*.md")):
    content = path.read_text(encoding="utf-8")
    if any(
        f"status: {state}\n" in content
        for state in ("implemented", "tested", "completed", "merged", "released")
    ):
        notes += f"- [{path.stem}](https://github.com/{os.environ['GITHUB_REPOSITORY']}/blob/{sha}/{path.as_posix()})\n"
(root / "CHANGELOG.md").write_text(notes, encoding="utf-8")
(root / "releases.json").write_text(
    json.dumps(
        {
            "version": manifest["version"],
            "published_at": datetime.now(UTC).isoformat(),
            "source_sha": sha,
            "images": manifest["images"],
            "checks_url": run_url,
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
subprocess.run(
    [
        "gh",
        "release",
        "create",
        tag,
        "--target",
        sha,
        "--title",
        f"BIOCAD Workspace {tag}",
        "--notes-file",
        str(root / "CHANGELOG.md"),
        str(args.manifest),
        str(root / "CHANGELOG.md"),
        str(root / "releases.json"),
        "artifacts/allure-server/index.html#allure.html",
    ],
    check=True,
)
