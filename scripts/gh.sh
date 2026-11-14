#!/usr/bin/env bash
# Run GitHub CLI inside Docker (no local gh needed). Token is read from .env (GITHUB_TOKEN)
# and passed via environment only; it is never printed.
# Usage: scripts/gh.sh issue list --label agent:codex
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export MSYS_NO_PATHCONV=1
if [ -z "${GITHUB_TOKEN:-}" ] && [ -f "$ROOT/.env" ]; then
  GITHUB_TOKEN="$(grep -E '^GITHUB_TOKEN=' "$ROOT/.env" | head -1 | cut -d= -f2-)"
fi
if [ -z "${GITHUB_REPO:-}" ] && [ -f "$ROOT/.env" ]; then
  GITHUB_REPO="$(grep -E '^GITHUB_REPO=' "$ROOT/.env" | head -1 | cut -d= -f2-)"
fi
: "${GITHUB_TOKEN:?GITHUB_TOKEN missing in .env}"
# GITHUB_REPO may be a URL or owner/name; gh wants owner/name.
REPO_SLUG="$(printf '%s' "${GITHUB_REPO:-}" | sed -E 's#^https?://github.com/##; s#\.git$##; s#/$##')"
IMAGE=biocad-devtools:local
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  docker build -q -t "$IMAGE" "$ROOT/infra/devtools" >/dev/null
fi
TTY_FLAGS="-i"; [ -t 1 ] && TTY_FLAGS="-it"
docker run --rm $TTY_FLAGS \
  -e GH_TOKEN="$GITHUB_TOKEN" -e GH_REPO="$REPO_SLUG" -e GH_PROMPT_DISABLED=1 -e NO_COLOR=1 \
  -v "$ROOT:/repo" -w /repo \
  "$IMAGE" gh "$@"
