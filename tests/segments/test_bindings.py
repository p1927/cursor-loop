"""Segment: bindings read/write/TTL."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import loop_hook_lib as mod  # noqa: E402

from helpers.project_factory import SAMPLE_CONTRACT, write_contract  # noqa: E402

pytestmark = pytest.mark.segment


def test_write_binding_sets_updated_at(minimal_project: Path):
    mod.write_binding(minimal_project, "conv-1", {"loop_id": "x"})
    data = json.loads(mod.binding_path(minimal_project, "conv-1").read_text(encoding="utf-8"))
    assert "updated_at" in data


def test_build_binding(minimal_project: Path):
    write_contract(
        minimal_project,
        loop_id="test-loop",
        loop_script="tools/cursor-loop/scripts/agent-loop.sh",
    )
    cfg = mod.parse_loop_config(
        (minimal_project / "docs/agents/test-loop.md").read_text(encoding="utf-8")
    )
    binding = mod.build_binding(
        minimal_project,
        mod.load_manifest(minimal_project),
        "docs/agents/test-loop.md",
        cfg,
    )
    assert binding["loop_id"] == "test-loop"
    assert binding["stopped"] is False
    assert "pidfile" in binding


def test_cleanup_stale_bindings(minimal_project: Path):
    manifest = mod.load_manifest(minimal_project)
    manifest_path = minimal_project / ".cursor/cursor-loop.json"
    manifest_path.write_text(
        json.dumps({**manifest, "binding_ttl_days": 7}),
        encoding="utf-8",
    )
    bindings_dir = minimal_project / ".cursor" / "loop-bindings"
    bindings_dir.mkdir(parents=True, exist_ok=True)
    stale = bindings_dir / "old-chat.json"
    stale.write_text(
        json.dumps({"loop_id": "a", "updated_at": "2020-01-01T00:00:00+00:00"}),
        encoding="utf-8",
    )
    mod.write_binding(minimal_project, "new-chat", {"loop_id": "b"})
    removed = mod.cleanup_stale_bindings(minimal_project, mod.load_manifest(minimal_project))
    assert "old-chat" in removed
    assert not stale.is_file()
