#!/usr/bin/env python3
"""Per-window review diff scope — paths each loop owns and must review."""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

# Paths each window may change in a tick (review + code_changed detection).
WINDOW_REVIEW_PATHS: dict[str, list[str]] = {
    "worker-relay": ["pwa/", "server/"],
    "ux-relay": ["pwa/"],
    "code-health": ["pwa/", "server/", "tools/cursor-loop/"],
    "po-relay": [
        "docs/window-instances/po-relay/",
        "docs/window-instances/instances.manifest.json",
        "docs/maintenance/",
        "docs/agents/",
        "docs/RELAY.md",
    ],
}

DEFAULT_REVIEW_PATHS = ["pwa/", "server/"]


def review_paths(loop_id: str = "", state_file: str = "") -> list[str]:
    """Return git pathspecs this window owns for Phase 5/6 review."""
    paths = list(WINDOW_REVIEW_PATHS.get(loop_id, DEFAULT_REVIEW_PATHS))
    if state_file:
        bundle = Path(state_file).parent.as_posix().rstrip("/") + "/"
        if bundle not in paths:
            paths.append(bundle)
    seen: set[str] = set()
    out: list[str] = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def git_has_changes(project_root: Path, paths: list[str]) -> bool:
    if not paths:
        return False
    for args in (
        ["git", "diff", "--quiet", "HEAD", "--", *paths],
        ["git", "diff", "--quiet", "--cached", "--", *paths],
    ):
        try:
            r = subprocess.run(args, cwd=project_root, capture_output=True)
            if r.returncode == 1:
                return True
        except OSError:
            return False
    return False


def git_diff_range_label(project_root: Path, paths: list[str]) -> str:
    if not git_has_changes(project_root, paths):
        return "none"
    cached = subprocess.run(
        ["git", "diff", "--quiet", "--cached", "--", *paths],
        cwd=project_root,
        capture_output=True,
    )
    unstaged = subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--", *paths],
        cwd=project_root,
        capture_output=True,
    )
    has_cached = cached.returncode == 1
    has_unstaged = unstaged.returncode == 1
    if has_cached and has_unstaged:
        return "uncommitted (staged + unstaged)"
    if has_cached:
        return "uncommitted (staged)"
    if has_unstaged:
        return "uncommitted"
    return "committed (HEAD)"


def git_diff_stat(project_root: Path, paths: list[str]) -> str:
    lines: list[str] = []
    for args in (
        ["git", "diff", "--stat", "HEAD", "--", *paths],
        ["git", "diff", "--stat", "--cached", "--", *paths],
    ):
        try:
            r = subprocess.run(args, cwd=project_root, capture_output=True, text=True)
            if r.stdout.strip():
                lines.append(r.stdout.strip())
        except OSError:
            pass
    return "\n".join(lines)


def list_changed_files(project_root: Path, paths: list[str]) -> list[str]:
    """Return sorted unique paths changed in scope (staged + unstaged vs HEAD)."""
    if not paths:
        return []
    found: set[str] = set()
    for args in (
        ["git", "diff", "--name-only", "HEAD", "--", *paths],
        ["git", "diff", "--name-only", "--cached", "--", *paths],
    ):
        try:
            r = subprocess.run(args, cwd=project_root, capture_output=True, text=True)
            if r.returncode in (0, 1) and r.stdout.strip():
                for line in r.stdout.splitlines():
                    path = line.strip()
                    if path:
                        found.add(path)
        except OSError:
            pass
    return sorted(found)


def files_fingerprint(files: list[str]) -> str:
    """Stable short hash of sorted changed file list."""
    payload = "\n".join(sorted(files))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def manifest_matches_git(
    project_root: Path,
    paths: list[str],
    stored_files: str,
    stored_fingerprint: str,
) -> tuple[bool, list[str], str]:
    """Return (matches, live_files, live_fingerprint)."""
    live = list_changed_files(project_root, paths)
    live_fp = files_fingerprint(live)
    stored_list = [f for f in (stored_files or "").split() if f and f not in ("—", "-")]
    stored_fp = (stored_fingerprint or "").strip().strip("`")
    if stored_fp and stored_fp not in ("—", "-"):
        if live_fp != stored_fp:
            return False, live, live_fp
    if stored_list and set(stored_list) != set(live):
        return False, live, live_fp
    return True, live, live_fp


def main() -> int:
    parser = argparse.ArgumentParser(description="Window-scoped review diff detection")
    parser.add_argument("project", nargs="?", default=".", help="Project root")
    parser.add_argument("--loop-id", default="", help="Window loop_id")
    parser.add_argument("--state-file", default="", help="Relative STATE.md path")
    parser.add_argument("--stat", action="store_true", help="Print diff stat on change")
    args = parser.parse_args()

    root = Path(args.project).resolve()
    paths = review_paths(args.loop_id, args.state_file)
    changed = list_changed_files(root, paths)
    fingerprint = files_fingerprint(changed)
    if git_has_changes(root, paths):
        print("CODE_CHANGED=yes")
        print(f"review_paths={' '.join(paths)}")
        print(f"review_diff_range={git_diff_range_label(root, paths)}")
        print(f"changed_files={' '.join(changed)}")
        print(f"review_fingerprint={fingerprint}")
        if args.stat:
            stat = git_diff_stat(root, paths)
            if stat:
                print(stat)
        return 1
    print("CODE_CHANGED=no")
    print(f"review_paths={' '.join(paths)}")
    print("changed_files=")
    print(f"review_fingerprint={fingerprint}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
