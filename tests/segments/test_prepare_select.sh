#!/usr/bin/env bash
# Segment: prepare_select_tick + worktree requirement
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPTS="${ROOT}/scripts"
PROJECT="$(cd "$ROOT/../.." && pwd)"
export PYTHONPATH="${SCRIPTS}:${PYTHONPATH:-}"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cat > "${TMP}/STATE.md" <<'EOF'
## CHECKPOINT
| Field | Value |
| current_item_id | relay-999 |
| worktree_status | none |

## IN_PROGRESS
| id | started_at | notes |
| relay-999 | 2026-07-27 | test item |
EOF

if bash "${SCRIPTS}/prepare_select_tick.sh" "$TMP" \
  --state-file STATE.md --loop-id worker-relay; then
  echo "FAIL: should require worktree for engineer with item"
  exit 1
fi
echo "OK prepare_select requires worktree when item set"

OUT="$(bash "${SCRIPTS}/prepare_select_tick.sh" "$TMP" \
  --state-file STATE.md --loop-id po-relay 2>&1 || true)"
echo "$OUT" | grep -q "requires_worktree=no" || {
  echo "FAIL: po-relay should not require worktree by default"
  exit 1
}
echo "OK prepare_select skips worktree for product archetype"

if [[ -d "$PROJECT/.git" ]]; then
  bash "${SCRIPTS}/prepare_select_tick.sh" "$PROJECT" \
    --state-file docs/window-instances/worker-relay/STATE.md \
    --loop-id worker-relay >/dev/null || true
  echo "OK prepare_select runs against Habits worker-relay STATE"
fi

echo "OK prepare select segment"
