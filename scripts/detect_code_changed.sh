#!/usr/bin/env bash
# Phase 5 helper — detect code changes in this window's review scope.
# Usage: detect_code_changed.sh [project] [--loop-id ID] [--state-file PATH]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${1:-.}"
shift || true

LOOP_ID=""
STATE_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --loop-id) LOOP_ID="${2:?}"; shift 2 ;;
    --state-file) STATE_FILE="${2:?}"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

args=(python3 "${SCRIPT_DIR}/review_scope.py" "$(cd "$ROOT" && pwd)" --stat)
if [[ -n "$LOOP_ID" ]]; then
  args+=(--loop-id "$LOOP_ID")
fi
if [[ -n "$STATE_FILE" ]]; then
  args+=(--state-file "$STATE_FILE")
fi

exec "${args[@]}"
