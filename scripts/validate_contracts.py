#!/usr/bin/env python3
"""Validate loop contracts: unique loop_id/sentinel, required fields, script paths."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import loop_hook_lib as mod


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate loop contract docs")
    parser.add_argument("project", nargs="?", default=".", help="Project root")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    root = Path(args.project).resolve()
    try:
        manifest = mod.load_manifest(root)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    errors = mod.validate_all_contracts(root, manifest)

    if args.json:
        print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
    elif errors:
        print("Contract validation FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
    else:
        count = len(mod.iter_contract_files(root, manifest))
        print(f"OK — {count} contract(s) validated")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
