#!/usr/bin/env bash
# Segment: ritual_phase + validate_ritual_gate
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPTS="${ROOT}/scripts"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

export PYTHONPATH="${SCRIPTS}:${PYTHONPATH:-}"

python3 - <<'PY'
import ritual_phase as rp

assert rp.validate_transition("1-wake", "2-orient") == (True, "")
ok, msg = rp.validate_transition("4-execute", "9-arm")
assert not ok and "skip" in msg
assert rp.allowed_phase_on_wake("9-arm") == "1-wake"
print("OK ritual_phase transitions")
PY

STATE="${TMP}/STATE.md"
cat > "$STATE" <<'EOF'
## CHECKPOINT
| Field | Value |
| phase | `4-execute` |
| review_status | pending |
| code_changed | no |
EOF

if python3 "${SCRIPTS}/validate_ritual_gate.py" \
  --project "$TMP" --loop-id worker-relay --state-file STATE.md --mode arm 2>/dev/null; then
  echo "FAIL: gate should reject phase 4 before arm"
  exit 1
fi
echo "OK gate rejects early phase"

cat > "$STATE" <<'EOF'
## CHECKPOINT
| Field | Value |
| phase | `8-close` |
| review_status | skipped |
| review_skip_reason | docs only |
| code_changed | no |
EOF

python3 "${SCRIPTS}/validate_ritual_gate.py" \
  --project "$TMP" --loop-id worker-relay --state-file STATE.md --mode arm
echo "OK gate accepts 8-close skipped review"

cat > "$STATE" <<'EOF'
## CHECKPOINT
| Field | Value |
| phase | `9-arm` |
| review_status | skipped |
| review_skip_reason | test |
| code_changed | no |
EOF

if python3 "${SCRIPTS}/validate_ritual_gate.py" \
  --project "$TMP" --loop-id worker-relay --state-file STATE.md --mode arm 2>/dev/null; then
  echo "FAIL: gate should reject phase 9-arm before arm"
  exit 1
fi
echo "OK gate rejects 9-arm before arm"

PAYLOAD="$(python3 "${SCRIPTS}/build_wake_prompt.py" \
  --loop-id worker-relay \
  --contract-doc docs/window-instances/worker-relay/INSTANCE.md \
  --state-file docs/window-instances/worker-relay/STATE.md \
  --project "$(cd "$ROOT/../.." && pwd)" 2>/dev/null || true)"

if echo "$PAYLOAD" | grep -q '"allowed_phase": "1-wake"'; then
  echo "OK wake prompt uses allowed_phase 1-wake"
else
  echo "WARN: could not verify wake prompt in Habits project (optional)"
fi

echo "OK ritual gate segment"
