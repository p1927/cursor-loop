#!/usr/bin/env python3
"""Audit HISTORY vs REVIEW_FINDINGS — detect code ships without /code-review."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import loop_hook_lib as mod
import ritual_phase as rp

CODE_HISTORY_PATTERN = re.compile(
    r"\b(build|commit|shipped|pwa/|server/|relay-|ui-|ch-|rf-|ux-|pr-)\b",
    re.IGNORECASE,
)


def parse_history_rows(state_text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if "## HISTORY" not in state_text:
        return rows
    section = state_text.split("## HISTORY", 1)[1]
    if "\n## " in section:
        section = section.split("\n## ", 1)[0]
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 7:
            continue
        cells = parts[1:-1]
        if len(cells) < 5:
            continue
        if cells[0].lower() in ("completed_at", "----") or cells[0] in ("—", "-", ""):
            continue
        rows.append(
            {
                "completed_at": cells[0],
                "item_id": cells[1],
                "phase": cells[2],
                "outcome": cells[3],
                "evidence": cells[4] if len(cells) > 4 else "",
            }
        )
    return rows


def history_suggests_code(row: dict[str, str]) -> bool:
    blob = " ".join((row.get("outcome", ""), row.get("evidence", ""), row.get("phase", "")))
    if CODE_HISTORY_PATTERN.search(blob):
        return True
    phase = (row.get("phase") or "").lower()
    return "execute" in phase or "4-" in phase


def audit_state(
    *,
    loop_id: str,
    state_file: str,
    state_text: str,
    project_root: Path,
) -> list[str]:
    issues: list[str] = []
    checkpoint = rp.parse_checkpoint_table(state_text)
    review_round = (checkpoint.get("review_round") or "0").strip().strip("`")
    review_status = (checkpoint.get("review_status") or "pending").strip().strip("`").lower()
    code_changed = (checkpoint.get("code_changed") or "no").strip().strip("`").lower() in (
        "yes",
        "true",
        "1",
    )
    last_reviewed = rp.max_reviewed_round(state_text)
    round_num = rp.parse_review_round(review_round)
    git_diff = rp.git_has_code_changes(project_root, loop_id, state_file)
    last_wake = checkpoint.get("last_wake", "")

    if git_diff and review_status in ("done", "triaged"):
        if not rp.has_round_findings(state_text, review_round):
            issues.append(
                f"git diff present, review_status={review_status}, "
                f"but no round-{review_round} REVIEW_FINDINGS"
            )
        elif round_num < last_reviewed:
            issues.append(
                f"git diff present, review_round={round_num} stale "
                f"(last_reviewed_round={last_reviewed})"
            )

    if code_changed and review_status in ("done", "triaged"):
        if not rp.has_round_findings(state_text, review_round):
            issues.append(
                f"code_changed=yes, review_status={review_status}, "
                f"no round-{review_round} findings logged"
            )

    if review_status in ("done", "triaged") and round_num > last_reviewed:
        if not rp.has_round_findings(state_text, review_round):
            issues.append(
                f"review_round={round_num} > last_reviewed_round={last_reviewed} "
                f"but no matching REVIEW_FINDINGS"
            )

    code_history = [r for r in parse_history_rows(state_text) if history_suggests_code(r)]
    if code_history and last_reviewed < 0 and review_status in ("done", "triaged"):
        issues.append("HISTORY shows code ships but REVIEW_FINDINGS is empty")

    recent = code_history[-5:]
    if recent and not rp.has_round_findings(state_text, review_round) and code_changed:
        ids = ", ".join(r.get("item_id", "?") for r in recent[-3:])
        issues.append(
            f"recent HISTORY code rows ({ids}) with no round-{review_round} review logged"
        )

    if last_wake and code_changed and review_status == "pending":
        issues.append(
            f"last_wake={last_wake}: code_changed=yes but review still pending "
            "(Phase 6 /code-review not completed)"
        )

    worktree_status = (checkpoint.get("worktree_status") or "none").strip().strip("`").lower()
    if worktree_status == "active" and review_status in ("done", "triaged"):
        issues.append(
            "worktree_status=active with review complete — merge+remove worktree before Phase 8"
        )

    if git_diff:
        issues.extend(
            rp.manifest_gate_issues(checkpoint, project_root, loop_id, state_file)
        )

    if git_diff and review_status in ("done", "triaged"):
        import review_scope as rs

        live_files = rs.list_changed_files(
            project_root, rs.review_paths(loop_id, state_file)
        )
        if live_files and rp.is_sentinel_only_review(state_text, review_round):
            issues.append(
                f"sentinel-only round-{review_round} review with {len(live_files)} changed file(s)"
            )

    for row in rp.parse_round_finding_rows(state_text, review_round):
        if (row.get("action") or "").strip().strip("`").lower() == "backlog":
            ref = (row.get("backlog_ref") or "").strip().strip("`")
            if not ref or ref in ("—", "-"):
                issues.append(f"{row.get('id')}: action=backlog without backlog_ref")

    return issues


def load_instances(project_root: Path) -> list[dict]:
    manifest = mod.load_manifest(project_root)
    data = mod.load_instances_manifest(project_root, manifest)
    return data.get("instances") or []


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit per-tick /code-review compliance")
    parser.add_argument("project", nargs="?", default=".", help="Project root")
    parser.add_argument("--loop-id", default="", help="Audit single instance")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    root = Path(args.project).resolve()
    instances = load_instances(root)
    if args.loop_id:
        instances = [i for i in instances if i.get("loop_id") == args.loop_id]
        if not instances:
            print(f"audit-review: unknown loop_id {args.loop_id}", file=sys.stderr)
            return 1

    report: list[dict] = []
    exit_code = 0
    for entry in instances:
        loop_id = entry.get("loop_id", "")
        state_file = entry.get("state_file", "")
        state_path = root / state_file
        if not state_path.is_file():
            report.append({"loop_id": loop_id, "ok": False, "issues": [f"missing {state_file}"]})
            exit_code = 1
            continue
        state_text = state_path.read_text(encoding="utf-8")
        issues = audit_state(
            loop_id=loop_id,
            state_file=state_file,
            state_text=state_text,
            project_root=root,
        )
        ok = not issues
        if not ok:
            exit_code = 1
        report.append({"loop_id": loop_id, "ok": ok, "issues": issues})

    if args.json:
        print(json.dumps({"project": str(root), "instances": report}, indent=2))
    else:
        print(f"Review audit — {root}")
        for row in report:
            status = "OK" if row["ok"] else "FAIL"
            print(f"\n{row['loop_id']}: {status}")
            for issue in row["issues"]:
                print(f"  - {issue}")
        if exit_code == 0:
            print("\nAll instances pass review audit")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
