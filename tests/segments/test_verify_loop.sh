#!/usr/bin/env bash
# Segment: verify-loop.sh exit codes.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
source "$(dirname "$0")/../helpers/test_lib.sh"

test_segment_verify_loop() {
  local tmp
  tmp="$(test_mkdir)"
  export TMPDIR="${tmp}/tmp"
  mkdir -p "$TMPDIR"

  local loop_id="verify-$$"
  if bash "${ROOT}/scripts/verify-loop.sh" "$loop_id" 2>/dev/null; then
    echo "expected DOWN" >&2
    exit 1
  fi

  echo $$ > "${TMPDIR}/cursor-loop-${loop_id}.pid"
  bash "${ROOT}/scripts/verify-loop.sh" "$loop_id"

  rm -f "${TMPDIR}/cursor-loop-${loop_id}.pid"
  test_rmdir "$tmp"
}

test_segment_verify_loop
