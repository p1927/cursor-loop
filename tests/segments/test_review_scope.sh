#!/usr/bin/env bash
# Segment: review_scope per-window paths
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPTS="${ROOT}/scripts"
export PYTHONPATH="${SCRIPTS}:${PYTHONPATH:-}"

python3 - <<'PY'
import review_scope as rs

ch = rs.review_paths("code-health", "docs/window-instances/code-health/STATE.md")
assert "tools/cursor-loop/" in ch, ch
assert "docs/window-instances/code-health/" in ch

po = rs.review_paths("po-relay", "docs/window-instances/po-relay/STATE.md")
assert "docs/window-instances/po-relay/" in po
assert "pwa/" not in po

worker = rs.review_paths("worker-relay", "docs/window-instances/worker-relay/STATE.md")
assert worker[0] == "pwa/"
print("OK review_scope paths")
PY

# list_changed_files + fingerprint in temp git repo
GIT_TMP="$(mktemp -d)"
trap 'rm -rf "$GIT_TMP"' EXIT
(
  cd "$GIT_TMP"
  git init -q
  git config user.email test@test.com
  git config user.name Test
  mkdir -p pwa
  echo "v1" > pwa/a.ts
  git add .
  git commit -q -m init
  echo "v2" >> pwa/a.ts
)
python3 - <<PY
import review_scope as rs
from pathlib import Path

root = Path("${GIT_TMP}")
files = rs.list_changed_files(root, ["pwa/"])
assert files == ["pwa/a.ts"], files
fp = rs.files_fingerprint(files)
assert len(fp) == 16, fp
ok, live, live_fp = rs.manifest_matches_git(root, ["pwa/"], "pwa/a.ts", fp)
assert ok and live_fp == fp
ok2, _, _ = rs.manifest_matches_git(root, ["pwa/"], "pwa/a.ts", "stale")
assert not ok2
print("OK list_changed_files + fingerprint")
PY

echo "OK review scope segment"
