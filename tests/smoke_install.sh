#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "=== smoke_install copy mode ==="
bash "$ROOT/install.sh" "$TMP" --copy --package-path vendor/cursor-loop

test -f "$TMP/.cursor/cursor-loop.json"
test -f "$TMP/vendor/cursor-loop/scripts/hook_bind.py"
test -x "$TMP/.cursor/hooks/loop-bind.sh"
test -x "$TMP/.cursor/hooks/_common.sh"
grep -q loop-bind.sh "$TMP/.cursor/hooks.json"

CID="copy-smoke"
payload="{\"conversation_id\":\"$CID\",\"workspace_roots\":[\"$TMP\"],\"prompt\":\"@docs/agents/demo.md keep working\"}"
mkdir -p "$TMP/docs/agents"
cat > "$TMP/docs/agents/demo.md" <<'MD'
## Loop config
| Field | Value |
|-------|-------|
| loop_id | `demo` |
| sentinel | `AGENT_LOOP_TICK_DEMO` |
| interval_sec | `30` |
| loop_script | `vendor/cursor-loop/scripts/agent-loop.sh` |
| contract_doc | `docs/agents/demo.md` |
MD

echo "$payload" | bash "$TMP/.cursor/hooks/loop-bind.sh"
test -f "$TMP/.cursor/loop-bindings/$CID.json"

bash "$TMP/vendor/cursor-loop/scripts/doctor.sh" "$TMP" >/dev/null
echo "PASS smoke_install"
