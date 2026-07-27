"""Shared test cleanup — no leftover bindings, locks, or pidfiles."""
from __future__ import annotations

import os
import shutil
import signal
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import loop_hook_lib as mod  # noqa: E402


def cleanup_project(root: Path) -> None:
    """Remove all cursor-loop runtime artifacts under a project root."""
    bindings = root / ".cursor" / "loop-bindings"
    if bindings.is_dir():
        shutil.rmtree(bindings, ignore_errors=True)

    try:
        manifest = mod.load_manifest(root)
        mod.cleanup_stale_bindings(root, manifest, dry_run=False)
    except (FileNotFoundError, ValueError):
        pass

    cleanup_pidfiles_glob()


def cleanup_pidfiles_glob(loop_id: str | None = None) -> None:
    """Kill and remove cursor-loop pidfiles in TMPDIR."""
    tmp = Path(os.environ.get("TMPDIR", "/tmp"))
    pattern = f"cursor-loop-{loop_id}.pid" if loop_id else "cursor-loop-*.pid"
    for pidfile in tmp.glob(pattern):
        mod.kill_loop_process(pidfile)
        pidfile.unlink(missing_ok=True)


def kill_pidfile(pidfile: Path) -> None:
    if not pidfile.is_file():
        return
    try:
        pid = int(pidfile.read_text(encoding="utf-8").strip())
        os.kill(pid, signal.SIGTERM)
    except (ValueError, ProcessLookupError, PermissionError, OSError):
        pass


def cleanup_temp_dir(path: Path) -> None:
    if path.is_dir():
        cleanup_project(path)
        cleanup_pidfiles_glob()
        shutil.rmtree(path, ignore_errors=True)
