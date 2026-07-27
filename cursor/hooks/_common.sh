#!/usr/bin/env bash
# Shared bootstrap for cursor-loop Cursor hooks.
set -euo pipefail

cursor_loop_read_input() {
  CURSOR_LOOP_INPUT="$(cat)"
  export CURSOR_LOOP_INPUT
}

cursor_loop_scripts_dir() {
  python3 - <<'PY'
import json
import os
import sys
from pathlib import Path

raw = os.environ.get("CURSOR_LOOP_INPUT", "")
if not raw:
    sys.exit(1)
try:
    payload = json.loads(raw)
except json.JSONDecodeError:
    sys.exit(1)

for wr in payload.get("workspace_roots") or []:
    root = Path(wr)
    manifest_path = root / ".cursor" / "cursor-loop.json"
    if not manifest_path.is_file():
        continue
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        continue
    package_root = manifest.get("package_root")
    if not package_root:
        continue
    scripts = root / package_root / "scripts"
    if (scripts / "loop_hook_lib.py").is_file():
        print(scripts)
        sys.exit(0)

sys.exit(1)
PY
}

cursor_loop_run_hook() {
  local hook_py="$1"
  cursor_loop_read_input
  local scripts_dir
  if ! scripts_dir="$(cursor_loop_scripts_dir)"; then
    exit 0
  fi
  PYTHONPATH="${scripts_dir}" exec python3 "${scripts_dir}/${hook_py}"
}
