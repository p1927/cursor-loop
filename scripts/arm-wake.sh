#!/usr/bin/env bash
# Dynamic-mode one-shot wake — monitored shell sleeps then prints wake_sentinel JSON line.
# Env: LOOP_ID, WAKE_SENTINEL, INTERVAL, CONTRACT_DOC, STATE_FILE (optional), PROJECT_ROOT (optional)
set -euo pipefail

LOOP_ID="${LOOP_ID:?LOOP_ID is required}"
WAKE_SENTINEL="${WAKE_SENTINEL:?WAKE_SENTINEL is required}"
INTERVAL="${INTERVAL:-120}"
CONTRACT_DOC="${CONTRACT_DOC:?CONTRACT_DOC is required}"
STATE_FILE="${STATE_FILE:-}"
PROJECT_ROOT="${PROJECT_ROOT:-.}"

if ! [[ "$INTERVAL" =~ ^[0-9]+$ ]] || [[ "$INTERVAL" -lt 1 ]]; then
  echo "AGENT_LOOP_ERROR invalid INTERVAL=${INTERVAL}" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WAKE_PIDFILE="${WAKE_PIDFILE:-${TMPDIR:-/tmp}/cursor-loop-${LOOP_ID}.wake.pid}"
LAST_ARMED="${TMPDIR:-/tmp}/cursor-loop-${LOOP_ID}.wake.armed"

if [[ -n "$STATE_FILE" && -f "$PROJECT_ROOT/$STATE_FILE" ]]; then
  gate_args=(
    --project "$PROJECT_ROOT"
    --loop-id "$LOOP_ID"
    --state-file "$STATE_FILE"
    --mode arm
  )
  if [[ -n "${RITUAL_GATE_FORCE:-}" ]]; then
    gate_args+=(--force)
  fi
  python3 "${SCRIPT_DIR}/validate_ritual_gate.py" "${gate_args[@]}" || exit 1
fi

if [[ -f "$WAKE_PIDFILE" ]]; then
  old_pid="$(cat "$WAKE_PIDFILE" 2>/dev/null || true)"
  if [[ -n "$old_pid" ]] && kill -0 "$old_pid" 2>/dev/null; then
    echo "WAKE_ALREADY_ARMED loop_id=${LOOP_ID} pid=${old_pid} interval=${INTERVAL}s sentinel=${WAKE_SENTINEL}"
    exit 0
  fi
  rm -f "$WAKE_PIDFILE"
fi

PAYLOAD="$(python3 "${SCRIPT_DIR}/build_wake_prompt.py" \
  --loop-id "$LOOP_ID" \
  --contract-doc "$CONTRACT_DOC" \
  --state-file "$STATE_FILE" \
  --project "$PROJECT_ROOT")"

echo "$$" > "$WAKE_PIDFILE"
date -u +"%Y-%m-%dT%H:%M:%SZ" > "$LAST_ARMED" 2>/dev/null || true

cleanup() {
  rm -f "$WAKE_PIDFILE"
}
trap cleanup EXIT INT TERM

echo "WAKE_ARMED loop_id=${LOOP_ID} interval=${INTERVAL}s sentinel=${WAKE_SENTINEL} pid=$$"

sleep "$INTERVAL"
echo "${WAKE_SENTINEL} ${PAYLOAD}"
