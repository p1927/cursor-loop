#!/usr/bin/env python3
"""Patch CHECKPOINT fields in window instance STATE.md files."""
from __future__ import annotations

import re


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


def update_checkpoint_fields(state_text: str, updates: dict[str, str]) -> str:
    """Update or append CHECKPOINT table rows."""
    if not updates or "## CHECKPOINT" not in state_text:
        return state_text

    lines = state_text.splitlines()
    out: list[str] = []
    in_checkpoint = False
    seen: set[str] = set()
    row_re = re.compile(r"^\|\s*`?([^|`]+)`?\s*\|")

    for line in lines:
        if line.strip() == "## CHECKPOINT":
            in_checkpoint = True
            out.append(line)
            continue
        if in_checkpoint and line.strip().startswith("## "):
            for key, val in updates.items():
                if key not in seen:
                    out.append(f"| {key} | `{val}` |")
            in_checkpoint = False
            out.append(line)
            continue
        if in_checkpoint and "|" in line:
            m = row_re.match(line.strip())
            if m:
                key = m.group(1).strip()
                if key.lower() in ("field", "-------"):
                    out.append(line)
                    continue
                if key in updates:
                    out.append(f"| {key} | `{updates[key]}` |")
                    seen.add(key)
                    continue
                seen.add(key)
        out.append(line)

    if in_checkpoint:
        for key, val in updates.items():
            if key not in seen:
                out.append(f"| {key} | `{val}` |")

    return "\n".join(out) + ("\n" if state_text.endswith("\n") else "")
