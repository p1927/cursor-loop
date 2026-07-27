#!/usr/bin/env python3
"""Validate ritual phase line before arm, checkpoint, or transition."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import ritual_phase as rp


def emit_fail(loop_id: str, result: rp.GateResult) -> None:
    print(
        f"RITUAL_GATE_FAIL loop_id={loop_id} allowed_phase={result.allowed_phase} "
        f'reason="{result.reason}"',
        file=sys.stderr,
    )
    if result.fix:
        print(f"FIX: {result.fix}", file=sys.stderr)
    print(f"PHASE_LINE: {rp.phase_line_marker(result.allowed_phase)}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate window instance ritual phase gates")
    parser.add_argument("--project", default=".", help="Project root")
    parser.add_argument("--loop-id", required=True)
    parser.add_argument("--state-file", required=True)
    parser.add_argument(
        "--mode",
        choices=("arm", "checkpoint", "wake", "transition"),
        default="arm",
    )
    parser.add_argument("--from-phase", default="", help="For --mode=transition")
    parser.add_argument("--to-phase", default="", help="For --mode=transition")
    parser.add_argument("--force", action="store_true", help="Operator override (skip gate)")
    args = parser.parse_args()

    if args.force:
        print(f"RITUAL_GATE_SKIP loop_id={args.loop_id} mode={args.mode} (forced)")
        return 0

    root = Path(args.project).resolve()
    state_path = root / args.state_file
    if not state_path.is_file():
        print(f"RITUAL_GATE_FAIL loop_id={args.loop_id} reason=missing state file", file=sys.stderr)
        return 1

    state_text = state_path.read_text(encoding="utf-8")
    checkpoint = rp.parse_checkpoint_table(state_text)

    if args.mode == "transition":
        if not args.from_phase or not args.to_phase:
            print("RITUAL_GATE_FAIL reason=--from-phase and --to-phase required", file=sys.stderr)
            return 1
        ok, msg = rp.validate_transition(args.from_phase, args.to_phase)
        if not ok:
            print(
                f"RITUAL_GATE_FAIL loop_id={args.loop_id} "
                f"allowed_phase={rp.next_phase(args.from_phase) or args.from_phase} "
                f'reason="{msg}"',
                file=sys.stderr,
            )
            print(f"PHASE_LINE: {rp.phase_line_marker(args.from_phase)}", file=sys.stderr)
            return 1
        print(f"RITUAL_GATE_OK loop_id={args.loop_id} mode=transition")
        return 0

    if args.mode == "wake":
        allowed = rp.allowed_phase_on_wake(checkpoint.get("phase", "1-wake"))
        print(f"RITUAL_GATE_OK loop_id={args.loop_id} allowed_phase={allowed} mode=wake")
        return 0

    result = rp.required_phase_before_arm(
        checkpoint,
        state_text,
        project_root=root,
        mode="checkpoint" if args.mode == "checkpoint" else "arm",
    )
    if not result.ok:
        emit_fail(args.loop_id, result)
        return 1

    print(f"RITUAL_GATE_OK loop_id={args.loop_id} mode={args.mode} phase={checkpoint.get('phase', '?')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
