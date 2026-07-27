"""Shared helpers for cursor-loop Cursor hooks."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

PACKAGE_VERSION = "0.2.0"

LOOP_CONFIG_KEYS = frozenset(
    {
        "loop_id",
        "contract_doc",
        "sentinel",
        "wake_sentinel",
        "interval_sec",
        "monitor_regex",
        "loop_script",
        "pidfile",
        "state_file",
    }
)

REQUIRED_MANIFEST_KEYS = ("package_root", "contracts_dir")


def load_manifest(root: Path) -> dict:
    manifest_path = root / ".cursor" / "cursor-loop.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(
            f"Missing manifest: {manifest_path}. Run install.sh in the project root."
        )
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise ValueError(f"Invalid manifest {manifest_path}: {exc}") from exc

    missing = [k for k in REQUIRED_MANIFEST_KEYS if not data.get(k)]
    if missing:
        raise ValueError(f"Manifest missing required keys: {', '.join(missing)}")

    data.setdefault("version", PACKAGE_VERSION)
    data.setdefault("contract_globs", [])
    data.setdefault("binding_ttl_days", 30)
    return data


def workspace_root(payload: dict) -> Path | None:
    for wr in payload.get("workspace_roots") or []:
        root = Path(wr)
        manifest = root / ".cursor" / "cursor-loop.json"
        if manifest.is_file():
            return root
    return None


def scripts_dir(root: Path, manifest: dict) -> Path:
    path = root / manifest["package_root"] / "scripts"
    if not (path / "loop_hook_lib.py").is_file():
        raise FileNotFoundError(f"cursor-loop scripts not found at {path}")
    return path


def contract_pattern(contracts_dir: str) -> re.Pattern[str]:
    escaped = re.escape(contracts_dir.strip("/"))
    return re.compile(
        rf"@?(({escaped}/[\w.-]+\.md))",
        re.IGNORECASE,
    )


def _loop_config_section(text: str) -> str:
    if "## Loop config" not in text:
        return ""
    section = text.split("## Loop config", 1)[1]
    if "\n## " in section:
        section = section.split("\n## ", 1)[0]
    return section


def has_loop_config(text: str) -> bool:
    return bool(_loop_config_section(text).strip())


def find_contract_paths(prompt: str, root: Path, manifest: dict) -> list[str]:
    found: set[str] = set()
    contracts_dir = manifest["contracts_dir"]

    for match in contract_pattern(contracts_dir).finditer(prompt):
        found.add(match.group(1))

    for match in re.finditer(r"@?((?:[\w.-]+/)+[\w.-]+\.md)", prompt, re.IGNORECASE):
        rel = match.group(1)
        doc_path = root / rel
        if doc_path.is_file() and has_loop_config(doc_path.read_text(encoding="utf-8")):
            found.add(rel)

    for pattern in manifest.get("contract_globs") or []:
        glob = pattern.lstrip("@")
        if glob in prompt or f"@{glob}" in prompt:
            for path in root.glob(glob):
                if path.is_file() and path.suffix == ".md":
                    rel = str(path.relative_to(root))
                    if has_loop_config(path.read_text(encoding="utf-8")):
                        found.add(rel)

    return sorted(found)


def parse_loop_config(text: str) -> dict[str, str]:
    cfg: dict[str, str] = {}
    section = _loop_config_section(text)
    if not section:
        return cfg
    for line in section.splitlines():
        if "|" not in line or "`" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3:
            continue
        key = parts[1].strip()
        val = parts[2].strip().strip("`")
        if key in LOOP_CONFIG_KEYS:
            cfg[key] = val
    return cfg


def binding_path(root: Path, conversation_id: str) -> Path:
    return root / ".cursor" / "loop-bindings" / f"{conversation_id}.json"


def read_binding(root: Path, conversation_id: str) -> dict | None:
    path = binding_path(root, conversation_id)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def write_binding(root: Path, conversation_id: str, data: dict) -> None:
    path = binding_path(root, conversation_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    data.setdefault("schema_version", 1)
    data["updated_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def binding_age_days(binding: dict) -> float | None:
    raw = binding.get("updated_at") or binding.get("created_at")
    if not raw:
        return None
    try:
        updated = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - updated).total_seconds() / 86400


def cleanup_stale_bindings(
    root: Path,
    manifest: dict,
    *,
    dry_run: bool = False,
) -> list[str]:
    """Remove bindings older than binding_ttl_days. Returns deleted conversation ids."""
    bindings_dir = root / ".cursor" / "loop-bindings"
    if not bindings_dir.is_dir():
        return []

    ttl_days = int(manifest.get("binding_ttl_days") or 30)
    cutoff = timedelta(days=ttl_days)
    now = datetime.now(timezone.utc)
    removed: list[str] = []

    for path in bindings_dir.glob("*.json"):
        if path.name.startswith("."):
            continue
        try:
            binding = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            if not dry_run:
                path.unlink(missing_ok=True)
            removed.append(path.stem)
            continue

        raw = binding.get("updated_at") or binding.get("created_at")
        if raw:
            try:
                updated = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
                if updated.tzinfo is None:
                    updated = updated.replace(tzinfo=timezone.utc)
                age = now - updated
            except ValueError:
                age = cutoff + timedelta(seconds=1)
        else:
            age = cutoff + timedelta(seconds=1)

        if age > cutoff:
            if not dry_run:
                path.unlink(missing_ok=True)
            removed.append(path.stem)

    return removed


def maybe_cleanup_bindings(root: Path, manifest: dict) -> None:
    """Lightweight opportunistic cleanup — runs at most once per 24h per project."""
    stamp = root / ".cursor" / "loop-bindings" / ".last_cleanup"
    now = datetime.now(timezone.utc)
    if stamp.is_file():
        try:
            last = datetime.fromisoformat(stamp.read_text(encoding="utf-8").strip())
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            if (now - last) < timedelta(hours=24):
                return
        except ValueError:
            pass
    cleanup_stale_bindings(root, manifest)
    stamp.parent.mkdir(parents=True, exist_ok=True)
    stamp.write_text(now.replace(microsecond=0).isoformat() + "\n", encoding="utf-8")


def is_stop_request(prompt: str) -> bool:
    return bool(re.search(r"\bstop\s+(the\s+)?loop\b|\bstop\s+working\b", prompt, re.I))


def is_keep_working_request(prompt: str) -> bool:
    return bool(re.search(r"\bkeep\s+working\b", prompt, re.I))


def resolve_loop_script(root: Path, manifest: dict, cfg: dict) -> str:
    script = cfg.get("loop_script") or f"{manifest['package_root']}/scripts/agent-loop.sh"
    script_path = Path(script)
    if not script_path.is_absolute():
        script_path = root / script
    if not script_path.is_file():
        raise FileNotFoundError(f"loop_script not found: {script_path}")
    if script_path.is_absolute():
        return str(script_path)
    return str(script_path.relative_to(root))


def resolve_pidfile_path(loop_id: str, cfg: dict | None = None) -> Path:
    tmp = Path(os.environ.get("TMPDIR") or "/tmp")
    cfg = cfg or {}
    custom = (cfg.get("pidfile") or "").strip()
    if custom:
        path = Path(custom)
        if path.is_absolute():
            return path
        return tmp / path.name
    return tmp / f"cursor-loop-{loop_id}.pid"


def build_binding(root: Path, manifest: dict, rel: str, cfg: dict) -> dict:
    loop_id = cfg["loop_id"]
    pidfile = resolve_pidfile_path(loop_id, cfg)
    return {
        "loop_id": loop_id,
        "contract_doc": cfg.get("contract_doc") or rel,
        "sentinel": cfg.get("sentinel", ""),
        "interval_sec": cfg.get("interval_sec", ""),
        "loop_script": resolve_loop_script(root, manifest, cfg),
        "pidfile": str(pidfile),
        "stopped": False,
    }
