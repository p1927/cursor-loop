"""Integration: copy install + hook bootstrap via manifest."""
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
from helpers.project_factory import install_copy_project, write_contract  # noqa: E402

pytestmark = pytest.mark.integration


def test_copy_install_hooks_bootstrap(isolated_tmpdir: Path):
    project = isolated_tmpdir
    install_copy_project(project, package_path="vendor/cursor-loop")
    write_contract(
        project,
        loop_id="copy-loop",
        loop_script="vendor/cursor-loop/scripts/agent-loop.sh",
    )
    cid = "integ-install-1"
    root = str(project)

    try:
        manifest = json.loads((project / ".cursor/cursor-loop.json").read_text())
        assert manifest["package_root"] == "vendor/cursor-loop"
        assert (project / "vendor/cursor-loop/scripts/loop_hook_lib.py").is_file()

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
        assert binding and binding["loop_id"] == "copy-loop"
    finally:
        if binding := mod.read_binding(project, cid):
            mod.release_loop_lock(project, binding.get("loop_id", ""), cid)
        cleanup_project(project)
