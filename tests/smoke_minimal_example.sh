#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
EXAMPLE="${ROOT}/examples/minimal-project"

bash "${EXAMPLE}/setup.sh"
test -f "${EXAMPLE}/vendor/cursor-loop/scripts/agent-loop.sh"
test -f "${EXAMPLE}/.cursor/cursor-loop.json"
test -f "${EXAMPLE}/docs/agents/hello-loop.md"
echo "PASS smoke_minimal_example"
