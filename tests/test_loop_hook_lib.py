"""Tests for loop_hook_lib."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import loop_hook_lib as mod  # noqa: E402

SAMPLE_CONTRACT = """\
# Task

## Loop config

| Field | Value |
|-------|-------|
| loop_id | `demo-task` |
| sentinel | `AGENT_LOOP_TICK_DEMO` |
| interval_sec | `60` |
| loop_script | `tools/cursor-loop/scripts/agent-loop.sh` |
| contract_doc | `docs/agents/demo-task.md` |

## Task

Do work.
"""


def test_parse_loop_config_scoped_to_section(tmp_path: Path) -> None:
    text = "| loop_id | `wrong` |\n" + SAMPLE_CONTRACT
    cfg = mod.parse_loop_config(text)
    assert cfg["loop_id"] == "demo-task"


def test_is_stop_and_keep_working() -> None:
    assert mod.is_stop_request("please stop loop now")
    assert mod.is_stop_request("stop working")
    assert not mod.is_stop_request("keep working")
    assert mod.is_keep_working_request("keep working")


def test_find_contract_paths_from_at_mention(tmp_path: Path) -> None:
    doc = tmp_path / "docs/agents/demo-task.md"
    doc.parent.mkdir(parents=True)
    doc.write_text(SAMPLE_CONTRACT, encoding="utf-8")
    manifest = {"contracts_dir": "docs/agents", "contract_globs": []}
    paths = mod.find_contract_paths("@docs/agents/demo-task.md keep working", tmp_path, manifest)
    assert paths == ["docs/agents/demo-task.md"]


def test_resolve_pidfile_path() -> None:
    path = mod.resolve_pidfile_path("demo-task", {"pidfile": "cursor-loop-demo-task.pid"})
    assert path.name == "cursor-loop-demo-task.pid"
    default = mod.resolve_pidfile_path("demo-task")
    assert default.name == "cursor-loop-demo-task.pid"


def test_load_manifest_requires_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        mod.load_manifest(tmp_path)


def test_build_binding(tmp_path: Path) -> None:
    pkg = tmp_path / "tools/cursor-loop/scripts"
    pkg.mkdir(parents=True)
    (pkg / "agent-loop.sh").write_text("#!/bin/bash\n", encoding="utf-8")
    manifest_path = tmp_path / ".cursor/cursor-loop.json"
    manifest_path.parent.mkdir(parents=True)
    manifest_path.write_text(
        json.dumps({"package_root": "tools/cursor-loop", "contracts_dir": "docs/agents"}),
        encoding="utf-8",
    )
    cfg = mod.parse_loop_config(SAMPLE_CONTRACT)
    binding = mod.build_binding(tmp_path, mod.load_manifest(tmp_path), "docs/agents/demo-task.md", cfg)
    assert binding["loop_id"] == "demo-task"
    assert binding["stopped"] is False
    assert "pidfile" in binding
