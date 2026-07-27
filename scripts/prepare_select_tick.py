#!/usr/bin/env python3
"""Phase 3 prep — detect worktree requirement and suggest create command."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import ritual_phase as rp
import worktree_lib as wt

LOOP_ARCHETYPE_FALLBACK: dict[str, str] = {
    "worker-relay": "engineer",
    "ux-relay": "designer",
    "code-health": "engineer",
    "po-relay": "product",
}


def load_archetype(project_root: Path, loop_id: str) -> str:
    manifest_path = project_root / "docs/window-instances/instances.manifest.json"
    if manifest_path.is_file():
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            for entry in data.get("instances") or []:
                if entry.get("loop_id") == loop_id:
                    return str(entry.get("archetype") or "")
        except (json.JSONDecodeError, OSError):
            pass
    return LOOP_ARCHETYPE_FALLBACK.get(loop_id, "")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare Phase 3 select tick (worktree)")
    parser.add_argument("project", nargs="?", default=".", help="Project root")
    parser.add_argument("--state-file", required=True, help="Relative path to STATE.md")
    parser.add_argument("--loop-id", default="", help="Window loop_id")
    args = parser.parse_args()

    root = Path(args.project).resolve()
    state_path = root / args.state_file
    if not state_path.is_file():
        print(f"PREPARE_SELECT_ERROR missing state file: {args.state_file}", file=sys.stderr)
        return 1

    loop_id = args.loop_id
    if not loop_id:
        loop_id = state_path.parent.name

    state_text = state_path.read_text(encoding="utf-8")
    checkpoint = rp.parse_checkpoint_table(state_text)
    archetype = load_archetype(root, loop_id)
    item_id = rp.parse_current_item_id(state_text, checkpoint)
    requires = rp.requires_worktree(archetype) and bool(item_id)

    disk = wt.worktree_entry(root, loop_id)
    wt_status = wt.status_worktree(root, loop_id)
    checkpoint_status = (checkpoint.get("worktree_status") or "none").strip().strip("`").lower()

    if disk:
        worktree_state = "active"
    elif checkpoint_status == "active":
        worktree_state = "missing"
    else:
        worktree_state = "none"

    pkg = "tools/cursor-loop/scripts"
    create_cmd = (
        f"bash {pkg}/instance_worktree.sh create . "
        f"--loop-id {loop_id} --item-id {item_id} --state-file {args.state_file}"
    )

    print("PREPARE_SELECT_BEGIN")
    print(f"archetype={archetype or 'unknown'}")
    print(f"current_item_id={item_id or 'none'}")
    print(f"requires_worktree={'yes' if requires else 'no'}")
    print(f"worktree_status={worktree_state}")
    if disk:
        print(f"worktree_path={disk.get('path', '')}")
        print(f"worktree_branch={disk.get('branch', '')}")
    elif wt_status.get("status") == "active":
        print(f"worktree_path={wt_status.get('path', '')}")
        print(f"worktree_branch={wt_status.get('branch', '')}")

    if requires and worktree_state != "active":
        print(f"suggested_command={create_cmd}")
        print("PREPARE_SELECT_ACTION=create_worktree_before_phase_4")
    elif requires and worktree_state == "active":
        print("PREPARE_SELECT_ACTION=use_worktree_path_for_phases_4_7")
        print(f"suggested_workdir={wt_status.get('path', checkpoint.get('worktree_path', ''))}")
    else:
        print("PREPARE_SELECT_ACTION=skip_worktree")
        print("suggested_command=")

    print("PREPARE_SELECT_END")
    return 0 if not requires or worktree_state == "active" else 1


if __name__ == "__main__":
    raise SystemExit(main())
