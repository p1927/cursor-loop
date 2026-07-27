#!/usr/bin/env bash
# Bootstrap the minimal example project (run from cursor-loop repo root or example dir).
set -euo pipefail

EXAMPLE_DIR="$(cd "$(dirname "$0")" && pwd)"
PKG="$(cd "${EXAMPLE_DIR}/../.." && pwd)"

bash "${PKG}/install.sh" "${EXAMPLE_DIR}" \
  --copy \
  --package-path vendor/cursor-loop \
  --contracts-dir docs/agents

echo
echo "Example ready: ${EXAMPLE_DIR}"
echo "Paste in Cursor Agent: @docs/agents/hello-loop.md keep working"
