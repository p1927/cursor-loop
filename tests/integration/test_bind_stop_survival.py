"""Integration: bind → stop → survival skip → revive → survival emit."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import loop_hook_lib as mod  # noqa: E402

from helpers.cleanup import cleanup_project  # noqa: E402
from helpers.hooks import invoke_hook  # noqa: E402

pytestmark = pytest.mark.integration


def test_bind_stop_survival_flow(installed_project: Path):
    project = installed_project
    cid = "integ-flow-1"
    root = str(project)

    try:
        invoke_hook(
            project,
            "loop-bind.sh",
            {
                "conversation_id": cid,
                "workspace_roots": [root],
                "prompt": "@docs/agents/test-loop.md keep working",
            },
        )
        binding = mod.read_binding(project, cid)
        assert binding is not None
        assert binding.get("stopped") is False

        invoke_hook(
            project,
            "loop-bind.sh",
            {"conversation_id": cid, "workspace_roots": [root], "prompt": "stop loop"},
        )
        binding = mod.read_binding(project, cid)
        assert binding["stopped"] is True

        _, surv_out, _ = invoke_hook(
            project,
            "loop-survival.sh",
            {"conversation_id": cid, "workspace_roots": [root]},
        )
        assert surv_out == ""

        binding["stopped"] = False
        mod.write_binding(project, cid, binding)

        _, surv_out2, _ = invoke_hook(
            project,
            "loop-survival.sh",
            {"conversation_id": cid, "workspace_roots": [root]},
        )
        assert surv_out2
        payload = json.loads(surv_out2)
        assert "followup_message" in payload
        assert "deliverable" in payload["followup_message"].lower()
    finally:
        if binding := mod.read_binding(project, cid):
            mod.release_loop_lock(project, binding.get("loop_id", ""), cid)
        cleanup_project(project)
