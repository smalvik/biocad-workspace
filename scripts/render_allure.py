"""Collect actual nested result directories without shell glob assumptions."""

import argparse
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("root", type=Path)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
directories = sorted(
    {path.parent for path in args.root.rglob("*-result.json") if path.parent.name == "allure-results"}
)
if not directories:
    raise SystemExit("No actual Allure results found")
subprocess.run(
    [
        "npx",
        "--yes",
        "--package=allure-commandline@2.32.0",
        "allure",
        "generate",
        *map(str, directories),
        "--single-file",
        "--clean",
        "-o",
        str(args.output),
    ],
    check=True,
)
