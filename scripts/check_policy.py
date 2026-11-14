"""Small CI baseline: task branch, Conventional Commit PR title, and secret file paths."""

import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMMIT_PATTERN = r"(?:feat|fix|chore|test|ci|docs|refactor|build|perf|style|revert)(?:\([^)]+\))?!?: .+"


def main() -> None:
    branch = os.environ.get("PR_BRANCH", "")
    promotion = branch == "develop" and os.environ.get("PR_BASE_BRANCH") == "main"
    if branch:
        if not promotion:
            match = re.fullmatch(r"(?:feat|fix|chore|test|ci|docs|refactor)/(wb-\d{2})-[a-z0-9-]+", branch)
            assert match, "Use a purpose-specific task branch; develop may only be promoted into main"
            note = ROOT / "docs" / "changes" / f"{match[1].upper()}.md"
            assert note.is_file(), f"Missing change note: {note.name}"
            assert re.search(
                r"^status: (?:implemented|tested|completed|merged|released)$",
                note.read_text(encoding="utf-8"),
                re.MULTILINE,
            ), "Change note is still a draft"
        assert re.fullmatch(
            COMMIT_PATTERN, os.environ.get("PR_TITLE", "")
        ), "PR title must follow Conventional Commits"
    base, head = os.environ.get("BASE_SHA", ""), os.environ.get("HEAD_SHA", "")
    if base and head and base != "0" * 40:
        assert all(re.fullmatch(r"[0-9a-fA-F]{40}", value) for value in (base, head)), "Invalid Git SHA"
        subjects = subprocess.check_output(
            ["git", "log", "--no-merges", "--format=%s", f"{base}..{head}"],
            cwd=ROOT,
            text=True,
        ).splitlines()
        assert all(
            re.fullmatch(COMMIT_PATTERN, subject) for subject in subjects
        ), "Commit messages must follow Conventional Commits"
    tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    forbidden = [
        path
        for path in tracked
        if path
        and (
            (Path(path).name.startswith(".env") and Path(path).name != ".env.example")
            or Path(path).suffix.lower() in {".pem", ".key", ".p12"}
            or path.startswith("secrets/")
        )
    ]
    assert not forbidden, "Secret file paths must not be tracked"
    print("PASS: branch/task-note/commit checks (when context supplied) and secret-file baseline")


if __name__ == "__main__":
    main()
