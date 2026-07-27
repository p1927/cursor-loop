#!/usr/bin/env bash
# Generic Cursor agent wake loop — persistent sentinel ticker.
# Configure via env: LOOP_ID, SENTINEL, INTERVAL, PROMPT, PIDFILE (optional).
set -euo pipefail

LOOP_ID="${LOOP_ID:?LOOP_ID is required}"
SENTINEL="${SENTINEL:?SENTINEL is required}"
INTERVAL="${INTERVAL:-120}"
PROMPT="${PROMPT:-Read your loop contract doc and run Ritual. Do not ask user.}"
PIDFILE="${PIDFILE:-${TMPDIR:-/tmp}/cursor-loop-${LOOP_ID}.pid}"

if ! [[ "$INTERVAL" =~ ^[0-9]+$ ]] || [[ "$INTERVAL" -lt 1 ]]; then
  echo "AGENT_LOOP_ERROR invalid INTERVAL=${INTERVAL}" >&2
  exit 1
fi

if [[ -f "$PIDFILE" ]]; then
  old_pid="$(cat "$PIDFILE" 2>/dev/null || true)"
  if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
    echo "AGENT_LOOP_ALREADY_RUNNING loop_id=${LOOP_ID} pid=${old_pid} interval=${INTERVAL}s sentinel=${SENTINEL}"
    exit 0
  fi
  rm -f "$PIDFILE"
fi

echo "$$" > "$PIDFILE"
trap 'rm -f "$PIDFILE"' EXIT INT TERM

echo "AGENT_LOOP_STARTED loop_id=${LOOP_ID} interval=${INTERVAL}s sentinel=${SENTINEL} pid=$$"

emit_tick() {
  local payload
  payload="$(LOOP_ID="$LOOP_ID" PROMPT="$PROMPT" SENTINEL="$SENTINEL" python3 - <<'PY'
import json, os
print(json.dumps({
    "loop_id": os.environ["LOOP_ID"],
    "prompt": os.environ["PROMPT"],
}))
PY
)"
  echo "${SENTINEL} ${payload}"
}

while true; do
  sleep "$INTERVAL"
  emit_tick
done
