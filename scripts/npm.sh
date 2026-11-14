#!/usr/bin/env bash
# Run npm/npx inside Docker (no local Node needed).
# Usage: scripts/npm.sh <dir relative to repo> <npm args...>
# Example: scripts/npm.sh apps/web ci ; scripts/npm.sh apps/web run test
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIR="${1:?directory, e.g. apps/web}"; shift
export MSYS_NO_PATHCONV=1
TTY_FLAGS="-i"; [ -t 1 ] && TTY_FLAGS="-it"
# Publish the Vite dev server only when asked: VITE_PORT=5173 scripts/npm.sh apps/web run dev -- --host
PORT_FLAGS=""; [ -n "${VITE_PORT:-}" ] && PORT_FLAGS="-p ${VITE_PORT}:5173"
# node_modules lives in a named volume so Linux binaries never mix with the Windows checkout.
NM_VOL="biocad-nm-$(printf '%s' "$DIR" | tr '/' '-')"
docker run --rm $TTY_FLAGS $PORT_FLAGS \
  -v "$ROOT:/repo" -w "/repo/$DIR" \
  -v "$NM_VOL:/repo/$DIR/node_modules" \
  -v biocad-npm-cache:/root/.npm \
  node:22.12.0-bookworm-slim npm "$@"
