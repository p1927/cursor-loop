#!/usr/bin/env bash
# Report UP/DOWN for cursor-loop pidfiles.
set -euo pipefail

JSON=0
FILTER_LOOP_ID=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --json) JSON=1; shift ;;
    --loop-id)
      FILTER_LOOP_ID="${2:?--loop-id requires value}"
      shift 2
      ;;
    -h|--help)
      echo "Usage: $0 [--json] [--loop-id ID]"
      exit 0
      ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

TMP="${TMPDIR:-/tmp}"
shopt -s nullglob
found=0
json_items=()

for pidfile in "${TMP}"/cursor-loop-*.pid; do
  found=1
  name="$(basename "$pidfile" .pid)"
  loop_id="${name#cursor-loop-}"
  if [[ -n "$FILTER_LOOP_ID" && "$loop_id" != "$FILTER_LOOP_ID" ]]; then
    continue
  fi
  pid="$(cat "$pidfile" 2>/dev/null || true)"
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    if [[ "$JSON" -eq 1 ]]; then
      json_items+=("{\"name\":\"${name}\",\"pidfile\":\"${pidfile}\",\"status\":\"UP\",\"pid\":\"${pid}\"}")
    else
      echo "UP   ${name} pid=${pid}"
    fi
  else
    if [[ "$JSON" -eq 1 ]]; then
      json_items+=("{\"name\":\"${name}\",\"pidfile\":\"${pidfile}\",\"status\":\"DOWN\",\"pid\":\"\"}")
    else
      echo "DOWN ${name} (stale pidfile)"
    fi
  fi
done

if [[ "$JSON" -eq 1 ]]; then
  if [[ ${#json_items[@]} -eq 0 ]]; then
    echo "[]"
  else
    (IFS=,; echo "[${json_items[*]}]")
  fi
elif [[ "$found" -eq 0 ]]; then
  echo "No loop pidfiles found under ${TMP}"
fi
