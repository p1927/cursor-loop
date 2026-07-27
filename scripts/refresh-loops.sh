#!/usr/bin/env bash
# Stop legacy persistent loops + wake shells; clear pidfiles for cursor-loop refresh.
# Preserves bindings unless --full-reset passed.
#
# Usage:
#   bash refresh-loops.sh [project_root]
#   bash refresh-loops.sh . --loop-id ux-relay
#   bash refresh-loops.sh . --full-reset   # also clears bindings/locks (needs --yes)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT="${1:-.}"
shift || true

LOOP_ID=""
FULL=0
YES=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --loop-id) LOOP_ID="${2:?}"; shift 2 ;;
    --full-reset) FULL=1; shift ;;
    --yes) YES=1; shift ;;
    -h|--help)
      sed -n '2,8p' "$0"
      exit 0
      ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

PROJECT="$(cd "$PROJECT" && pwd)"
TMP="${TMPDIR:-/tmp}"

kill_pattern() {
  local pat="$1"
  pkill -f "$pat" 2>/dev/null || true
}

if [[ -n "$LOOP_ID" ]]; then
  kill_pattern "cursor-loop-${LOOP_ID}"
  kill_pattern "LOOP_ID=${LOOP_ID}"
  rm -f "${TMP}/cursor-loop-${LOOP_ID}.pid" \
        "${TMP}/cursor-loop-${LOOP_ID}.wake.pid" \
        "${TMP}/cursor-loop-${LOOP_ID}.last_exit" \
        "${TMP}/cursor-loop-${LOOP_ID}.wake.armed"
  echo "refresh-loops: stopped processes and pidfiles for loop_id=${LOOP_ID}"
else
  kill_pattern "tools/cursor-loop/scripts/agent-loop.sh"
  kill_pattern "scripts/agent-.*-loop.sh"
  kill_pattern "AGENT_LOOP_TICK_"
  kill_pattern "AGENT_LOOP_WAKE_"
  rm -f "${TMP}"/cursor-loop-*.pid \
        "${TMP}"/cursor-loop-*.wake.pid \
        "${TMP}"/cursor-loop-*.last_exit \
        "${TMP}"/cursor-loop-*.wake.armed 2>/dev/null || true
  echo "refresh-loops: stopped all cursor-loop and legacy loop processes"
  echo "refresh-loops: persistent agent-loop.sh removed (window instances use dynamic arm-wake.sh only)"
fi

if [[ "$FULL" -eq 1 ]]; then
  if [[ "$YES" -ne 1 ]]; then
    echo "refresh-loops: --full-reset requires --yes" >&2
    exit 1
  fi
  bash "${SCRIPT_DIR}/force-reset.sh" "$PROJECT" --all --yes
else
  bash "${SCRIPT_DIR}/loop-status.sh" 2>/dev/null || true
  echo
  echo "Bindings preserved. In each chat, paste: @docs/window-instances/<loop_id>/INSTANCE.md keep working"
  echo "Agent will arm dynamic wake via arm-wake.sh (see agent-loop-contract.mdc)."
fi
