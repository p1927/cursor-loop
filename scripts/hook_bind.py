#!/usr/bin/env python3
"""beforeSubmitPrompt — bind conversation to loop contract; honor stop loop."""
from __future__ import annotations

import json
import os
import sys

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
    prompt = payload.get("prompt") or ""
    if not conversation_id:
        return 0

    root = mod.workspace_root(payload)
    if root is None:
        return 0

    try:
        manifest = mod.load_manifest(root)
    except (FileNotFoundError, ValueError):
        return 0

    if mod.is_stop_request(prompt):
        binding = mod.read_binding(root, conversation_id)
        if binding:
            binding["stopped"] = True
            mod.write_binding(root, conversation_id, binding)
        return 0

    if mod.is_keep_working_request(prompt):
        binding = mod.read_binding(root, conversation_id)
        if binding and binding.get("stopped"):
            binding["stopped"] = False
            mod.write_binding(root, conversation_id, binding)
            return 0

    for rel in mod.find_contract_paths(prompt, root, manifest):
        doc_path = root / rel
        if not doc_path.is_file():
            continue
        text = doc_path.read_text(encoding="utf-8")
        if not mod.has_loop_config(text):
            continue
        cfg = mod.parse_loop_config(text)
        loop_id = cfg.get("loop_id")
        if not loop_id:
            continue
        try:
            binding = mod.build_binding(root, manifest, rel, cfg)
        except FileNotFoundError:
            continue
        mod.write_binding(root, conversation_id, binding)
        break

    return 0


if __name__ == "__main__":
    sys.exit(main())
