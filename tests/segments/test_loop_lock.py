"""Segment: loop_id lock (one chat per loop)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import loop_hook_lib as mod  # noqa: E402

pytestmark = pytest.mark.segment


def test_loop_lock_rejects_second_chat(minimal_project: Path):
    ok, _ = mod.acquire_loop_lock(minimal_project, "demo", "chat-a", "docs/agents/demo.md")
    assert ok
    ok2, err = mod.acquire_loop_lock(minimal_project, "demo", "chat-b", "docs/agents/demo.md")
    assert not ok2
    assert err and "another chat" in err
    mod.release_loop_lock(minimal_project, "demo", "chat-a")
    ok3, _ = mod.acquire_loop_lock(minimal_project, "demo", "chat-b", "docs/agents/demo.md")
    assert ok3
    mod.release_loop_lock(minimal_project, "demo", "chat-b")
