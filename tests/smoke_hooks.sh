#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PKG="$ROOT"
HABITS="$(cd "$ROOT/../.." && pwd)"

echo "=== smoke_hooks (Habits install) ==="
bash "$PKG/install.sh" "$HABITS" --symlink >/dev/null

HOOK="$HABITS/.cursor/hooks/loop-bind.sh"
SURV="$HABITS/.cursor/hooks/loop-survival.sh"
CID="smoke-$(date +%s)"

bind_payload="{\"conversation_id\":\"$CID\",\"workspace_roots\":[\"$HABITS\"],\"prompt\":\"@docs/agents/worker-relay.md keep working\"}"
echo "$bind_payload" | bash "$HOOK"
test -f "$HABITS/.cursor/loop-bindings/$CID.json"

stop_payload="{\"conversation_id\":\"$CID\",\"workspace_roots\":[\"$HABITS\"],\"prompt\":\"stop loop\"}"
echo "$stop_payload" | bash "$HOOK"
grep -q '"stopped": true' "$HABITS/.cursor/loop-bindings/$CID.json"

OUT=$(echo "{\"conversation_id\":\"$CID\",\"workspace_roots\":[\"$HABITS\"]}" | bash "$SURV")
test -z "$OUT"

python3 -c "
import json
p='$HABITS/.cursor/loop-bindings/$CID.json'
d=json.load(open(p)); d['stopped']=False; json.dump(d, open(p,'w'), indent=2)
"
OUT=$(echo "{\"conversation_id\":\"$CID\",\"workspace_roots\":[\"$HABITS\"]}" | bash "$SURV")
echo "$OUT" | python3 -c "import sys,json; assert 'followup_message' in json.load(sys.stdin)"

keep_payload="{\"conversation_id\":\"$CID\",\"workspace_roots\":[\"$HABITS\"],\"prompt\":\"keep working\"}"
echo "$keep_payload" | bash "$HOOK"
grep -q '"stopped": false' "$HABITS/.cursor/loop-bindings/$CID.json"

rm -f "$HABITS/.cursor/loop-bindings/$CID.json"
echo "PASS smoke_hooks"
