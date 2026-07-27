"""Segment: validate_contracts and force_reset."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import loop_hook_lib as mod  # noqa: E402

from helpers.project_factory import SAMPLE_CONTRACT, write_contract  # noqa: E402

pytestmark = pytest.mark.segment


def test_validate_duplicate_loop_id(minimal_project: Path):
    agents = minimal_project / "docs/agents"
    agents.mkdir(parents=True, exist_ok=True)
    body = SAMPLE_CONTRACT
    for name in ("a.md", "b.md"):
        text = body.format(
            loop_id="dup-id",
            sentinel="AGENT_LOOP_TICK_DUP",
            wake_sentinel="AGENT_LOOP_WAKE_DUP",
            loop_script="tools/cursor-loop/scripts/agent-loop.sh",
            contract_doc=f"docs/agents/{name}",
        )
        (agents / name).write_text(text, encoding="utf-8")
    errors = mod.validate_all_contracts(minimal_project, mod.load_manifest(minimal_project))
    assert any("duplicate loop_id" in e for e in errors)


def test_force_reset_bindings_only(minimal_project: Path):
    mod.write_binding(minimal_project, "reset-me", {"loop_id": "x"})
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/force_reset.py"), str(minimal_project), "--bindings", "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(proc.stdout)
    assert "reset-me" in data["bindings"]
    assert not mod.binding_path(minimal_project, "reset-me").is_file()
