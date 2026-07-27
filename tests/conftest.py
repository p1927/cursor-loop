"""Pytest fixtures with guaranteed cleanup."""
from __future__ import annotations

import pytest

from helpers.cleanup import cleanup_pidfiles_glob, cleanup_project, cleanup_temp_dir
from helpers.project_factory import install_copy_project, minimal_package_layout, write_contract


@pytest.fixture
def isolated_tmpdir(tmp_path, monkeypatch):
    """Isolated TMPDIR so pidfiles never touch system /tmp clutter long-term."""
    tmp = tmp_path / "tmp"
    tmp.mkdir()
    monkeypatch.setenv("TMPDIR", str(tmp))
    yield tmp_path
    cleanup_pidfiles_glob()
    cleanup_temp_dir(tmp_path)


@pytest.fixture
def minimal_project(isolated_tmpdir):
    """Project with manifest + scripts only."""
    minimal_package_layout(isolated_tmpdir)
    yield isolated_tmpdir
    cleanup_project(isolated_tmpdir)


@pytest.fixture
def installed_project(isolated_tmpdir):
    """Full copy install in temp project."""
    install_copy_project(isolated_tmpdir, package_path="vendor/cursor-loop")
    write_contract(isolated_tmpdir, loop_id="test-loop", loop_script="vendor/cursor-loop/scripts/agent-loop.sh")
    yield isolated_tmpdir
    cleanup_project(isolated_tmpdir)
