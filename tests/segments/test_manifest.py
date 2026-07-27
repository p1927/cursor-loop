"""Segment: manifest loading."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import loop_hook_lib as mod  # noqa: E402

pytestmark = pytest.mark.segment


def test_load_manifest_requires_file(isolated_tmpdir: Path):
    with pytest.raises(FileNotFoundError):
        mod.load_manifest(isolated_tmpdir)


def test_load_manifest_defaults(minimal_project: Path):
    m = mod.load_manifest(minimal_project)
    assert m["contracts_dir"] == "docs/agents"
    assert m["binding_ttl_days"] == 30
