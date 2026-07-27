#!/usr/bin/env bash
# Install cursor-loop into a project without cloning the repo first.
#
# One-liner (copy mode, vendors package into tools/cursor-loop):
#   curl -fsSL https://raw.githubusercontent.com/p1927/cursor-loop/v0.2.0/install-remote.sh | bash -s -- .
#
# With options (passed through to install.sh):
#   curl -fsSL .../install-remote.sh | bash -s -- . --symlink --contracts-dir docs/agents
#
# Environment:
#   CURSOR_LOOP_REPO   Git URL (default: https://github.com/p1927/cursor-loop.git)
#   CURSOR_LOOP_REF    Branch or tag (default: main)
#   CURSOR_LOOP_PACKAGE_PATH  Package dir relative to project (default: tools/cursor-loop)
set -euo pipefail

REPO="${CURSOR_LOOP_REPO:-https://github.com/p1927/cursor-loop.git}"
REF="${CURSOR_LOOP_REF:-main}"
PACKAGE_PATH="${CURSOR_LOOP_PACKAGE_PATH:-tools/cursor-loop}"

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  sed -n '2,14p' "$0"
  exit 0
fi

TARGET="${1:-.}"
shift || true

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Required command not found: $1" >&2
    exit 1
  fi
}

need_cmd bash
need_cmd python3

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

fetch_with_git() {
  need_cmd git
  git clone --depth 1 --branch "$REF" "$REPO" "$TMP/cursor-loop"
}

fetch_with_curl() {
  need_cmd curl
  need_cmd tar
  local tarball
  if [[ "$REF" == v* ]]; then
    tarball="https://github.com/p1927/cursor-loop/archive/refs/tags/${REF}.tar.gz"
  else
    tarball="https://github.com/p1927/cursor-loop/archive/refs/heads/${REF}.tar.gz"
  fi
  curl -fsSL "$tarball" | tar -xz -C "$TMP"
  mv "$TMP"/cursor-loop-* "$TMP/cursor-loop"
}

if command -v git >/dev/null 2>&1; then
  fetch_with_git || fetch_with_curl
else
  fetch_with_curl
fi

INSTALL_ARGS=(--copy "--package-path" "$PACKAGE_PATH")
# Pass remaining args unless user already specified --copy/--symlink
has_mode=0
for arg in "$@"; do
  if [[ "$arg" == "--copy" || "$arg" == "--symlink" ]]; then
    has_mode=1
    break
  fi
done
if [[ "$has_mode" -eq 0 ]]; then
  set -- "${INSTALL_ARGS[@]}" "$@"
else
  set -- "$@"
fi

bash "$TMP/cursor-loop/install.sh" "$TARGET" "$@"
