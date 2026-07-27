"""Segment: contract parsing and path discovery."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import loop_hook_lib as mod  # noqa: E402

from helpers.project_factory import SAMPLE_CONTRACT, write_contract  # noqa: E402

pytestmark = pytest.mark.segment


def test_parse_loop_config_scoped_to_section():
    text = "| loop_id | `wrong` |\n" + SAMPLE_CONTRACT.format(
        loop_id="demo-task",
        sentinel="AGENT_LOOP_TICK_DEMO",
        wake_sentinel="AGENT_LOOP_WAKE_DEMO",
        loop_script="tools/cursor-loop/scripts/agent-loop.sh",
        contract_doc="docs/agents/demo-task.md",
    )
    cfg = mod.parse_loop_config(text)
    assert cfg["loop_id"] == "demo-task"


def test_find_contract_paths_from_at_mention(minimal_project: Path):
    write_contract(
        minimal_project,
        loop_id="demo-task",
        rel="docs/agents/demo-task.md",
        loop_script="tools/cursor-loop/scripts/agent-loop.sh",
    )
    manifest = mod.load_manifest(minimal_project)
    paths = mod.find_contract_paths(
        "@docs/agents/demo-task.md keep working", minimal_project, manifest
    )
    assert paths == ["docs/agents/demo-task.md"]
