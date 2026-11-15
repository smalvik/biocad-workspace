import json
import time
from pathlib import Path

PATH = Path("/tmp/biocad-notification-health.json")


def main():
    try:
        data = json.loads(PATH.read_text())
        return 0 if data["storage_ok"] and time.time() - data["at"] < 15 else 1
    except (OSError, ValueError, KeyError):
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
