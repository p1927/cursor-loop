#!/usr/bin/env python3
"""Phase 5 prep — detect code changes and suggest review CHECKPOINT updates."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import review_scope as rs
import ritual_phase as rp


def max_reviewed_round(state_text: str) -> int:
    rounds: list[int] = []
    checkpoint = rp.parse_checkpoint_table(state_text)
    lr = checkpoint.get("last_reviewed_round", "")
    if lr:
        try:
            rounds.append(int(str(lr).strip().strip("`")))
        except ValueError:
            pass
    for src in rp.parse_review_findings_sources(state_text):
        m = re.search(r"round-(\d+)", src)
        if m:
            rounds.append(int(m.group(1)))
    return max(rounds) if rounds else -1


def parse_int(val: str, default: int = 0) -> int:
    try:
        return int(str(val).strip().strip("`"))
    except (ValueError, TypeError):
        return default


def update_checkpoint_fields(state_text: str, updates: dict[str, str]) -> str:
    """Replace or append CHECKPOINT table rows by field name."""
    if not updates or "## CHECKPOINT" not in state_text:
        return state_text
    lines = state_text.splitlines()
    out: list[str] = []
    in_checkpoint = False
    seen: set[str] = set()
    field_re = re.compile(r"^\|\s*`?([^|`]+)`?\s*\|")

    for line in lines:
        if line.strip() == "## CHECKPOINT":
            in_checkpoint = True
            out.append(line)
            continue
        if in_checkpoint and line.strip().startswith("## "):
            for key, val in updates.items():
                if key not in seen:
                    out.append(f"| {key} | `{val}` |")
            in_checkpoint = False
            out.append(line)
            continue
        if in_checkpoint:
            m = field_re.match(line.strip())
            if m:
                key = m.group(1).strip()
                if key.lower() in ("field", "-------"):
                    out.append(line)
                    continue
                if key in updates:
                    out.append(f"| {key} | `{updates[key]}` |")
                    seen.add(key)
                    continue
        out.append(line)

    if in_checkpoint:
        for key, val in updates.items():
            if key not in seen:
                out.append(f"| {key} | `{val}` |")

    return "\n".join(out) + ("\n" if state_text.endswith("\n") else "")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare review tick for Phase 5")
    parser.add_argument("project", nargs="?", default=".", help="Project root")
    parser.add_argument("--state-file", required=True, help="Relative path to STATE.md")
    parser.add_argument("--loop-id", default="", help="Window loop_id (for scope + prefix)")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write suggested CHECKPOINT fields to STATE.md",
    )
    args = parser.parse_args()

    root = Path(args.project).resolve()
    state_path = root / args.state_file
    if not state_path.is_file():
        print(f"PREPARE_REVIEW_ERROR missing state file: {args.state_file}", file=sys.stderr)
        return 1

    state_text = state_path.read_text(encoding="utf-8")
    checkpoint = rp.parse_checkpoint_table(state_text)
    paths = rs.review_paths(args.loop_id, args.state_file)
    git_root = rp.git_root_for_checkpoint(root, checkpoint)
    has_diff = rs.git_has_changes(git_root, paths)
    changed_files = rs.list_changed_files(git_root, paths)
    fingerprint = rs.files_fingerprint(changed_files)
    diff_range = rs.git_diff_range_label(git_root, paths)
    last_reviewed = max_reviewed_round(state_text)
    current_round = parse_int(checkpoint.get("review_round", "0"))
    review_status = (checkpoint.get("review_status") or "pending").strip().strip("`").lower()

    print("PREPARE_REVIEW_BEGIN")
    print(f"git_root={git_root}")
    print(f"review_paths={' '.join(paths)}")
    print(f"code_changed={'yes' if has_diff else 'no'}")
    print(f"review_diff_range={diff_range if has_diff else 'none'}")
    print(f"changed_files={' '.join(changed_files)}")
    print(f"review_fingerprint={fingerprint}")

    updates: dict[str, str] = {
        "review_changed_files": " ".join(changed_files) if changed_files else "—",
        "review_fingerprint": fingerprint if changed_files else "—",
        "review_diff_range": diff_range if has_diff else "none",
    }

    if has_diff:
        suggested_round = max(current_round, last_reviewed + 1)
        if suggested_round <= last_reviewed:
            suggested_round = last_reviewed + 1
        print(f"suggested_review_round={suggested_round}")
        print("suggested_review_status=pending")
        print("suggested_code_changed=yes")
        updates["code_changed"] = "yes"
        updates["review_status"] = "pending"
        updates["review_round"] = str(suggested_round)
        stat = rs.git_diff_stat(git_root, paths)
        if stat:
            print("diff_stat_begin")
            print(stat)
            print("diff_stat_end")
        if review_status in ("done", "triaged") and last_reviewed >= 0:
            print(
                "WARN=stale review_status from prior tick — reset to pending and run /code-review"
            )
        if suggested_round > last_reviewed:
            print(
                f"ACTION=increment review_round to {suggested_round}; "
                f"set review_status=pending; run /code-review Round {suggested_round}"
            )
        print("RUN=/code-review on review_paths scope; then /receiving-code-review before Phase 8")
    else:
        suggested_round = current_round
        print(f"suggested_review_round={current_round}")
        print("suggested_review_status=skipped")
        print("suggested_code_changed=no")
        skip_reason = f"No diff in window scope ({' '.join(paths)}) this tick"
        print(f"suggested_review_skip_reason={skip_reason}")
        print("ACTION=set code_changed=no; review_status=skipped with reason; skip Phase 6-7")
        updates["code_changed"] = "no"
        updates["review_status"] = "skipped"
        updates["review_skip_reason"] = skip_reason
        updates["review_round"] = str(current_round)

    prefix = rp.LOOP_PREFIX.get(args.loop_id, "rf")
    print(f"finding_id_prefix={prefix}-r{suggested_round if has_diff else current_round}")

    if args.apply:
        new_text = update_checkpoint_fields(state_text, updates)
        state_path.write_text(new_text, encoding="utf-8")
        print("APPLIED=yes")

    print("PREPARE_REVIEW_END")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
