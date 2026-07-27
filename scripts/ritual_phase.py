#!/usr/bin/env python3
"""9-phase ritual state machine — strict sequential phase line."""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

PHASES: tuple[str, ...] = (
    "1-wake",
    "2-orient",
    "3-select",
    "4-execute",
    "5-verify",
    "6-review",
    "7-triage",
    "8-close",
    "9-arm",
)

LOOP_PREFIX: dict[str, str] = {
    "worker-relay": "rf",
    "ux-relay": "ux",
    "code-health": "ch",
    "po-relay": "pr",
}


def normalize_phase(name: str) -> str:
    raw = (name or "").strip().strip("`").lower()
    if not raw:
        return "1-wake"
    for phase in PHASES:
        if raw == phase or raw.replace("_", "-") == phase:
            return phase
    m = re.search(r"(\d+)", raw)
    if m:
        num = int(m.group(1))
        for phase in PHASES:
            if phase.startswith(f"{num}-"):
                return phase
    return "1-wake"


def phase_index(name: str) -> int:
    phase = normalize_phase(name)
    try:
        return PHASES.index(phase)
    except ValueError:
        return 0


def next_phase(name: str) -> str | None:
    idx = phase_index(name)
    if idx + 1 >= len(PHASES):
        return None
    return PHASES[idx + 1]


def allowed_phase_on_wake(stored_phase: str) -> str:
    """New tick always starts at 1-wake (9-arm from prior turn is stale)."""
    return "1-wake"


def validate_transition(from_phase: str, to_phase: str) -> tuple[bool, str]:
    src = phase_index(from_phase)
    dst = phase_index(to_phase)
    if dst == src:
        return True, ""
    if dst == src + 1:
        return True, ""
    if dst < src:
        return False, f"cannot move backward {normalize_phase(from_phase)} → {normalize_phase(to_phase)}"
    return False, (
        f"cannot skip phases {normalize_phase(from_phase)} → {normalize_phase(to_phase)} "
        "(advance one at a time)"
    )


def phase_line_marker(current: str) -> str:
    cur = normalize_phase(current)
    parts: list[str] = []
    for phase in PHASES:
        label = phase.split("-", 1)[1]
        if phase == cur:
            parts.append(f"[YOU ARE HERE: {phase}]")
        else:
            parts.append(label)
    return " → ".join(parts)


def parse_checkpoint_table(state_text: str) -> dict[str, str]:
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
            val = parts[2].strip("`").strip()
            if key.lower() not in ("field", "-------") and val and val != "—":
                out[key] = val
    return out


def parse_review_findings_sources(state_text: str) -> list[str]:
    sources: list[str] = []
    if "## REVIEW_FINDINGS" not in state_text:
        return sources
    section = state_text.split("## REVIEW_FINDINGS", 1)[1]
    if "\n## " in section:
        section = section.split("\n## ", 1)[0]
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 8:
            continue
        cells = parts[1:-1]
        if len(cells) < 4:
            continue
        if cells[0].lower() in ("id", "----") or cells[0] in ("—", "-", ""):
            continue
        sources.append(cells[3])
    return sources


def has_round_findings(state_text: str, review_round: str) -> bool:
    rnd = (review_round or "").strip().strip("`")
    if not rnd or rnd in ("?", "—", "-"):
        return False
    pattern = f"round-{rnd}"
    for src in parse_review_findings_sources(state_text):
        if pattern in src:
            return True
    return False


def git_has_code_changes(project_root: Path) -> bool:
    for args in (
        ["git", "diff", "--quiet", "HEAD", "--", "pwa/", "server/"],
        ["git", "diff", "--quiet", "--cached", "--", "pwa/", "server/"],
    ):
        try:
            r = subprocess.run(args, cwd=project_root, capture_output=True)
            if r.returncode == 1:
                return True
        except OSError:
            return False
    return False


@dataclass
class GateResult:
    ok: bool
    allowed_phase: str
    reason: str
    fix: str


def _yes(val: str) -> bool:
    return (val or "").strip().strip("`").lower() in ("yes", "true", "1")


