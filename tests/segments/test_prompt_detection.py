"""Segment: prompt detection (stop / keep working)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import loop_hook_lib as mod  # noqa: E402

pytestmark = pytest.mark.segment


def test_is_stop_request():
    assert mod.is_stop_request("please stop loop now")
    assert mod.is_stop_request("stop working")
    assert not mod.is_stop_request("keep working")


def test_is_keep_working_request():
    assert mod.is_keep_working_request("keep working")
    assert not mod.is_keep_working_request("stop loop")
