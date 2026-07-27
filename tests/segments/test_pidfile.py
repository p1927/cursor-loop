"""Segment: pidfile resolution."""
from __future__ import annotations

import sys

import pytest

ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import loop_hook_lib as mod  # noqa: E402

pytestmark = pytest.mark.segment


def test_resolve_pidfile_path():
    path = mod.resolve_pidfile_path("demo-task", {"pidfile": "cursor-loop-demo-task.pid"})
    assert path.name == "cursor-loop-demo-task.pid"
    default = mod.resolve_pidfile_path("demo-task")
    assert default.name == "cursor-loop-demo-task.pid"
