#!/usr/bin/env bash
# Phase 3 prep — worktree requirement detection for window instances
# Usage: prepare_select_tick.sh [project] --state-file PATH [--loop-id ID]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${1:-.}"
if [[ -d "$ROOT" ]]; then
  shift || true
else
  ROOT="."
fi

STATE_FILE=""
LOOP_ID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --state-file) STATE_FILE="${2:?}"; shift 2 ;;
    --loop-id) LOOP_ID="${2:?}"; shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "$STATE_FILE" ]]; then
  echo "Usage: prepare_select_tick.sh [project] --state-file PATH [--loop-id ID]" >&2
  exit 1
fi

ROOT="$(cd "$ROOT" && pwd)"
args=(python3 "${SCRIPT_DIR}/prepare_select_tick.py" "$ROOT" --state-file "$STATE_FILE")
[[ -n "$LOOP_ID" ]] && args+=(--loop-id "$LOOP_ID")
"${args[@]}"
