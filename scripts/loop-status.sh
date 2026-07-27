#!/usr/bin/env bash
# Report UP/DOWN for cursor-loop pidfiles and dynamic wake shells.
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

report_line() {
  local kind="$1" name="$2" status="$3" pid="$4" path="$5"
  if [[ "$JSON" -eq 1 ]]; then
    json_items+=("{\"kind\":\"${kind}\",\"name\":\"${name}\",\"status\":\"${status}\",\"pid\":\"${pid}\",\"path\":\"${path}\"}")
  else
    echo "${status}  ${name} pid=${pid} (${kind})"
  fi
}

for pidfile in "${TMP}"/cursor-loop-*.pid; do
  [[ "$pidfile" == *.wake.pid ]] && continue
  found=1
  name="$(basename "$pidfile" .pid)"
  loop_id="${name#cursor-loop-}"
  if [[ -n "$FILTER_LOOP_ID" && "$loop_id" != "$FILTER_LOOP_ID" ]]; then
    continue
  fi
  pid="$(cat "$pidfile" 2>/dev/null || true)"
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    report_line "persistent" "$name" "STALE" "$pid" "$pidfile"
    if [[ "$JSON" -eq 0 ]]; then
      echo "  ^ legacy agent-loop.sh — run: cwin refresh (window instances use dynamic wake only)"
    fi
  else
    report_line "persistent" "$name" "DOWN" "" "$pidfile"
  fi
done

for wakefile in "${TMP}"/cursor-loop-*.wake.pid; do
  found=1
  base="$(basename "$wakefile" .wake.pid)"
  loop_id="${base#cursor-loop-}"
  if [[ -n "$FILTER_LOOP_ID" && "$loop_id" != "$FILTER_LOOP_ID" ]]; then
    continue
  fi
  pid="$(cat "$wakefile" 2>/dev/null || true)"
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    report_line "dynamic-wake" "$base" "ARMED" "$pid" "$wakefile"
  else
    report_line "dynamic-wake" "$base" "DOWN" "" "$wakefile"
  fi
done

if [[ "$JSON" -eq 1 ]]; then
  if [[ ${#json_items[@]} -eq 0 ]]; then
    echo "[]"
  else
    (IFS=,; echo "[${json_items[*]}]")
  fi
elif [[ "$found" -eq 0 ]]; then
  echo "No cursor-loop pidfiles under ${TMP}"
fi
