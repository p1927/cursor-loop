#!/usr/bin/env python3
"""Add missing CHECKPOINT fields from _template/STATE.md to live instance STATE files."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import loop_hook_lib as mod


def parse_checkpoint_fields(state_text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    if "## CHECKPOINT" not in state_text:
        return out
    section = state_text.split("## CHECKPOINT", 1)[1]
    if "\n## " in section:
        section = section.split("\n## ", 1)[0]
    for line in section.splitlines():
        if "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 3 and parts[1] and parts[2]:
            key = parts[1].strip("`")
            val = parts[2].strip("`")
            if key.lower() not in ("field", "-------"):
                out[key] = val
    return out


def parse_template_defaults(template_text: str) -> dict[str, str]:
    return parse_checkpoint_fields(template_text)


def insert_checkpoint_rows(state_text: str, missing: dict[str, str]) -> str:
    if not missing or "## CHECKPOINT" not in state_text:
        return state_text
    lines = state_text.splitlines()
    out: list[str] = []
    in_checkpoint = False
    inserted = False
    for line in lines:
        out.append(line)
        if line.strip() == "## CHECKPOINT":
            in_checkpoint = True
            continue
        if in_checkpoint and not inserted and line.strip().startswith("## "):
            for key, val in missing.items():
                out.insert(-1, f"| {key} | `{val}` |")
            inserted = True
            in_checkpoint = False
    if in_checkpoint and not inserted:
        for key, val in missing.items():
            out.append(f"| {key} | `{val}` |")
    return "\n".join(out) + ("\n" if state_text.endswith("\n") else "")


def load_instances(root: Path) -> list[dict]:
    manifest = mod.load_manifest(root)
    data = mod.load_instances_manifest(root, manifest)
    return data.get("instances") or []


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate live STATE CHECKPOINT fields from template")
    parser.add_argument("project", nargs="?", default=".")
    parser.add_argument("--apply", action="store_true", help="Write changes (default dry-run)")
    parser.add_argument("--loop-id", default="")
    args = parser.parse_args()

    root = Path(args.project).resolve()
    manifest = mod.load_manifest(root)
    wi_root = root / manifest["package_root"] / "window-instances"
    template_path = wi_root / "_template" / "STATE.md"
    if not template_path.is_file():
        print(f"migrate: missing template {template_path}", file=sys.stderr)
        return 1

    defaults = parse_template_defaults(template_path.read_text(encoding="utf-8"))
    instances = load_instances(root)
    if args.loop_id:
        instances = [i for i in instances if i.get("loop_id") == args.loop_id]

    changed = 0
    for entry in instances:
        loop_id = entry.get("loop_id", "")
        state_file = root / entry.get("state_file", "")
        if not state_file.is_file():
            print(f"SKIP {loop_id}: missing {state_file}")
            continue
        text = state_file.read_text(encoding="utf-8")
        current = parse_checkpoint_fields(text)
        missing = {k: v for k, v in defaults.items() if k not in current}
        if not missing:
            print(f"OK {loop_id}: CHECKPOINT complete")
            continue
        print(f"MIGRATE {loop_id}: add {', '.join(missing.keys())}")
        if args.apply:
            state_file.write_text(insert_checkpoint_rows(text, missing), encoding="utf-8")
            changed += 1

    if args.apply:
        print(f"Applied migrations to {changed} instance(s)")
    else:
        print("Dry-run — pass --apply to write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
