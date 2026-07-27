#!/usr/bin/env python3
"""9-phase ritual state machine — strict sequential phase line."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import review_scope as rs

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

CODE_WORKTREE_ARCHETYPES = frozenset({"engineer", "designer", "qa"})


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


def parse_round_finding_rows(state_text: str, review_round: str) -> list[dict[str, str]]:
    rnd = (review_round or "").strip().strip("`")
    if not rnd:
        return []
    pattern = f"round-{rnd}"
    rows: list[dict[str, str]] = []
    if "## REVIEW_FINDINGS" not in state_text:
        return rows
    section = state_text.split("## REVIEW_FINDINGS", 1)[1]
    if "\n## " in section:
        section = section.split("\n## ", 1)[0]
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 9:
            continue
        cells = parts[1:-1]
        if len(cells) < 7:
            continue
        if cells[0].lower() in ("id", "----") or cells[0] in ("—", "-", ""):
            continue
        if pattern not in cells[3]:
            continue
        rows.append(
            {
                "id": cells[0],
                "action": cells[4],
                "backlog_ref": cells[5] if len(cells) > 5 else "",
                "status": cells[6] if len(cells) > 6 else "",
            }
        )
    return rows


def backlog_reflect_issues(state_text: str, review_round: str) -> list[str]:
    issues: list[str] = []
    for row in parse_round_finding_rows(state_text, review_round):
        fid = row.get("id", "?")
        action = (row.get("action") or "").strip().strip("`").lower()
        status = (row.get("status") or "").strip().strip("`").lower()
        backlog_ref = (row.get("backlog_ref") or "").strip().strip("`")
        if not action or action in ("—", "-", "open"):
            issues.append(f"{fid}: action not triaged (set fix-now|backlog|closed|pushback)")
        elif action == "backlog":
            if not backlog_ref or backlog_ref in ("—", "-"):
                issues.append(f"{fid}: action=backlog missing backlog_ref (Phase 7b)")
            elif backlog_ref not in state_text:
                issues.append(f"{fid}: backlog_ref '{backlog_ref}' not found in STATE (Phase 7b)")
            elif status not in ("open", "closed"):
                issues.append(f"{fid}: action=backlog requires status=open or closed")
    return issues


def round_finding_rows_full(state_text: str, review_round: str) -> list[dict[str, str]]:
    rnd = (review_round or "").strip().strip("`")
    if not rnd:
        return []
    pattern = f"round-{rnd}"
    rows: list[dict[str, str]] = []
    if "## REVIEW_FINDINGS" not in state_text:
        return rows
    section = state_text.split("## REVIEW_FINDINGS", 1)[1]
    if "\n## " in section:
        section = section.split("\n## ", 1)[0]
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 9:
            continue
        cells = parts[1:-1]
        if len(cells) < 4:
            continue
        if cells[0].lower() in ("id", "----") or cells[0] in ("—", "-", ""):
            continue
        if pattern not in cells[3]:
            continue
        rows.append(
            {
                "id": cells[0],
                "finding": cells[2] if len(cells) > 2 else "",
                "action": cells[4] if len(cells) > 4 else "",
                "backlog_ref": cells[5] if len(cells) > 5 else "",
                "status": cells[6] if len(cells) > 6 else "",
            }
        )
    return rows


def is_sentinel_only_review(state_text: str, review_round: str) -> bool:
    rows = round_finding_rows_full(state_text, review_round)
    if not rows:
        return False
    rnd = (review_round or "").strip().strip("`")
    for row in rows:
        fid = row.get("id", "")
        if not re.search(rf"-r{re.escape(rnd)}-000$", fid):
            return False
    return True


def manifest_gate_issues(
    checkpoint: dict[str, str],
    project_root: Path,
    loop_id: str,
    state_file: str,
) -> list[str]:
    paths = rs.review_paths(loop_id, state_file)
    git_root = git_root_for_checkpoint(project_root, checkpoint)
    live = rs.list_changed_files(git_root, paths)
    if not live:
        return []
    stored_files = checkpoint.get("review_changed_files", "")
    stored_fp = checkpoint.get("review_fingerprint", "")
    if not stored_files or stored_files.strip().strip("`") in ("—", "-", ""):
        return ["review_changed_files empty — run prepare_review_tick.sh --apply in Phase 5"]
    ok, _, live_fp = rs.manifest_matches_git(git_root, paths, stored_files, stored_fp)
    if not ok:
        return [
            f"review manifest stale (checkpoint fp != git fp {live_fp}) — re-run prepare_review_tick.sh --apply"
        ]
    return []


def review_stop_needed(
    checkpoint: dict[str, str],
    state_text: str,
    *,
    project_root: Path,
    loop_id: str,
    state_file: str,
) -> GateResult | None:
    """Return GateResult when stop hook should force review completion."""
    phase = normalize_phase(checkpoint.get("phase", "1-wake"))
    if phase_index(phase) < phase_index("5-verify"):
        return None
    if not git_has_code_changes(project_root, loop_id, state_file):
        return None
    gate = required_phase_before_arm(
        checkpoint,
        state_text,
        project_root=project_root,
        mode="arm",
        loop_id=loop_id,
        state_file=state_file,
    )
    if gate.ok:
        return None
    allowed = normalize_phase(gate.allowed_phase)
    if phase_index(phase) < phase_index(allowed):
        return None
    if allowed not in ("5-verify", "6-review", "7-triage") and phase != "8-close":
        return None
    return gate


def has_round_findings(state_text: str, review_round: str) -> bool:
    rnd = (review_round or "").strip().strip("`")
    if not rnd or rnd in ("?", "—", "-"):
        return False
    pattern = f"round-{rnd}"
    for src in parse_review_findings_sources(state_text):
        if pattern in src:
            return True
    return False


def max_reviewed_round(state_text: str) -> int:
    rounds: list[int] = []
    checkpoint = parse_checkpoint_table(state_text)
    lr = checkpoint.get("last_reviewed_round", "")
    if lr:
        try:
            rounds.append(int(str(lr).strip().strip("`")))
        except ValueError:
            pass
    for src in parse_review_findings_sources(state_text):
        m = re.search(r"round-(\d+)", src)
        if m:
            rounds.append(int(m.group(1)))
    return max(rounds) if rounds else -1


def parse_review_round(val: str) -> int:
    try:
        return int(str(val or "0").strip().strip("`"))
    except ValueError:
        return 0


def git_root_for_checkpoint(project_root: Path, checkpoint: dict[str, str]) -> Path:
    """Use active worktree as git cwd when CHECKPOINT says worktree_status=active."""
    status = (checkpoint.get("worktree_status") or "none").strip().strip("`").lower()
    raw_path = (checkpoint.get("worktree_path") or "").strip().strip("`")
    if status == "active" and raw_path and raw_path not in ("—", "-", ""):
        wt = Path(raw_path)
        if not wt.is_absolute():
            wt = project_root / wt
        if wt.is_dir():
            return wt.resolve()
    return project_root


def git_has_code_changes(
    project_root: Path,
    loop_id: str = "",
    state_file: str = "",
    checkpoint: dict[str, str] | None = None,
) -> bool:
    paths = rs.review_paths(loop_id, state_file)
    git_root = git_root_for_checkpoint(project_root, checkpoint or {})
    return rs.git_has_changes(git_root, paths)


def requires_worktree(archetype: str) -> bool:
    return (archetype or "").strip().lower() in CODE_WORKTREE_ARCHETYPES


def parse_current_item_id(state_text: str, checkpoint: dict[str, str]) -> str:
    item = (checkpoint.get("current_item_id") or "").strip().strip("`")
    if item and item not in ("—", "-", ""):
        return item
    if "## IN_PROGRESS" not in state_text:
        return ""
    section = state_text.split("## IN_PROGRESS", 1)[1]
    if "\n## " in section:
        section = section.split("\n## ", 1)[0]
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3:
            continue
        key = parts[1].strip("`").lower()
        val = parts[2].strip("`").strip()
        if key in ("id", "----") or not val or val in ("—", "-", ""):
            continue
        if key == "id" or (parts[1] and val):
            return val
    return ""


def worktree_on_disk(project_root: Path, loop_id: str) -> bool:
    try:
        import worktree_lib as wt

        return wt.worktree_entry(project_root, loop_id) is not None
    except OSError:
        return False


def worktree_gate_issues(
    *,
    phase: str,
    checkpoint: dict[str, str],
    state_text: str,
    project_root: Path | None,
    loop_id: str,
    archetype: str,
    state_file: str = "",
) -> GateResult | None:
    """Return GateResult when worktree is required but missing."""
    if not requires_worktree(archetype):
        return None
    item_id = parse_current_item_id(state_text, checkpoint)
    if not item_id:
        return None
    worktree_status = (checkpoint.get("worktree_status") or "none").strip().strip("`").lower()
    idx = phase_index(phase)
    exec_idx = phase_index("4-execute")
    triage_idx = phase_index("7-triage")
    if exec_idx <= idx <= triage_idx:
        on_disk = project_root is not None and worktree_on_disk(project_root, loop_id)
        if worktree_status != "active" or not on_disk:
            sf = state_file or f"docs/window-instances/{loop_id}/STATE.md"
            return GateResult(
                False,
                "3-select",
                f"worktree required for {item_id} at {phase} (status={worktree_status})",
                f"Run prepare_select_tick.sh --state-file {sf}; "
                f"instance_worktree.sh create . --loop-id {loop_id} --item-id {item_id} --state-file {sf}",
            )
    return None


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
    loop_id: str = "",
    state_file: str = "",
    archetype: str = "",
) -> GateResult:
    """Return the phase the agent must complete before arm/checkpoint passes."""
    phase = normalize_phase(checkpoint.get("phase", "1-wake"))
    code_changed = _yes(checkpoint.get("code_changed", "no"))
    review_status = (checkpoint.get("review_status") or "pending").strip().strip("`").lower()
    review_round = (checkpoint.get("review_round") or "0").strip().strip("`")
    skip_reason = (checkpoint.get("review_skip_reason") or "").strip().strip("`")
    round_num = parse_review_round(review_round)
    last_reviewed = max_reviewed_round(state_text)
    skip_git_checks = mode == "steady"
    git_diff = (
        not skip_git_checks
        and project_root is not None
        and git_has_code_changes(project_root, loop_id, state_file, checkpoint)
    )
    worktree_status = (checkpoint.get("worktree_status") or "none").strip().strip("`").lower()

    if mode == "wake":
        return GateResult(True, allowed_phase_on_wake(phase), "", "Start at Phase 1-wake")

    wt_issue = worktree_gate_issues(
        phase=phase,
        checkpoint=checkpoint,
        state_text=state_text,
        project_root=project_root,
        loop_id=loop_id,
        archetype=archetype,
        state_file=state_file,
    )
    if wt_issue is not None:
        return wt_issue

    eval_mode = mode
    eval_phase = phase
    if mode == "arm" and phase == "9-arm":
        eval_phase = "8-close"
    if mode == "steady":
        if phase_index(phase) < phase_index("8-close"):
            nxt = next_phase(phase) or "8-close"
            return GateResult(
                False,
                nxt,
                f"phase={phase} but steady state requires 8-close or 9-arm",
                f"Complete Phase {nxt} next; advance one phase at a time",
            )
        if phase == "9-arm":
            eval_phase = "8-close"
        eval_mode = "checkpoint"

    if phase_index(eval_phase) < phase_index("8-close"):
        nxt = next_phase(eval_phase) or "8-close"
        if phase_index(eval_phase) == 0:
            nxt = "1-wake"
        reason = (
            f"phase={phase} but must reach 8-close before "
            f"{'arm' if mode == 'arm' else 'checkpoint' if mode == 'checkpoint' else 'steady check'}"
        )
        fix = f"Complete Phase {nxt} next; advance one phase at a time"
        return GateResult(False, nxt, reason, fix)

    if eval_phase == "8-close":
        if review_status == "pending":
            target = "6-review" if code_changed else "8-close"
            return GateResult(
                False,
                target,
                "review_status=pending at 8-close",
                "Complete Phase 6 /code-review then Phase 7 /receiving-code-review",
            )
        if code_changed:
            if git_diff and review_status in ("done", "triaged") and not has_round_findings(
                state_text, review_round
            ):
                return GateResult(
                    False,
                    "6-review",
                    f"stale review_status={review_status} with git diff but no round-{review_round} findings",
                    f"Run prepare_review_tick.sh; set review_status=pending; /code-review Round {round_num}",
                )
            if (
                git_diff
                and review_status in ("done", "triaged")
                and round_num < last_reviewed
            ):
                return GateResult(
                    False,
                    "5-verify",
                    f"review_round={round_num} not fresh (last_reviewed_round={last_reviewed}) with new git diff",
                    f"Increment review_round to {last_reviewed + 1}; set review_status=pending; run /code-review",
                )
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
                    f"Phase 6: invoke /code-review Round {review_round}; log findings or sentinel row",
                )
            reflect_issues = backlog_reflect_issues(state_text, review_round)
            if reflect_issues:
                return GateResult(
                    False,
                    "7-triage",
                    "; ".join(reflect_issues[:3]),
                    "Phase 7b: complete backlog reflect — deferred findings need backlog_ref + backlog row",
                )
            if project_root is not None and not skip_git_checks:
                manifest_issues = manifest_gate_issues(
                    checkpoint, project_root, loop_id, state_file
                )
                if manifest_issues:
                    return GateResult(
                        False,
                        "5-verify",
                        manifest_issues[0],
                        "Run prepare_review_tick.sh --apply; invoke /code-review on changed_files",
                    )
                live_files = rs.list_changed_files(
                    git_root_for_checkpoint(project_root, checkpoint),
                    rs.review_paths(loop_id, state_file),
                )
                if (
                    review_status in ("done", "triaged")
                    and live_files
                    and is_sentinel_only_review(state_text, review_round)
                ):
                    return GateResult(
                        False,
                        "6-review",
                        f"sentinel-only review with {len(live_files)} changed file(s)",
                        "Invoke /code-review; log findings citing each changed file or fix issues",
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

        if project_root is not None and git_diff and not code_changed and not skip_git_checks:
            scope = ", ".join(rs.review_paths(loop_id, state_file))
            return GateResult(
                False,
                "5-verify",
                f"git diff in window scope ({scope}) but code_changed=no",
                "Run prepare_review_tick.sh --apply; set code_changed=yes and increment review_round",
            )

        if project_root is not None and git_diff and not skip_git_checks:
            manifest_issues = manifest_gate_issues(
                checkpoint, project_root, loop_id, state_file
            )
            if manifest_issues:
                return GateResult(
                    False,
                    "5-verify",
                    manifest_issues[0],
                    "Run prepare_review_tick.sh --apply in Phase 5",
                )

        if worktree_status == "active":
            return GateResult(
                False,
                "8-close",
                "worktree_status=active at 8-close",
                "Run instance_worktree.sh merge then remove; set worktree_status=none",
            )

        if mode == "arm":
            return GateResult(True, "9-arm", "", "Run arm-wake.sh; after verify-wake exit 0 set phase=9-arm")

        if eval_mode == "checkpoint" and mode == "steady":
            return GateResult(True, "1-wake", "", "Steady state OK — next wake starts at 1-wake")

        return GateResult(True, "8-close", "", "Ready for checkpoint-loop --product")

    if eval_phase == "9-arm" and eval_mode == "checkpoint":
        return GateResult(True, "1-wake", "", "Next wake starts at 1-wake")

    return GateResult(False, "8-close", f"unexpected phase={phase}", "Complete Phase 8 close checklist")
    p = normalize_phase(phase)
    criteria: dict[str, list[str]] = {
        "1-wake": ["Read INSTANCE → IDENTITY → STATE → RITUAL", "Set CHECKPOINT.phase=1-wake"],
        "2-orient": ["Update LAST_REVIEW", "Read CHECKPOINT + git status", "Set phase=2-orient"],
        "3-select": [
            "Pick top backlog item or resume IN_PROGRESS",
            "Run prepare_select_tick.sh then instance_worktree.sh create when required",
            "Set phase=3-select",
        ],
        "4-execute": ["Ship execute/brainstorm work for selected item", "Set phase=4-execute"],
        "5-verify": [
            "Run build/tests",
            "Run prepare_review_tick.sh --apply --state-file STATE.md",
            "Apply suggested review_round / review_status / code_changed / review_changed_files",
            "Set phase=5-verify",
        ],
        "6-review": [
            "Invoke /code-review command (read full file first)",
            "Log REVIEW_FINDINGS",
            "Set phase=6-review",
        ],
        "7-triage": [
            "Read receiving-code-review skill + invoke /receiving-code-review (7a)",
            "Backlog reflect: deferred → backlog id + AC + backlog_ref (7b)",
            "Set review_status",
            "Set phase=7-triage",
        ],
        "8-close": [
            "Merge+remove worktree when active",
            "HISTORY row",
            "Clear IN_PROGRESS",
            "Set phase=8-close",
        ],
        "9-arm": ["checkpoint-loop --product", "arm-wake.sh + verify-wake exit 0", "Set phase=9-arm"],
    }
    items = list(criteria.get(p, []))
    if p == "5-verify" and not code_changed:
        items.append("May skip 6-7 with review_status=skipped + reason")
    return items
