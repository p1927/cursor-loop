#!/usr/bin/env bash
# Segment: worktree_lib + instance_worktree CLI
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPTS="${ROOT}/scripts"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

export PYTHONPATH="${SCRIPTS}:${PYTHONPATH:-}"

python3 - <<'PY'
import worktree_lib as wt

assert wt.sanitize_item_id("relay-123 foo") == "relay-123-foo"
assert wt.branch_name("worker-relay", "relay-1") == "loop/worker-relay/relay-1"
assert wt.worktree_rel_path("worker-relay") == ".worktrees/worker-relay"
print("OK worktree_lib helpers")
PY

# Requires git repo with .worktrees/ ignored — use Habits project root
PROJECT="$(cd "${ROOT}/../.." && pwd)"
if [[ ! -d "${PROJECT}/.git" ]]; then
  echo "SKIP worktree create (no git repo at ${PROJECT})"
  exit 0
fi

if ! git -C "$PROJECT" check-ignore -q .worktrees/ 2>/dev/null; then
  echo "FAIL: .worktrees/ must be gitignored"
  exit 1
fi

bash "${SCRIPTS}/instance_worktree.sh" status "$PROJECT" --loop-id test-loop
echo "OK worktree status (no active worktree)"

echo "OK instance worktree segment"
