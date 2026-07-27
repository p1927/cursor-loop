"""Factory for isolated cursor-loop test projects."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[2]

SAMPLE_CONTRACT = """\
# Test contract

## Loop config

| Field | Value |
|-------|-------|
| loop_id | `{loop_id}` |
| sentinel | `{sentinel}` |
| wake_sentinel | `{wake_sentinel}` |
| interval_sec | `60` |
| monitor_regex | `^{sentinel}` |
| loop_script | `{loop_script}` |
| contract_doc | `{contract_doc}` |

## Task

Test task.
"""


def write_contract(
    project: Path,
    *,
    loop_id: str = "test-loop",
    rel: str = "docs/agents/test-loop.md",
    loop_script: str | None = None,
) -> Path:
    loop_script = loop_script or "vendor/cursor-loop/scripts/agent-loop.sh"
    doc = project / rel
    doc.parent.mkdir(parents=True, exist_ok=True)
    sentinel = f"AGENT_LOOP_TICK_{loop_id.upper().replace('-', '_')}"
    wake = f"AGENT_LOOP_WAKE_{loop_id.upper().replace('-', '_')}"
    doc.write_text(
        SAMPLE_CONTRACT.format(
            loop_id=loop_id,
            sentinel=sentinel,
            wake_sentinel=wake,
            loop_script=loop_script,
            contract_doc=rel,
        ),
        encoding="utf-8",
    )
    return doc


def install_copy_project(project: Path, package_path: str = "vendor/cursor-loop") -> None:
    subprocess.run(
        ["bash", str(PACKAGE_ROOT / "install.sh"), str(project), "--copy", "--package-path", package_path],
        check=True,
        capture_output=True,
        text=True,
    )


def write_manifest(project: Path, package_path: str = "tools/cursor-loop") -> None:
    manifest = project / ".cursor" / "cursor-loop.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {
                "version": "0.3.0",
                "package_root": package_path,
                "contracts_dir": "docs/agents",
                "contract_globs": [],
                "binding_ttl_days": 30,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def minimal_package_layout(project: Path, package_path: str = "tools/cursor-loop") -> None:
    """Vendor scripts without full install (for fast segment tests)."""
    src = PACKAGE_ROOT / "scripts"
    dest = project / package_path / "scripts"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    for name in dest.iterdir():
        if name.suffix in {".py", ".sh"}:
            name.chmod(0o755)
    write_manifest(project, package_path)
