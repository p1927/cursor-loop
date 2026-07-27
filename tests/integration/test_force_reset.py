"""Integration: force-reset roundtrip clears bindings and locks."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import loop_hook_lib as mod  # noqa: E402

from helpers.cleanup import cleanup_project  # noqa: E402
from helpers.hooks import invoke_hook  # noqa: E402

pytestmark = pytest.mark.integration


def test_force_reset_all_clears_state(installed_project: Path):
    project = installed_project
    cid = "integ-reset-1"
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
        assert mod.read_binding(project, cid) is not None

        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/force_reset.py"),
                str(project),
                "--all",
                "--yes",
                "--json",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(proc.stdout)
        assert cid in data.get("bindings", []) or not mod.binding_path(project, cid).is_file()
        assert not mod.binding_path(project, cid).is_file()
    finally:
        cleanup_project(project)
