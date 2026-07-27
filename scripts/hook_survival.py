#!/usr/bin/env python3
"""stop hook backup — re-arm if bound, not stopped, and pidfile process is dead."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import loop_hook_lib as mod


def main() -> int:
    raw = os.environ.get("CURSOR_LOOP_INPUT", "")
    if not raw:
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return 0

    conversation_id = payload.get("conversation_id") or ""
    if not conversation_id:
        return 0

    root = mod.workspace_root(payload)
    if root is None:
        return 0

    binding = mod.read_binding(root, conversation_id)
    if not binding or binding.get("stopped") or binding.get("bind_blocked"):
        return 0

    loop_id = binding.get("loop_id") or ""
    contract_doc = binding.get("contract_doc") or ""
    if not loop_id or not contract_doc:
        return 0

    lock = mod.read_loop_lock(root, loop_id)
    if lock and lock.get("conversation_id") not in (None, conversation_id):
        return 0

    pidfile = (
        Path(binding["pidfile"])
        if binding.get("pidfile")
        else mod.resolve_pidfile_path(loop_id)
    )

    if mod.is_loop_process_alive(pidfile):
        return 0

    turns = int(binding.get("survival_turns") or 0) + 1
    binding["survival_turns"] = turns
    mod.write_binding(root, conversation_id, binding)

    msg = (
        f"Loop {loop_id} is DOWN. Re-read {contract_doc}, "
        "execute Arming + Ritual + Loop survival. Do not ask user."
    )
    if turns >= mod.SURVIVAL_TURN_WARN:
        msg += (
            f" WARNING: stop-hook recovery turn {turns}/{mod.SURVIVAL_TURN_LIMIT} — "
            "after limit, paste @contract again or run force-reset.sh --all."
        )
    print(json.dumps({"followup_message": msg}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
