"""Invoke cursor-loop hooks in tests."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path


def invoke_hook(project: Path, hook: str, payload: dict) -> tuple[int, str, str]:
    hook_path = project / ".cursor" / "hooks" / hook
    proc = subprocess.run(
        ["bash", str(hook_path)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(project),
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
