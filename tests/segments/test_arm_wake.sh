#!/usr/bin/env bash
# Segment: arm-wake.sh — idempotent wake arming.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck source=../helpers/test_lib.sh
source "${ROOT}/tests/helpers/test_lib.sh"

test_arm_wake_idempotent() {
  local tmp loop_id
  tmp="$(mktemp -d)"
  loop_id="seg-arm-$(date +%s)"
  export TMPDIR="$tmp"

  mkdir -p "$tmp/docs"
  cat > "$tmp/docs/state.md" <<'EOF'
## CHECKPOINT
| Field | Value |
| phase | `8-close` |
| review_status | skipped |
| review_skip_reason | test |
| code_changed | no |
EOF

  LOOP_ID="$loop_id" \
  WAKE_SENTINEL="AGENT_LOOP_WAKE_TEST" \
  INTERVAL=1 \
  CONTRACT_DOC="docs/agents/test.md" \
  STATE_FILE="docs/state.md" \
  PROJECT_ROOT="$tmp" \
  bash "${ROOT}/scripts/arm-wake.sh" &
  local pid=$!

  sleep 0.3
  if ! LOOP_ID="$loop_id" WAKE_SENTINEL="AGENT_LOOP_WAKE_TEST" INTERVAL=1 \
    CONTRACT_DOC="docs/agents/test.md" \
    STATE_FILE="docs/state.md" \
    PROJECT_ROOT="$tmp" \
    bash "${ROOT}/scripts/arm-wake.sh" | grep -q WAKE_ALREADY_ARMED; then
    kill "$pid" 2>/dev/null || true
    rm -rf "$tmp"
    echo "FAIL expected WAKE_ALREADY_ARMED"
    exit 1
  fi

  kill "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
  rm -rf "$tmp"
  echo "OK arm-wake idempotent guard"
}

test_arm_wake_idempotent
