#!/usr/bin/env python3
"""Update loop binding checkpoint fields (product work / recovery metrics)."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import loop_hook_lib as mod

RECOVERY_ESCALATE = 3


def run_ritual_gate(root: Path, binding: dict) -> bool:
    loop_id = binding.get("loop_id") or ""
    state_file = binding.get("state_file") or ""
    if not loop_id or not state_file:
        return True
    scripts = root / mod.load_manifest(root)["package_root"] / "scripts"
    gate = scripts / "validate_ritual_gate.py"
    if not gate.is_file():
        return True
    r = subprocess.run(
        [
            "python3",
            str(gate),
            "--project",
            str(root),
            "--loop-id",
            loop_id,
            "--state-file",
            state_file,
            "--mode",
            "checkpoint",
        ],
        cwd=root,
    )
    return r.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Record cursor-loop checkpoint in binding")
    parser.add_argument("project", nargs="?", default=".", help="Project root")
    parser.add_argument("--conversation-id", required=True)
    parser.add_argument(
        "--product",
        action="store_true",
        help="Mark product deliverable completed this wake",
    )
    parser.add_argument("--evidence", default="", help="Item id or path (required with --product)")
    parser.add_argument(
        "--blocker",
        default="",
        help="Document blocker reason (alternative to --product)",
    )
    parser.add_argument(
        "--infra-only",
        action="store_true",
        help="Increment recovery_turns (infra-only turn)",
    )
    parser.add_argument("--reset-recovery", action="store_true", help="Clear recovery_turns counter")
    args = parser.parse_args()

    root = Path(args.project).resolve()
    binding = mod.read_binding(root, args.conversation_id)
    if not binding:
        print(f"CHECKPOINT_ERROR no binding for conversation {args.conversation_id}", file=sys.stderr)
        return 1

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    if args.product:
        if not args.evidence.strip():
            print("CHECKPOINT_ERROR --product requires --evidence", file=sys.stderr)
            return 1
        if not run_ritual_gate(root, binding):
            print(
                "CHECKPOINT_ERROR ritual gate failed — complete phases 1→8 before --product",
                file=sys.stderr,
            )
            return 1
        binding["last_product_wake"] = now
        binding["last_product_evidence"] = args.evidence.strip()
        binding["recovery_turns"] = 0
        binding["survival_turns"] = 0
        print(f"CHECKPOINT_PRODUCT loop_id={binding.get('loop_id')} evidence={args.evidence}")
    elif args.blocker.strip():
        binding["last_blocker"] = args.blocker.strip()
        binding["last_blocker_at"] = now
        binding["recovery_turns"] = 0
        print(f"CHECKPOINT_BLOCKER loop_id={binding.get('loop_id')}")
    elif args.infra_only:
        turns = int(binding.get("recovery_turns") or 0) + 1
        binding["recovery_turns"] = turns
        print(f"CHECKPOINT_INFRA_ONLY loop_id={binding.get('loop_id')} recovery_turns={turns}")
        if turns >= RECOVERY_ESCALATE:
            print(
                "CHECKPOINT_WARN infra-only recovery streak — ship Ritual deliverable before re-arm",
                file=sys.stderr,
            )
    elif args.reset_recovery:
        binding["recovery_turns"] = 0
        print(f"CHECKPOINT_RESET loop_id={binding.get('loop_id')}")
    else:
        print("CHECKPOINT_ERROR specify --product, --blocker, --infra-only, or --reset-recovery", file=sys.stderr)
        return 1

    mod.write_binding(root, args.conversation_id, binding)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
