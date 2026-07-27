#!/usr/bin/env bash
# Phase 5 prep — detect diff and print suggested CHECKPOINT review fields.
# Usage: prepare_review_tick.sh [project_root] --state-file docs/window-instances/worker-relay/STATE.md [--loop-id worker-relay]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${1:-.}"
shift || true

STATE_FILE=""
LOOP_ID=""

APPLY=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --state-file) STATE_FILE="${2:?}"; shift 2 ;;
    --loop-id) LOOP_ID="${2:?}"; shift 2 ;;
    --apply) APPLY=1; shift ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$STATE_FILE" ]]; then
  echo "Usage: prepare_review_tick.sh [project] --state-file PATH [--loop-id ID]" >&2
  exit 1
fi

args=(python3 "${SCRIPT_DIR}/prepare_review_tick.py" "$(cd "$ROOT" && pwd)" --state-file "$STATE_FILE")
if [[ -n "$LOOP_ID" ]]; then
  args+=(--loop-id "$LOOP_ID")
fi
if [[ -n "$APPLY" ]]; then
  args+=(--apply)
fi
exec "${args[@]}"
