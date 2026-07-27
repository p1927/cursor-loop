#!/usr/bin/env bash
# Segment: agent-loop.sh — start, verify, kill, cleanup.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
# shellcheck source=../helpers/test_lib.sh
source "$(dirname "$0")/../helpers/test_lib.sh"

test_segment_agent_loop() {
  local tmp
  tmp="$(test_mkdir)"
  export TMPDIR="${tmp}/tmp"
  mkdir -p "$TMPDIR"

  local loop_id="seg-test-$$"
  LOOP_ID="$loop_id" SENTINEL="AGENT_LOOP_TICK_SEG" INTERVAL=3600 \
    PROMPT='test' bash "${ROOT}/scripts/agent-loop.sh" &
  local pid=$!
  sleep 0.5

  test -f "${TMPDIR}/cursor-loop-${loop_id}.pid"
  bash "${ROOT}/scripts/verify-loop.sh" "$loop_id"

  kill -TERM "$pid" 2>/dev/null || true
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    kill -0 "$pid" 2>/dev/null || break
    sleep 0.1
  done
  kill -9 "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
  rm -f "${TMPDIR}/cursor-loop-${loop_id}.pid"
  test_rmdir "$tmp"
}

test_segment_agent_loop
