"""Integration: one loop_id per chat — second bind is blocked."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import loop_hook_lib as mod  # noqa: E402

from helpers.cleanup import cleanup_project  # noqa: E402
from helpers.hooks import invoke_hook  # noqa: E402

pytestmark = pytest.mark.integration


def test_second_chat_blocked_for_same_loop_id(installed_project: Path):
    project = installed_project
    root = str(project)
    chat_a = "integ-lock-a"
    chat_b = "integ-lock-b"

    try:
        invoke_hook(
            project,
            "loop-bind.sh",
            {
                "conversation_id": chat_a,
                "workspace_roots": [root],
                "prompt": "@docs/agents/test-loop.md keep working",
            },
        )
        binding_a = mod.read_binding(project, chat_a)
        assert binding_a and not binding_a.get("bind_blocked")

        invoke_hook(
            project,
            "loop-bind.sh",
            {
                "conversation_id": chat_b,
                "workspace_roots": [root],
                "prompt": "@docs/agents/test-loop.md keep working",
            },
        )
        binding_b = mod.read_binding(project, chat_b)
        assert binding_b
        assert binding_b.get("bind_blocked") is True
        assert binding_b.get("stopped") is True
    finally:
        for cid in (chat_a, chat_b):
            if binding := mod.read_binding(project, cid):
                mod.release_loop_lock(project, binding.get("loop_id", ""), cid)
        cleanup_project(project)
