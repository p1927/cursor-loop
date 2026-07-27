#!/usr/bin/env bash
# Verify a loop process is alive (agent runs this before ending every turn).
# Usage: verify-loop.sh <loop_id>
# Exit 0 = UP, 1 = DOWN
set -euo pipefail

LOOP_ID="${1:?Usage: verify-loop.sh <loop_id>}"
PIDFILE="${TMPDIR:-/tmp}/cursor-loop-${LOOP_ID}.pid"

if [[ -f "$PIDFILE" ]]; then
  PID="$(cat "$PIDFILE" 2>/dev/null || true)"
  if [[ -n "$PID" ]] && kill -0 "$PID" 2>/dev/null; then
    echo "LOOP_UP loop_id=${LOOP_ID} pid=${PID} pidfile=${PIDFILE}"
    exit 0
  fi
fi

echo "LOOP_DOWN loop_id=${LOOP_ID} pidfile=${PIDFILE}"
exit 1
