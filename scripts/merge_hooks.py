#!/usr/bin/env python3
"""Merge cursor-loop hook entries into .cursor/hooks.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def merge_hooks(target: Path, snippet: Path) -> None:
    snippet_data = json.loads(snippet.read_text(encoding="utf-8"))
    if target.is_file():
        data = json.loads(target.read_text(encoding="utf-8"))
    else:
        data = {"version": 1, "hooks": {}}

    data.setdefault("version", snippet_data.get("version", 1))
    data.setdefault("hooks", {})

    for hook_name, entries in snippet_data.get("hooks", {}).items():
        existing = data["hooks"].setdefault(hook_name, [])
        commands = {entry.get("command") for entry in existing}
        for entry in entries:
            cmd = entry.get("command")
            if cmd in commands:
                for idx, current in enumerate(existing):
                    if current.get("command") == cmd:
                        existing[idx] = {**current, **entry}
                        break
            else:
                existing.append(entry)
                commands.add(cmd)

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <hooks.json> <hooks.json.snippet>", file=sys.stderr)
        return 1
    merge_hooks(Path(sys.argv[1]), Path(sys.argv[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
