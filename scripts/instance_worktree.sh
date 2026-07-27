#!/usr/bin/env bash
# Window instance git worktree lifecycle — create | status | merge | remove | prune
# Usage: instance_worktree.sh <command> [project] [--loop-id ID] [--item-id ID] [--state-file PATH]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CMD="${1:-}"
shift || true

ROOT="${1:-.}"
if [[ -d "$ROOT" ]]; then
  shift || true
else
  ROOT="."
fi

LOOP_ID=""
ITEM_ID=""
STATE_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --loop-id) LOOP_ID="${2:?}"; shift 2 ;;
    --item-id) ITEM_ID="${2:?}"; shift 2 ;;
    --state-file) STATE_FILE="${2:?}"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$CMD" ]]; then
  echo "Usage: instance_worktree.sh <create|status|merge|remove|prune> [project] --loop-id ID [--item-id ID] [--state-file PATH]" >&2
  exit 1
fi

ROOT="$(cd "$ROOT" && pwd)"

run_py() {
  python3 "${SCRIPT_DIR}/instance_worktree.py" "$CMD" "$ROOT" --loop-id "$LOOP_ID" \
    ${ITEM_ID:+--item-id "$ITEM_ID"} \
    ${STATE_FILE:+--state-file "$STATE_FILE"}
}

case "$CMD" in
  create|status|merge|remove|prune) run_py ;;
  *)
    echo "Unknown command: $CMD" >&2
    exit 1
    ;;
esac
