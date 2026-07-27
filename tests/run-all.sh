#!/usr/bin/env bash
# Run full test pyramid: segments → integration → e2e (each tier cleans up after itself).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export TMPDIR="${TMPDIR:-/tmp}/cursor-loop-run-$$"
mkdir -p "$TMPDIR"
trap 'rm -rf "$TMPDIR"' EXIT

echo "=== Tier 1: segment tests (pytest) ==="
python3 -m pytest tests/segments -q -m segment

echo "=== Tier 1: segment tests (bash) ==="
for script in tests/segments/test_*.sh; do
  bash "$script"
done

echo "=== Tier 2: integration tests ==="
python3 -m pytest tests/integration -q -m integration

echo "=== Tier 3: end-to-end tests ==="
bash tests/e2e/test_full_lifecycle.sh

echo "PASS run-all"