def required_phase_before_arm(
    checkpoint: dict[str, str],
    state_text: str,
    *,
    project_root: Path | None = None,
    mode: str = "arm",
) -> GateResult:
    """Return the phase the agent must complete before arm/checkpoint passes."""
    phase = normalize_phase(checkpoint.get("phase", "1-wake"))
    code_changed = _yes(checkpoint.get("code_changed", "no"))
    review_status = (checkpoint.get("review_status") or "pending").strip().strip("`").lower()
    review_round = (checkpoint.get("review_round") or "0").strip().strip("`")
    skip_reason = (checkpoint.get("review_skip_reason") or "").strip().strip("`")

    if mode == "wake":
        return GateResult(True, allowed_phase_on_wake(phase), "", "Start at Phase 1-wake")

    if phase_index(phase) < phase_index("8-close"):
        nxt = next_phase(phase) or "8-close"
        if phase_index(phase) == 0:
            nxt = "1-wake"
        reason = f"phase={phase} but must reach 8-close before {'arm' if mode == 'arm' else 'checkpoint'}"
        fix = f"Complete Phase {nxt} next; advance one phase at a time"
        return GateResult(False, nxt, reason, fix)

    if phase == "9-arm":
        if mode == "arm":
            return GateResult(
                False,
                "8-close",
                "phase=9-arm before arm-wake.sh (9-arm is post-arm only)",
                "Set phase=8-close, run arm-wake.sh, verify-wake exit 0, then set phase=9-arm",
            )
        return GateResult(True, "1-wake", "", "Next wake starts at 1-wake")

    if phase == "8-close":
        if review_status == "pending":
            target = "6-review" if code_changed else "8-close"
            return GateResult(
                False,
                target,
                "review_status=pending at 8-close",
                "Complete Phase 6 /code-review then Phase 7 /receiving-code-review",
            )
        if code_changed:
            if review_status == "skipped":
                return GateResult(
                    False,
                    "5-verify",
                    "code_changed=yes but review_status=skipped",
                    "Re-run Phase 5 detect_code_changed; run /code-review if yes",
                )
            if review_status not in ("done", "triaged"):
                return GateResult(
                    False,
                    "7-triage",
                    f"review_status={review_status} invalid for code_changed=yes",
                    "Phase 7: triage round-N findings; set review_status=done or triaged",
                )
            if not has_round_findings(state_text, review_round):
                return GateResult(
                    False,
                    "6-review",
                    f"code_changed=yes but no round-{review_round} REVIEW_FINDINGS",
                    f"Phase 6: run /code-review Round {review_round}; log findings or sentinel row",
                )
        else:
            if review_status == "done":
                return GateResult(
                    False,
                    "8-close",
                    "code_changed=no but review_status=done (use skipped)",
                    "Set review_status=skipped with review_skip_reason",
                )
            if review_status == "skipped" and not skip_reason:
                return GateResult(
                    False,
                    "8-close",
                    "review_status=skipped without review_skip_reason",
                    "Add non-empty review_skip_reason to CHECKPOINT",
                )

        if project_root is not None and git_has_code_changes(project_root) and not code_changed:
            return GateResult(
                False,
                "5-verify",
                "git diff in pwa/ or server/ but code_changed=no",
                "Run detect_code_changed.sh; set code_changed=yes and increment review_round",
            )

        if mode == "arm":
            return GateResult(True, "9-arm", "", "Run arm-wake.sh; after verify-wake exit 0 set phase=9-arm")

        return GateResult(True, "8-close", "", "Ready for checkpoint-loop --product")

    return GateResult(False, "8-close", f"unexpected phase={phase}", "Complete Phase 8 close checklist")


def phase_exit_criteria(phase: str, code_changed: bool) -> list[str]:
    p = normalize_phase(phase)
    criteria: dict[str, list[str]] = {
        "1-wake": ["Read INSTANCE → IDENTITY → STATE → RITUAL", "Set CHECKPOINT.phase=1-wake"],
        "2-orient": ["Update LAST_REVIEW", "Read CHECKPOINT + git status", "Set phase=2-orient"],
        "3-select": ["Pick top backlog item or resume IN_PROGRESS", "Set phase=3-select"],
        "4-execute": ["Ship execute/brainstorm work for selected item", "Set phase=4-execute"],
        "5-verify": [
            "Run build/tests",
            "Run detect_code_changed.sh",
            "Set code_changed yes/no",
            "Set phase=5-verify",
        ],
        "6-review": ["Invoke /code-review Round N", "Log REVIEW_FINDINGS", "Set phase=6-review"],
        "7-triage": [
            "Invoke /receiving-code-review Round N",
            "Triage findings",
            "Set review_status",
            "Set phase=7-triage",
        ],
        "8-close": ["HISTORY row", "Clear IN_PROGRESS", "Set phase=8-close"],
        "9-arm": ["checkpoint-loop --product", "arm-wake.sh + verify-wake exit 0", "Set phase=9-arm"],
    }
    items = list(criteria.get(p, []))
    if p == "5-verify" and not code_changed:
        items.append("May skip 6-7 with review_status=skipped + reason")
    return items
