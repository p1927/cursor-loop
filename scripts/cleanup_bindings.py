#!/usr/bin/env python3
"""Remove stale conversation bindings past binding_ttl_days."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import loop_hook_lib as mod


def main() -> int:
    parser = argparse.ArgumentParser(description="Prune stale .cursor/loop-bindings/")
    parser.add_argument("project", nargs="?", default=".", help="Project root")
    parser.add_argument("--dry-run", action="store_true", help="List stale bindings without deleting")
    parser.add_argument("--json", action="store_true", help="Emit JSON result")
    args = parser.parse_args()

    root = Path(args.project).resolve()
    try:
        manifest = mod.load_manifest(root)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    removed = mod.cleanup_stale_bindings(root, manifest, dry_run=args.dry_run)
    ttl = manifest.get("binding_ttl_days", 30)

    if args.json:
        print(json.dumps({"removed": removed, "ttl_days": ttl, "dry_run": args.dry_run}))
    elif removed:
        action = "Would remove" if args.dry_run else "Removed"
        print(f"{action} {len(removed)} binding(s) older than {ttl} days:")
        for cid in removed:
            print(f"  - {cid}")
    else:
        print(f"No stale bindings (ttl={ttl} days)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
