#!/usr/bin/env python3
"""Validate Window Instance bundles and instances.manifest.json."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import loop_hook_lib as mod

REQUIRED_BUNDLE_FILES = ("INSTANCE.md", "IDENTITY.md", "RITUAL.md", "STATE.md")
REQUIRED_STATE_SECTIONS = (
    "LAST_REVIEW",
    "CHECKPOINT",
    "IN_PROGRESS",
    "REVIEW_FINDINGS",
    "HISTORY",
)
REQUIRED_CHECKPOINT_FIELDS = ("phase", "review_status")
V2_CHECKPOINT_FIELDS = ("review_round", "code_changed")
VALID_ARCHETYPES = frozenset({"engineer", "designer", "product", "qa"})
VALID_SEVERITIES = frozenset({"critical", "high", "medium", "low"})
VALID_ACTIONS = frozenset({"fix-now", "backlog", "closed", "pushback", "open", "—", "-"})


def load_instances_manifest(root: Path) -> dict:
    try:
        manifest = mod.load_manifest(root)
    except (FileNotFoundError, ValueError):
        legacy = root / "docs/window-instances/instances.manifest.json"
        if legacy.is_file():
            return json.loads(legacy.read_text(encoding="utf-8"))
        return {"version": 1, "instances": []}
    return mod.load_instances_manifest(root, manifest)


def parse_review_findings_rows(state_text: str) -> list[dict[str, str]]:
    if "## REVIEW_FINDINGS" not in state_text:
        return []
    section = state_text.split("## REVIEW_FINDINGS", 1)[1]
    if "\n## " in section:
        section = section.split("\n## ", 1)[0]
    rows: list[dict[str, str]] = []
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 9:
            continue
        cells = parts[1:-1]
        if len(cells) < 7:
            continue
        header = cells[0].lower()
        if header in ("id", "----"):
            continue
        if cells[0] in ("—", "-", ""):
            continue
        rows.append(
            {
                "id": cells[0],
                "severity": cells[1],
                "action": cells[4],
            }
        )
    return rows


def instance_version_from_bundle(bundle: Path) -> int:
    instance_path = bundle / "INSTANCE.md"
    if not instance_path.is_file():
        return 1
    cfg = mod.parse_loop_config(instance_path.read_text(encoding="utf-8"))
    raw = cfg.get("instance_version", "1")
    try:
        return int(str(raw).strip("`"))
    except ValueError:
        return 1


def validate_bundle(root: Path, bundle_rel: str, entry: dict) -> list[str]:
    errors: list[str] = []
    warnings: list[str] = []
    bundle = root / bundle_rel
    loop_id = entry.get("loop_id", "")
    version = instance_version_from_bundle(bundle)

    for name in REQUIRED_BUNDLE_FILES:
        if not (bundle / name).is_file():
            errors.append(f"{loop_id}: missing {bundle_rel}/{name}")

    state_path = bundle / "STATE.md"
    if state_path.is_file():
        state_text = state_path.read_text(encoding="utf-8")
        for section in REQUIRED_STATE_SECTIONS:
            if f"## {section}" not in state_text:
                errors.append(f"{loop_id}: STATE.md missing section ## {section}")
        checkpoint_lower = state_text.lower()
        for field in REQUIRED_CHECKPOINT_FIELDS:
            if field not in checkpoint_lower:
                errors.append(f"{loop_id}: CHECKPOINT missing field {field}")
        if version >= 2:
            for field in V2_CHECKPOINT_FIELDS:
                if field not in checkpoint_lower:
                    warnings.append(f"{loop_id}: CHECKPOINT missing v2 field {field}")
        if "REVIEW_FINDINGS" in state_text and "| severity |" not in state_text:
            errors.append(f"{loop_id}: REVIEW_FINDINGS missing schema table header")
        for row in parse_review_findings_rows(state_text):
            sev = row["severity"].lower()
            if sev and sev not in VALID_SEVERITIES:
                errors.append(
                    f"{loop_id}: REVIEW_FINDINGS row {row['id']} invalid severity '{sev}'"
                )
            action = row["action"].lower()
            if action and action not in VALID_ACTIONS:
                errors.append(
                    f"{loop_id}: REVIEW_FINDINGS row {row['id']} invalid action '{action}'"
                )

    instance_path = bundle / "INSTANCE.md"
    if instance_path.is_file():
        cfg = mod.parse_loop_config(instance_path.read_text(encoding="utf-8"))
        if not cfg.get("loop_id"):
            errors.append(f"{loop_id}: INSTANCE.md missing loop_id in Loop config")
        elif cfg["loop_id"] != loop_id:
            errors.append(
                f"{loop_id}: INSTANCE loop_id '{cfg['loop_id']}' != manifest '{loop_id}'"
            )
        for key in ("state_file", "contract_doc"):
            if not cfg.get(key):
                errors.append(f"{loop_id}: INSTANCE.md missing {key}")
        archetype = entry.get("archetype") or cfg.get("archetype", "")
        if archetype and archetype not in VALID_ARCHETYPES:
            errors.append(f"{loop_id}: invalid archetype '{archetype}'")

    ritual_path = bundle / "RITUAL.md"
    if ritual_path.is_file():
        ritual = ritual_path.read_text(encoding="utf-8")
        if "Phase" not in ritual and "phase" not in ritual.lower():
            if "RITUAL.base" not in ritual and "9" not in ritual:
                errors.append(f"{loop_id}: RITUAL.md should reference 9-phase ritual")
        if version >= 2:
            if "/code-review" not in ritual:
                warnings.append(f"{loop_id}: RITUAL.md should reference /code-review")
            if "/receiving-code-review" not in ritual:
                warnings.append(f"{loop_id}: RITUAL.md should reference /receiving-code-review")

    for w in warnings:
        print(f"WARN: {w}", file=sys.stderr)
    return errors


def validate_manifest_entry(root: Path, entry: dict, loop_ids: dict[str, str]) -> list[str]:
    errors: list[str] = []
    loop_id = entry.get("loop_id")
    if not loop_id:
        errors.append("manifest entry missing loop_id")
        return errors

    if loop_id in loop_ids:
        errors.append(f"duplicate loop_id '{loop_id}' in manifest")
    else:
        loop_ids[loop_id] = entry.get("bundle", "")

    for key in ("bundle", "contract_doc", "state_file", "archetype"):
        if not entry.get(key):
            errors.append(f"{loop_id}: manifest missing {key}")

    bundle_rel = entry.get("bundle", "")
    contract = entry.get("contract_doc", "")
    state = entry.get("state_file", "")

    if contract and not (root / contract).is_file():
        errors.append(f"{loop_id}: contract_doc not found: {contract}")
    if state and not (root / state).is_file():
        errors.append(f"{loop_id}: state_file not found: {state}")

    if bundle_rel:
        errors.extend(validate_bundle(root, bundle_rel, entry))

    return errors


def validate_all_instances(root: Path) -> list[str]:
    manifest = load_instances_manifest(root)
    errors: list[str] = []
    loop_ids: dict[str, str] = {}
    sentinels: dict[str, str] = {}

    for entry in manifest.get("instances") or []:
        errors.extend(validate_manifest_entry(root, entry, loop_ids))
        loop_id = entry.get("loop_id", "")
        for sentinel_key in ("sentinel", "wake_sentinel"):
            sentinel = entry.get(sentinel_key, "")
            if sentinel:
                if sentinel in sentinels:
                    errors.append(
                        f"duplicate {sentinel_key} '{sentinel}' "
                        f"for {loop_id} and {sentinels[sentinel]}"
                    )
                else:
                    sentinels[sentinel] = loop_id

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Window Instance bundles")
    parser.add_argument("project", nargs="?", default=".", help="Project root")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument(
        "--strict-review",
        action="store_true",
        help="Fail if ritual gate fails for any instance STATE",
    )
    args = parser.parse_args()

    root = Path(args.project).resolve()
    errors = validate_all_instances(root)

    if args.strict_review:
        import subprocess

        manifest = load_instances_manifest(root)
        gate_script = root / "tools/cursor-loop/scripts/validate_ritual_gate.py"
        if not gate_script.is_file():
            try:
                pkg = mod.load_manifest(root)["package_root"]
                gate_script = root / pkg / "scripts/validate_ritual_gate.py"
            except (FileNotFoundError, ValueError, KeyError):
                pass
        for entry in manifest.get("instances") or []:
            loop_id = entry.get("loop_id", "")
            state_file = entry.get("state_file", "")
            if not loop_id or not state_file:
                continue
            r = subprocess.run(
                [
                    "python3",
                    str(gate_script),
                    "--project",
                    str(root),
                    "--loop-id",
                    loop_id,
                    "--state-file",
                    state_file,
                    "--mode",
                    "arm",
                ],
                cwd=root,
                capture_output=True,
                text=True,
            )
            if r.returncode != 0:
                detail = (r.stderr or r.stdout or "").strip().splitlines()
                msg = detail[0] if detail else "ritual gate failed"
                errors.append(f"{loop_id}: {msg}")

    manifest = load_instances_manifest(root)
    count = len(manifest.get("instances") or [])

    if args.json:
        print(json.dumps({"ok": not errors, "errors": errors, "count": count}, indent=2))
    elif errors:
        print("Instance validation FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
    else:
        print(f"OK — {count} instance(s) validated")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
