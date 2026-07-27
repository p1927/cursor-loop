#!/usr/bin/env bash
# Thin wrapper for checkpoint-loop.py
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "${SCRIPT_DIR}/checkpoint-loop.py" "$@"
