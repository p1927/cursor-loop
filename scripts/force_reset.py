#!/usr/bin/env python3
"""Nuclear cleanup for broken loop state (extreme events)."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import loop_hook_lib as mod


def _clear_bindings(root: Path, loop_id: str | None) -> list[str]:
    bindings_dir = root / ".cursor" / "loop-bindings"
    if not bindings_dir.is_dir():
        return []
    removed: list[str] = []
    for path in bindings_dir.glob("*.json"):
        if path.name.startswith("."):
            continue
        if loop_id:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                data = {}
            if data.get("loop_id") != loop_id:
                continue
        path.unlink(missing_ok=True)
        removed.append(path.stem)
    return removed


def _clear_locks(root: Path, loop_id: str | None) -> list[str]:
    locks_dir = root / ".cursor" / "loop-bindings" / "locks"
    if not locks_dir.is_dir():
        return []
    removed: list[str] = []
    for path in locks_dir.glob("*.json"):
        if loop_id and path.stem != loop_id:
            continue
        path.unlink(missing_ok=True)
        removed.append(path.stem)
    return removed


def _clear_pidfiles(loop_id: str | None) -> list[str]:
    tmp = Path(os.environ.get("TMPDIR") or "/tmp")
    removed: list[str] = []
    pattern = f"cursor-loop-{loop_id}.pid" if loop_id else "cursor-loop-*.pid"
    for path in tmp.glob(pattern):
        if loop_id:
            mod.kill_loop_process(path)
        else:
            mod.kill_loop_process(path)
        path.unlink(missing_ok=True)
        removed.append(path.name)
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Force-clear cursor-loop state (loops, bindings, locks)."
    )
    parser.add_argument("project", nargs="?", default=".", help="Project root")
    parser.add_argument("--loop-id", help="Only reset this loop_id")
    parser.add_argument("--kill", action="store_true", help="Kill loop processes + pidfiles")
    parser.add_argument("--bindings", action="store_true", help="Remove conversation bindings")
    parser.add_argument("--locks", action="store_true", help="Remove loop_id locks")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Kill processes, clear pidfiles, bindings, locks (default if no flags)",
    )
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    root = Path(args.project).resolve()
    loop_id = args.loop_id
    do_all = args.all or not (args.kill or args.bindings or args.locks)

    result: dict[str, list[str]] = {
        "pidfiles": [],
        "bindings": [],
        "locks": [],
    }

    if do_all or args.kill:
        result["pidfiles"] = _clear_pidfiles(loop_id)
    if do_all or args.bindings:
        result["bindings"] = _clear_bindings(root, loop_id)
    if do_all or args.locks:
        result["locks"] = _clear_locks(root, loop_id)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"force-reset complete — {root}")
        for key, items in result.items():
            if items:
                print(f"  {key}: {', '.join(items)}")
            else:
                print(f"  {key}: (none)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
