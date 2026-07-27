#!/usr/bin/env python3
"""Materialize project window instances from a package preset."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

CONTRACT_FILES = ("INSTANCE.md", "IDENTITY.md", "RITUAL.md")


def find_project_root(start: Path) -> Path:
    cur = start.resolve()
    for _ in range(20):
        if (cur / ".cursor" / "cursor-loop.json").is_file():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    raise SystemExit(f"No .cursor/cursor-loop.json found from {start}")


def load_cursor_manifest(root: Path) -> dict:
    return json.loads((root / ".cursor" / "cursor-loop.json").read_text(encoding="utf-8"))


def package_window_instances(root: Path, manifest: dict) -> Path:
    return root / manifest["package_root"] / "window-instances"


def subst_state(template: str, loop_id: str) -> str:
    upper = loop_id.upper().replace("-", "_")
    return (
        template.replace("{{loop_id}}", loop_id)
        .replace("{{sentinel_tick}}", f"AGENT_LOOP_TICK_{upper}")
        .replace("{{sentinel_wake}}", f"AGENT_LOOP_WAKE_{upper}")
    )


def link_or_copy(src: Path, dest: Path, mode: str, refresh: bool) -> None:
    if dest.exists() or dest.is_symlink():
        if not refresh:
            return
        dest.unlink()
    if mode == "copy":
        shutil.copy2(src, dest)
    else:
        dest.symlink_to(src.resolve())


def bootstrap(
    root: Path,
    preset: str,
    mode: str = "symlink",
    refresh: bool = False,
) -> dict:
    cursor = load_cursor_manifest(root)
    wi_root = package_window_instances(root, cursor)
    preset_dir = wi_root / "presets" / preset
    preset_manifest_path = preset_dir / "instances.manifest.json"
    if not preset_manifest_path.is_file():
        raise SystemExit(f"Preset not found: {preset_manifest_path}")

    preset_data = json.loads(preset_manifest_path.read_text(encoding="utf-8"))
    state_dir = Path(cursor.get("state_dir") or "docs/window-instances")
    if not state_dir.is_absolute():
        state_dir = root / state_dir
    state_dir.mkdir(parents=True, exist_ok=True)

    template_state = (wi_root / "_template" / "STATE.md").read_text(encoding="utf-8")

    template_dest = state_dir / "_template"
    template_src = wi_root / "_template"
    if template_src.is_dir():
        if template_dest.exists() or template_dest.is_symlink():
            if refresh:
                if template_dest.is_symlink():
                    template_dest.unlink()
                elif template_dest.is_dir():
                    shutil.rmtree(template_dest)
        if not template_dest.exists():
            if mode == "copy":
                shutil.copytree(template_src, template_dest)
            else:
                template_dest.symlink_to(template_src.resolve(), target_is_directory=True)

    project_instances: list[dict] = []

    for entry in preset_data.get("instances") or []:
        loop_id = entry["loop_id"]
        bundle_dir = state_dir / loop_id
        bundle_dir.mkdir(parents=True, exist_ok=True)
        preset_bundle = preset_dir / loop_id

        for name in CONTRACT_FILES:
            src = preset_bundle / name
            if not src.is_file():
                raise SystemExit(f"Missing preset file: {src}")
            link_or_copy(src, bundle_dir / name, mode, refresh)

        state_path = bundle_dir / "STATE.md"
        if not state_path.exists():
            state_path.write_text(subst_state(template_state, loop_id), encoding="utf-8")

        bundle_rel = bundle_dir.relative_to(root).as_posix()
        project_instances.append(
            {
                **entry,
                "bundle": bundle_rel,
                "contract_doc": f"{bundle_rel}/INSTANCE.md",
                "state_file": f"{bundle_rel}/STATE.md",
            }
        )

    project_manifest = {
        "version": preset_data.get("version", 1),
        "preset": preset,
        "instances": project_instances,
    }
    manifest_out = state_dir / "instances.manifest.json"
    manifest_out.write_text(json.dumps(project_manifest, indent=2) + "\n", encoding="utf-8")

    cursor["instances_preset"] = preset
    cursor["instances_manifest"] = manifest_out.relative_to(root).as_posix()
    cursor["state_dir"] = state_dir.relative_to(root).as_posix()
    cursor["contracts_dir"] = cursor["state_dir"]
    globs = cursor.get("contract_globs") or []
    glob_pattern = f"{cursor['state_dir']}/*/INSTANCE.md"
    if glob_pattern not in globs:
        globs.append(glob_pattern)
    cursor["contract_globs"] = globs
    (root / ".cursor" / "cursor-loop.json").write_text(
        json.dumps(cursor, indent=2) + "\n", encoding="utf-8"
    )

    return project_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap window instances from preset")
    parser.add_argument("project", nargs="?", default=".", help="Project root")
    parser.add_argument("--preset", required=True, help="Preset name (e.g. habits-pwa, four-window)")
    parser.add_argument("--mode", choices=("symlink", "copy"), default="symlink")
    parser.add_argument("--refresh", action="store_true", help="Replace existing contract files")
    args = parser.parse_args()

    root = find_project_root(Path(args.project))
    result = bootstrap(root, args.preset, args.mode, args.refresh)
    count = len(result.get("instances") or [])
    print(f"OK — bootstrapped {count} instance(s) from preset '{args.preset}' into {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
