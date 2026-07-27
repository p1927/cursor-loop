"""Segment: stop hook emits review followup when wake would be ARMED."""
from __future__ import annotations

import json
import io
import subprocess
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import hook_survival  # noqa: E402
import loop_hook_lib as mod  # noqa: E402
import ritual_phase as rp  # noqa: E402

pytestmark = pytest.mark.segment


def _init_git_with_change(project: Path, rel_path: str = "pwa/test.ts") -> None:
    subprocess.run(["git", "init"], cwd=project, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=project, check=True)
    path = project / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("export const x = 1;\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=project, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=project, check=True, capture_output=True)
    path.write_text("export const x = 2;\n", encoding="utf-8")


def test_review_stop_needed_at_phase_8_with_sentinel_only(minimal_project: Path):
    _init_git_with_change(minimal_project)
    state_dir = minimal_project / "docs/window-instances/worker-relay"
    state_dir.mkdir(parents=True)
    state_file = "docs/window-instances/worker-relay/STATE.md"
    state_text = """## CHECKPOINT
| Field | Value |
| phase | `8-close` |
| review_status | done |
| review_round | `1` |
| last_reviewed_round | `1` |
| code_changed | yes |
| review_changed_files | `pwa/test.ts` |
| review_fingerprint | `deadbeef` |

## REVIEW_FINDINGS
| id | severity | finding | source | action | backlog_ref | status |
| wr-r1-000 | low | No issues | round-1 /code-review | closed | — | closed |
"""
    (state_dir / "STATE.md").write_text(state_text, encoding="utf-8")

    cp = rp.parse_checkpoint_table(state_text)
    result = rp.review_stop_needed(
        cp,
        state_text,
        project_root=minimal_project,
        loop_id="worker-relay",
        state_file=state_file,
    )
    assert result is not None
    assert not result.ok
    assert result.allowed_phase in ("5-verify", "6-review", "7-triage")


def test_hook_survival_review_before_wake_armed(minimal_project: Path, monkeypatch):
    _init_git_with_change(minimal_project)
    loop_id = "worker-relay"
    state_rel = "docs/window-instances/worker-relay/STATE.md"
    state_dir = minimal_project / "docs/window-instances/worker-relay"
    state_dir.mkdir(parents=True)
    state_text = """## CHECKPOINT
| Field | Value |
| phase | `8-close` |
| review_status | done |
| review_round | `1` |
| last_reviewed_round | `1` |
| code_changed | yes |
| review_changed_files | `pwa/test.ts` |
| review_fingerprint | `deadbeef` |

## REVIEW_FINDINGS
| id | severity | finding | source | action | backlog_ref | status |
| wr-r1-000 | low | No issues | round-1 /code-review | closed | — | closed |
"""
    (state_dir / "STATE.md").write_text(state_text, encoding="utf-8")

    cid = "review-stop-test"
    binding = {
        "loop_id": loop_id,
        "contract_doc": "docs/window-instances/worker-relay/INSTANCE.md",
        "state_file": state_rel,
        "loop_mode": "dynamic",
        "stopped": False,
    }
    mod.write_binding(minimal_project, cid, binding)

    monkeypatch.setenv(
        "CURSOR_LOOP_INPUT",
        json.dumps(
            {
                "conversation_id": cid,
                "workspace_roots": [str(minimal_project)],
            }
        ),
    )

    # Wake would be UP — review followup must still fire first
    monkeypatch.setattr(hook_survival, "_is_loop_up", lambda _b: True)

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = hook_survival.main()
    assert rc == 0
    out = buf.getvalue().strip()
    assert out
    payload = json.loads(out)
    assert "followup_message" in payload
    msg = payload["followup_message"]
    assert "REVIEW INCOMPLETE" in msg
    assert "pwa/test.ts" in msg
    assert "/code-review" in msg
