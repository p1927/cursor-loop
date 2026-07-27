"""Segment: merge_hooks.py"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

pytestmark = pytest.mark.segment


def test_merge_hooks_idempotent(isolated_tmpdir: Path):
    target = isolated_tmpdir / ".cursor/hooks.json"
    target.parent.mkdir(parents=True)
    target.write_text('{"version":1,"hooks":{"stop":[]}}\n', encoding="utf-8")
    snippet = ROOT / "cursor/hooks/hooks.json.snippet"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/merge_hooks.py"), str(target), str(snippet)],
        check=True,
    )
    data = json.loads(target.read_text())
    assert any("loop-bind.sh" in e.get("command", "") for e in data["hooks"]["beforeSubmitPrompt"])
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/merge_hooks.py"), str(target), str(snippet)],
        check=True,
    )
    data2 = json.loads(target.read_text())
    assert len(data2["hooks"]["beforeSubmitPrompt"]) == len(data["hooks"]["beforeSubmitPrompt"])
