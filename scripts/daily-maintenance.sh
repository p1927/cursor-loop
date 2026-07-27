#!/usr/bin/env bash
# Daily maintenance: prune stale bindings, report loop status, validate contracts.
set -euo pipefail

TARGET="${1:-.}"
TARGET="$(cd "$TARGET" && pwd)"
PKG="$(python3 -c "import json; from pathlib import Path; m=json.loads(Path('${TARGET}/.cursor/cursor-loop.json').read_text()); print(m['package_root'])")"

echo "=== cursor-loop daily maintenance — ${TARGET} ==="
python3 "${TARGET}/${PKG}/scripts/cleanup_bindings.py" "${TARGET}"
bash "${TARGET}/${PKG}/scripts/loop-status.sh"
python3 "${TARGET}/${PKG}/scripts/validate_contracts.py" "${TARGET}"
