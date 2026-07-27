#!/usr/bin/env python3
"""Git worktree helpers for window instance isolation."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

DEFAULT_BASE_BRANCH = "main"
WORKTREES_DIR = ".worktrees"


def sanitize_item_id(item_id: str) -> str:
    raw = (item_id or "item").strip().strip("`")
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", raw).strip("-")
    return cleaned or "item"


def branch_name(loop_id: str, item_id: str) -> str:
    return f"loop/{loop_id}/{sanitize_item_id(item_id)}"


def worktree_rel_path(loop_id: str) -> str:
    return f"{WORKTREES_DIR}/{loop_id}"


def worktree_abs_path(project_root: Path, loop_id: str) -> Path:
    return (project_root / worktree_rel_path(loop_id)).resolve()


def run_git(
    args: list[str],
    *,
    cwd: Path,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if check and proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {err}")
    return proc


def is_ignored(project_root: Path, rel_path: str) -> bool:
    proc = run_git(["check-ignore", "-q", rel_path], cwd=project_root, check=False)
    return proc.returncode == 0


def list_worktrees(project_root: Path) -> list[dict[str, str]]:
    proc = run_git(["worktree", "list", "--porcelain"], cwd=project_root, check=False)
    if proc.returncode != 0:
        return []
    entries: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in (proc.stdout or "").splitlines():
        if not line.strip():
            if current:
                entries.append(current)
                current = {}
            continue
        if line.startswith("worktree "):
            current["path"] = line.split(" ", 1)[1].strip()
        elif line.startswith("branch "):
            current["branch"] = line.split(" ", 1)[1].strip().removeprefix("refs/heads/")
        elif line == "detached":
            current["branch"] = "detached"
    if current:
        entries.append(current)
    return entries


def worktree_entry(project_root: Path, loop_id: str) -> dict[str, str] | None:
    target = str(worktree_abs_path(project_root, loop_id))
    for entry in list_worktrees(project_root):
        if entry.get("path") == target:
            return entry
    return None


def is_dirty(path: Path) -> bool:
    proc = run_git(["status", "--porcelain"], cwd=path, check=False)
    return proc.returncode == 0 and bool((proc.stdout or "").strip())


def commits_ahead(path: Path, base: str = DEFAULT_BASE_BRANCH) -> int:
    proc = run_git(
        ["rev-list", "--count", f"{base}..HEAD"],
        cwd=path,
        check=False,
    )
    if proc.returncode != 0:
        return 0
    try:
        return int((proc.stdout or "0").strip())
    except ValueError:
        return 0


def branch_exists(project_root: Path, name: str) -> bool:
    proc = run_git(["show-ref", "--verify", f"refs/heads/{name}"], cwd=project_root, check=False)
    return proc.returncode == 0


def create_worktree(
    project_root: Path,
    loop_id: str,
    item_id: str,
    *,
    base_branch: str = DEFAULT_BASE_BRANCH,
) -> dict[str, str]:
    rel = worktree_rel_path(loop_id)
    if not is_ignored(project_root, rel):
        raise RuntimeError(
            f"{rel} is not gitignored — add .worktrees/ to .gitignore before creating worktrees"
        )

    wt_path = worktree_abs_path(project_root, loop_id)
    branch = branch_name(loop_id, item_id)
    existing = worktree_entry(project_root, loop_id)

    if existing:
        existing_branch = existing.get("branch", "")
        if existing_branch == branch:
            return {
                "path": str(wt_path),
                "branch": branch,
                "rel_path": rel,
                "resumed": "yes",
            }
        raise RuntimeError(
            f"worktree already active for {loop_id} on branch {existing_branch}; "
            f"merge/remove before starting {branch}"
        )

    if branch_exists(project_root, branch):
        run_git(["worktree", "add", str(wt_path), branch], cwd=project_root)
    else:
        run_git(["worktree", "add", "-b", branch, str(wt_path), base_branch], cwd=project_root)

    return {
        "path": str(wt_path),
        "branch": branch,
        "rel_path": rel,
        "resumed": "no",
    }


def status_worktree(project_root: Path, loop_id: str) -> dict[str, str]:
    wt_path = worktree_abs_path(project_root, loop_id)
    entry = worktree_entry(project_root, loop_id)
    if not entry:
        return {
            "loop_id": loop_id,
            "status": "none",
            "path": str(wt_path),
            "branch": "",
            "dirty": "no",
            "ahead": "0",
        }
    path = Path(entry.get("path", wt_path))
    branch = entry.get("branch", "")
    return {
        "loop_id": loop_id,
        "status": "active",
        "path": str(path),
        "branch": branch,
        "dirty": "yes" if is_dirty(path) else "no",
        "ahead": str(commits_ahead(path)),
    }


def merge_worktree(
    project_root: Path,
    loop_id: str,
    *,
    base_branch: str = DEFAULT_BASE_BRANCH,
) -> dict[str, str]:
    entry = worktree_entry(project_root, loop_id)
    if not entry:
        raise RuntimeError(f"no active worktree for {loop_id}")

    wt_path = Path(entry["path"])
    branch = entry.get("branch", "")
    if not branch or branch == "detached":
        raise RuntimeError(f"worktree for {loop_id} has no branch")

    if is_dirty(wt_path):
        run_git(["add", "-A"], cwd=wt_path)
        run_git(
            ["commit", "-m", f"chore({loop_id}): close tick before merge"],
            cwd=wt_path,
        )

    run_git(["fetch", "origin", base_branch], cwd=project_root, check=False)
    rebase = run_git(["rebase", base_branch], cwd=wt_path, check=False)
    if rebase.returncode != 0:
        raise RuntimeError(
            f"rebase onto {base_branch} failed — fix conflicts in {wt_path}, "
            f"run git rebase --continue, then retry merge"
        )

    run_git(["checkout", base_branch], cwd=project_root)
    merge = run_git(["merge", "--ff-only", branch], cwd=project_root, check=False)
    if merge.returncode != 0:
        raise RuntimeError(
            f"ff-only merge of {branch} into {base_branch} failed — rebase may be required"
        )

    return {"path": str(wt_path), "branch": branch, "merged": "yes"}


def remove_worktree(project_root: Path, loop_id: str) -> None:
    entry = worktree_entry(project_root, loop_id)
    if not entry:
        return
    wt_path = Path(entry["path"])
    branch = entry.get("branch", "")
    run_git(["worktree", "remove", str(wt_path), "--force"], cwd=project_root, check=False)
    if branch and branch != "detached" and branch_exists(project_root, branch):
        run_git(["branch", "-d", branch], cwd=project_root, check=False)


def prune_worktrees(project_root: Path) -> list[str]:
    removed: list[str] = []
    base = DEFAULT_BASE_BRANCH
    for entry in list_worktrees(project_root):
        path_str = entry.get("path", "")
        branch = entry.get("branch", "")
        if not path_str or f"/{WORKTREES_DIR}/" not in path_str:
            continue
        if not branch or branch == "detached":
            continue
        merged = run_git(
            ["branch", "--merged", base],
            cwd=project_root,
            check=False,
        )
        if merged.returncode == 0 and branch in (merged.stdout or ""):
            run_git(["worktree", "remove", path_str, "--force"], cwd=project_root, check=False)
            run_git(["branch", "-d", branch], cwd=project_root, check=False)
            removed.append(branch)
    return removed
