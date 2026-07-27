#!/usr/bin/env bash
# Stop hung cursor-loop test runners and legacy persistent loops.
set -euo pipefail

pkill -f "tools/cursor-loop/tests/run-all.sh" 2>/dev/null || true
pkill -f "tests/run-all.sh" 2>/dev/null || true
pkill -f "pytest.*cursor-loop" 2>/dev/null || true
pkill -f "tools/cursor-loop/scripts/agent-loop.sh" 2>/dev/null || true

if pgrep -fl "run-all.sh|pytest.*cursor-loop" >/dev/null 2>&1; then
  echo "stop-tests: some test processes may still be running:"
  pgrep -fl "run-all.sh|pytest.*cursor-loop" || true
  exit 1
fi

echo "stop-tests: all cursor-loop test suites stopped"
