#!/usr/bin/env bash
# Run uv inside Docker (no local uv needed). Usage: scripts/uv.sh <service> <uv args...>
# Example: scripts/uv.sh booking lock ; scripts/uv.sh booking run pytest -q tests/unit
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE="${1:?service name: booking|assistant}"; shift
export MSYS_NO_PATHCONV=1
docker run --rm -i \
  -v "$ROOT/services/$SERVICE:/srv" -w /srv \
  -v biocad-uv-cache:/root/.cache/uv \
  -e UV_PROJECT_ENVIRONMENT=/opt/venv \
  ghcr.io/astral-sh/uv:0.5.11-python3.12-bookworm-slim uv "$@"
