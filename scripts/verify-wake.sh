#!/usr/bin/env bash
# Verify dynamic wake shell is armed (agent runs before ending every turn in dynamic mode).
# Usage: verify-wake.sh <loop_id>
# Exit 0 = ARMED, 1 = DOWN
set -euo pipefail

LOOP_ID="${1:?Usage: verify-wake.sh <loop_id>}"
WAKE_PIDFILE="${TMPDIR:-/tmp}/cursor-loop-${LOOP_ID}.wake.pid"

if [[ -f "$WAKE_PIDFILE" ]]; then
  PID="$(cat "$WAKE_PIDFILE" 2>/dev/null || true)"
  if [[ -n "$PID" ]] && kill -0 "$PID" 2>/dev/null; then
    echo "WAKE_ARMED loop_id=${LOOP_ID} pid=${PID} pidfile=${WAKE_PIDFILE}"
    exit 0
  fi
fi

echo "WAKE_DOWN loop_id=${LOOP_ID} pidfile=${WAKE_PIDFILE}"
exit 1
