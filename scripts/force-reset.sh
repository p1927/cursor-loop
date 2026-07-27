#!/usr/bin/env bash
# Force-clear cursor-loop state after extreme events (stuck loops, duplicate chats, corrupt bindings).
#
# Usage:
#   bash force-reset.sh [project_root] [--all]
#   bash force-reset.sh . --loop-id worker-relay --all
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "${SCRIPT_DIR}/force_reset.py" "$@"
