#!/usr/bin/env python3
"""CLI for window instance git worktrees."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import state_checkpoint as sc
import worktree_lib as wt


def patch_state_after_create(
    project_root: Path,
    state_file: str,
    loop_id: str,
    item_id: str,
    info: dict[str, str],
) -> None:
    state_path = project_root / state_file
    if not state_path.is_file():
        return
    text = state_path.read_text(encoding="utf-8")
    updates = {
        "worktree_status": "active",
        "worktree_path": info["path"],
        "worktree_branch": info["branch"],
        "worktree_item_id": item_id,
        "current_item_id": item_id,
    }
    state_path.write_text(sc.update_checkpoint_fields(text, updates), encoding="utf-8")


def patch_state_after_remove(project_root: Path, state_file: str) -> None:
    state_path = project_root / state_file
    if not state_path.is_file():
        return
    text = state_path.read_text(encoding="utf-8")
    updates = {
        "worktree_status": "none",
        "worktree_path": "—",
        "worktree_branch": "—",
        "worktree_item_id": "—",
    }
    state_path.write_text(sc.update_checkpoint_fields(text, updates), encoding="utf-8")


def cmd_create(args: argparse.Namespace) -> int:
    if not args.item_id:
        print("WORKTREE_ERROR --item-id required for create", file=sys.stderr)
        return 1
    print("WORKTREE_BEGIN")
    try:
        info = wt.create_worktree(Path(args.project), args.loop_id, args.item_id)
    except RuntimeError as exc:
        print(f"WORKTREE_ERROR {exc}", file=sys.stderr)
        return 1
    if args.state_file:
        patch_state_after_create(
            Path(args.project), args.state_file, args.loop_id, args.item_id, info
        )
        print(f"WORKTREE_STATE_UPDATED={args.state_file}")
    print(f"WORKTREE_PATH={info['path']}")
    print(f"WORKTREE_BRANCH={info['branch']}")
    print(f"WORKTREE_REL={info['rel_path']}")
    print(f"WORKTREE_RESUMED={info.get('resumed', 'no')}")
    print("WORKTREE_END")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    info = wt.status_worktree(Path(args.project), args.loop_id)
    print("WORKTREE_BEGIN")
    for key, val in info.items():
        print(f"WORKTREE_{key.upper()}={val}")
    print("WORKTREE_END")
    return 0


def cmd_merge(args: argparse.Namespace) -> int:
    print("WORKTREE_BEGIN")
    try:
        info = wt.merge_worktree(Path(args.project), args.loop_id)
    except RuntimeError as exc:
        print(f"WORKTREE_ERROR {exc}", file=sys.stderr)
        return 1
    print(f"WORKTREE_PATH={info['path']}")
    print(f"WORKTREE_BRANCH={info['branch']}")
    print("WORKTREE_MERGED=yes")
    print("WORKTREE_END")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    wt.remove_worktree(Path(args.project), args.loop_id)
    if args.state_file:
        patch_state_after_remove(Path(args.project), args.state_file)
        print(f"WORKTREE_STATE_UPDATED={args.state_file}")
    print("WORKTREE_BEGIN")
    print("WORKTREE_REMOVED=yes")
    print("WORKTREE_END")
    return 0


def cmd_prune(args: argparse.Namespace) -> int:
    removed = wt.prune_worktrees(Path(args.project))
    print("WORKTREE_BEGIN")
    if removed:
        print(f"WORKTREE_PRUNED={','.join(removed)}")
    else:
        print("WORKTREE_PRUNED=")
    print("WORKTREE_END")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Window instance git worktree CLI")
    parser.add_argument("command", choices=("create", "status", "merge", "remove", "prune"))
    parser.add_argument("project", nargs="?", default=".")
    parser.add_argument("--loop-id", required=True)
    parser.add_argument("--item-id", default="")
    parser.add_argument("--state-file", default="", help="Patch CHECKPOINT after create/remove")
    args = parser.parse_args()

    handlers = {
        "create": cmd_create,
        "status": cmd_status,
        "merge": cmd_merge,
        "remove": cmd_remove,
        "prune": cmd_prune,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
