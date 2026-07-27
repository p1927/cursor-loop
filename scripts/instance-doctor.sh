#!/usr/bin/env bash
# Window Instance health dashboard — all entries in instances.manifest.json
set -euo pipefail

ROOT="${1:-.}"
ROOT="$(cd "$ROOT" && pwd)"
MANIFEST="$(python3 - "$ROOT" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
manifest_path = root / ".cursor" / "cursor-loop.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
rel = manifest.get("instances_manifest", "docs/window-instances/instances.manifest.json")
print(root / rel)
PY
)"
SCRIPTS="$(python3 - "$ROOT" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
manifest = json.loads((root / ".cursor/cursor-loop.json").read_text(encoding="utf-8"))
print(root / manifest["package_root"] / "scripts")
PY
)"

if [[ ! -f "$MANIFEST" ]]; then
  echo "instance-doctor: missing $MANIFEST" >&2
  exit 1
fi

python3 "$SCRIPTS/validate_instance.py" "$ROOT" || true

echo ""
echo "=== Window Instance Doctor ==="

python3 - "$ROOT" "$MANIFEST" "$SCRIPTS" <<'PY'
import json
import re
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
manifest_path = Path(sys.argv[2])
scripts_dir = Path(sys.argv[3])
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
instances = manifest.get("instances") or []

def parse_checkpoint(state_text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    if "## CHECKPOINT" not in state_text:
        return out
    section = state_text.split("## CHECKPOINT", 1)[1]
    if "\n## " in section:
        section = section.split("\n## ", 1)[0]
    for line in section.splitlines():
        if "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 3 and parts[1] and parts[2]:
            key = parts[1].strip("`")
            val = parts[2].strip("`")
            if key and val and key.lower() not in ("field", "-------"):
                out[key] = val
    return out

def count_open_backlog(state_text: str) -> int:
    return len(re.findall(r"^\s*-\s*\[\s*\]", state_text, re.MULTILINE))

def has_round_findings(state_text: str, review_round: str) -> bool:
    rnd = (review_round or "").strip().strip("`")
    if not rnd or rnd in ("?", "—", "-"):
        return False
    pattern = f"round-{rnd}"
    return pattern in state_text

def parse_phase_num(phase: str) -> int:
    m = re.search(r"(\d+)", phase or "")
    return int(m.group(1)) if m else 0

def read_wake_armed_at(loop_id: str) -> str | None:
    import os
    tmp = Path(os.environ.get("TMPDIR") or "/tmp")
    armed = tmp / f"cursor-loop-{loop_id}.wake.armed"
    if not armed.is_file():
        return None
    return armed.read_text(encoding="utf-8").strip() or None

def wake_status(loop_id: str) -> str:
    script = scripts_dir / "verify-wake.sh"
    armed_at = read_wake_armed_at(loop_id)
    if not script.is_file():
        return "?"
    try:
        r = subprocess.run(
            ["bash", str(script), loop_id],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode == 0:
            return "ARMED" + (f" since {armed_at}" if armed_at else "")
        if armed_at:
            return f"DOWN (last armed {armed_at}) — re-arm required"
        return "DOWN (never armed)"
    except Exception:
        return "?"

def persistent_status(loop_id: str) -> str | None:
    script = scripts_dir / "verify-loop.sh"
    if not script.is_file():
        return None
    try:
        r = subprocess.run(
            ["bash", str(script), loop_id],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode == 0:
            return "STALE persistent agent-loop.sh running — run: cwin refresh"
    except Exception:
        pass
    return None

for entry in instances:
    loop_id = entry.get("loop_id", "?")
    bundle = root / entry.get("bundle", "")
    state_path = root / entry.get("state_file", "")
    status = "OK"
    notes: list[str] = []

    if not bundle.is_dir():
        status = "MISSING"
        notes.append("bundle missing")
    elif not state_path.is_file():
        status = "WARN"
        notes.append("state missing")
    else:
        state_text = state_path.read_text(encoding="utf-8")
        cp = parse_checkpoint(state_text)
        phase = cp.get("phase", "?")
        review = cp.get("review_status", "?")
        code_changed = cp.get("code_changed", "no").lower()
        review_round = cp.get("review_round", "0")
        open_items = count_open_backlog(state_text)
        wake = wake_status(loop_id)
        stale = persistent_status(loop_id)
        phase_num = parse_phase_num(phase)
        if stale:
            status = "WARN"
            notes.append(stale)
        if code_changed == "yes" and review in ("done", "triaged") and not has_round_findings(state_text, review_round):
            status = "WARN"
            notes.append(f"review_status={review} but no round-{review_round.strip('`')} findings")
        if review == "pending" and phase_num >= 4:
            status = "WARN"
            notes.append("review_status=pending past verify")
        if code_changed == "yes" and review == "pending" and phase_num >= 7:
            status = "WARN"
            notes.append("code_changed=yes but review pending at phase>=7")
        if phase_num >= 9 and "DOWN" in wake:
            status = "WARN"
            notes.append("phase=9-arm but wake DOWN — re-arm required")
        print(
            f"{loop_id:16} {status:4}  phase={phase:12} review={review:8} "
            f"code_changed={code_changed:3} round={review_round:3} "
            f"backlog_open={open_items:2}  wake={wake}"
        )
        if notes:
            print(f"  notes: {', '.join(notes)}")
        continue

    wake = wake_status(loop_id)
    print(f"{loop_id:16} {status:4}  wake={wake}  {'; '.join(notes)}")
PY

echo ""
echo "Run: python3 $SCRIPTS/validate_instance.py ."
