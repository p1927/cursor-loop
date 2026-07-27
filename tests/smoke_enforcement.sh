#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HABITS="$(cd "$ROOT/../.." && pwd)"

echo "=== smoke_enforcement ==="
python3 "${ROOT}/scripts/validate_contracts.py" "${HABITS}"

# force-reset dry run on temp binding
TMP="${HABITS}/.cursor/loop-bindings"
mkdir -p "$TMP"
TEST_FILE="${TMP}/smoke-reset-test.json"
echo '{"loop_id":"smoke-test"}' > "$TEST_FILE"
python3 "${ROOT}/scripts/force_reset.py" "${HABITS}" --bindings --json | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'smoke-reset-test' in d['bindings']"
test ! -f "$TEST_FILE"

# loop lock via hook
HOOK="${HABITS}/.cursor/hooks/loop-bind.sh"
C1="lock-test-a-$$"
C2="lock-test-b-$$"
PAYLOAD="{\"conversation_id\":\"${C1}\",\"workspace_roots\":[\"${HABITS}\"],\"prompt\":\"@docs/agents/worker-relay.md keep working\"}"
echo "$PAYLOAD" | bash "$HOOK"
PAYLOAD2="{\"conversation_id\":\"${C2}\",\"workspace_roots\":[\"${HABITS}\"],\"prompt\":\"@docs/agents/worker-relay.md keep working\"}"
echo "$PAYLOAD2" | bash "$HOOK"
python3 -c "
import json
from pathlib import Path
b=json.loads(Path('${HABITS}/.cursor/loop-bindings/${C2}.json').read_text())
assert b.get('bind_blocked') is True
"
rm -f "${HABITS}/.cursor/loop-bindings/${C1}.json" "${HABITS}/.cursor/loop-bindings/${C2}.json"
rm -f "${HABITS}/.cursor/loop-bindings/locks/worker-relay.json"

echo "PASS smoke_enforcement"
