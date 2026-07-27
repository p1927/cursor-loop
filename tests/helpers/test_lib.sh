#!/usr/bin/env bash
# Shared bash test helpers — always cleanup temp dirs and pidfiles.
set -euo pipefail

test_mkdir() {
  mktemp -d "${TMPDIR:-/tmp}/cursor-loop-test.XXXXXX"
}

test_rmdir() {
  local dir="$1"
  if [[ -n "${TMPDIR:-}" && -d "${TMPDIR}" ]]; then
    rm -f "${TMPDIR}"/cursor-loop-*.pid 2>/dev/null || true
  fi
  rm -rf "$dir"
}

test_invoke_hook() {
  local project="$1" hook="$2" payload="$3"
  echo "$payload" | bash "${project}/.cursor/hooks/${hook}"
}

test_cleanup_project() {
  local project="$1"
  local pkg_root
  pkg_root="$(python3 -c "import json; print(json.load(open('${project}/.cursor/cursor-loop.json'))['package_root']")" 2>/dev/null || echo "vendor/cursor-loop"
  python3 "${project}/${pkg_root}/scripts/force_reset.py" "$project" --all --yes 2>/dev/null || true
  rm -rf "${project}/.cursor/loop-bindings" 2>/dev/null || true
}
