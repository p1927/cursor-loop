#!/usr/bin/env bash
# Phase 5 helper — detect code changes under pwa/ and server/.
# Exit 0 = no changes, 1 = changes detected (prints stat).
set -euo pipefail

ROOT="${1:-.}"
ROOT="$(cd "$ROOT" && pwd)"

changed=0
if ! git -C "$ROOT" diff --quiet HEAD -- pwa/ server/ 2>/dev/null; then
  changed=1
fi
if ! git -C "$ROOT" diff --quiet --cached -- pwa/ server/ 2>/dev/null; then
  changed=1
fi

if [[ "$changed" -eq 1 ]]; then
  echo "CODE_CHANGED=yes"
  git -C "$ROOT" diff --stat HEAD -- pwa/ server/ 2>/dev/null || true
  git -C "$ROOT" diff --stat --cached -- pwa/ server/ 2>/dev/null || true
  exit 1
fi

echo "CODE_CHANGED=no"
exit 0
