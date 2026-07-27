"""Shared helpers for cursor-loop Cursor hooks."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

PACKAGE_VERSION = "0.5.0"

VALID_LOOP_MODES = frozenset({"dynamic", "persistent", "external"})
DEFAULT_LOOP_MODE = "dynamic"

SURVIVAL_TURN_WARN = 20
SURVIVAL_TURN_LIMIT = 25

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
        "loop_mode",
    }
)

REQUIRED_MANIFEST_KEYS = ("package_root",)


def resolve_state_dir(manifest: dict) -> str:
    return manifest.get("state_dir") or manifest.get("contracts_dir") or "docs/window-instances"


def resolve_instances_manifest_path(root: Path, manifest: dict) -> Path:
    rel = manifest.get("instances_manifest")
    if rel:
        return root / rel
    state_dir = resolve_state_dir(manifest)
    return root / state_dir / "instances.manifest.json"


def load_instances_manifest(root: Path, manifest: dict | None = None) -> dict:
    if manifest is None:
        manifest = load_manifest(root)
    path = resolve_instances_manifest_path(root, manifest)
    if not path.is_file():
        return {"version": 1, "instances": []}
    return json.loads(path.read_text(encoding="utf-8"))


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
    data.setdefault("contracts_dir", resolve_state_dir(data))
    data.setdefault("state_dir", resolve_state_dir(data))
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


def resolve_wake_pidfile_path(loop_id: str) -> Path:
    tmp = Path(os.environ.get("TMPDIR") or "/tmp")
    return tmp / f"cursor-loop-{loop_id}.wake.pid"


def resolve_last_exit_path(loop_id: str) -> Path:
    tmp = Path(os.environ.get("TMPDIR") or "/tmp")
    return tmp / f"cursor-loop-{loop_id}.last_exit"


def normalize_loop_mode(cfg: dict) -> str:
    mode = (cfg.get("loop_mode") or DEFAULT_LOOP_MODE).strip().lower()
    if mode not in VALID_LOOP_MODES:
        return DEFAULT_LOOP_MODE
    return mode


def build_binding(root: Path, manifest: dict, rel: str, cfg: dict) -> dict:
    loop_id = cfg["loop_id"]
    pidfile = resolve_pidfile_path(loop_id, cfg)
    loop_mode = normalize_loop_mode(cfg)
    return {
        "loop_id": loop_id,
        "contract_doc": cfg.get("contract_doc") or rel,
        "state_file": cfg.get("state_file", ""),
        "loop_mode": loop_mode,
        "sentinel": cfg.get("sentinel", ""),
        "wake_sentinel": cfg.get("wake_sentinel", ""),
        "interval_sec": cfg.get("interval_sec", ""),
        "monitor_regex": cfg.get("monitor_regex", ""),
        "loop_script": resolve_loop_script(root, manifest, cfg),
        "pidfile": str(pidfile),
        "wake_pidfile": str(resolve_wake_pidfile_path(loop_id)),
        "stopped": False,
        "survival_turns": 0,
        "recovery_turns": 0,
    }


def loop_lock_path(root: Path, loop_id: str) -> Path:
    return root / ".cursor" / "loop-bindings" / "locks" / f"{loop_id}.json"


def read_loop_lock(root: Path, loop_id: str) -> dict | None:
    path = loop_lock_path(root, loop_id)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def acquire_loop_lock(
    root: Path,
    loop_id: str,
    conversation_id: str,
    contract_doc: str,
) -> tuple[bool, str | None]:
    """One loop_id per chat. Returns (ok, error_message)."""
    path = loop_lock_path(root, loop_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    if path.is_file():
        try:
            lock = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            lock = {}
        owner = lock.get("conversation_id")
        if owner and owner != conversation_id:
            return (
                False,
                f"loop_id '{loop_id}' is already active in another chat "
                f"(conversation {owner[:12]}…). "
                f"Use one window per loop_id, or run force-reset.sh --all",
            )

    path.write_text(
        json.dumps(
            {
                "loop_id": loop_id,
                "conversation_id": conversation_id,
                "contract_doc": contract_doc,
                "updated_at": now,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return True, None


def release_loop_lock(root: Path, loop_id: str, conversation_id: str) -> None:
    path = loop_lock_path(root, loop_id)
    if not path.is_file():
        return
    try:
        lock = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        path.unlink(missing_ok=True)
        return
    if lock.get("conversation_id") == conversation_id:
        path.unlink(missing_ok=True)


def iter_contract_files(root: Path, manifest: dict) -> list[Path]:
    seen: set[Path] = set()
    files: list[Path] = []

    def add(path: Path) -> None:
        resolved = path.resolve()
        if resolved in seen or not path.is_file():
            return
        text = path.read_text(encoding="utf-8")
        if has_loop_config(text):
            seen.add(resolved)
            files.append(path)

    contracts_dir = root / resolve_state_dir(manifest)
    if contracts_dir.is_dir():
        for path in sorted(contracts_dir.glob("*.md")):
            add(path)

    for pattern in manifest.get("contract_globs") or []:
        for path in sorted(root.glob(pattern)):
            if "/_template/" in str(path.as_posix()):
                continue
            if path.suffix == ".md":
                add(path)

    return sorted(files, key=lambda p: str(p.relative_to(root)))


def validate_all_contracts(root: Path, manifest: dict) -> list[str]:
    """Return list of error messages (empty = ok)."""
    errors: list[str] = []
    loop_ids: dict[str, str] = {}
    sentinels: dict[str, str] = {}

    for path in iter_contract_files(root, manifest):
        rel = str(path.relative_to(root))
        cfg = parse_loop_config(path.read_text(encoding="utf-8"))
        loop_id = cfg.get("loop_id")
        sentinel = cfg.get("sentinel")

        if not loop_id:
            errors.append(f"{rel}: missing loop_id")
            continue
        if loop_id in loop_ids:
            errors.append(
                f"duplicate loop_id '{loop_id}' in {rel} and {loop_ids[loop_id]}"
            )
        else:
            loop_ids[loop_id] = rel

        if sentinel:
            if sentinel in sentinels:
                errors.append(
                    f"duplicate sentinel '{sentinel}' in {rel} and {sentinels[sentinel]}"
                )
            else:
                sentinels[sentinel] = rel

        script = cfg.get("loop_script") or f"{manifest['package_root']}/scripts/agent-loop.sh"
        script_path = root / script if not Path(script).is_absolute() else Path(script)
        if not script_path.is_file():
            errors.append(f"{rel}: loop_script not found: {script}")

        mode = (cfg.get("loop_mode") or DEFAULT_LOOP_MODE).strip().lower()
        if mode and mode not in VALID_LOOP_MODES:
            errors.append(f"{rel}: invalid loop_mode '{mode}' (use dynamic|persistent|external)")

        wake = cfg.get("wake_sentinel") or ""
        if mode == "dynamic" and not wake:
            errors.append(f"{rel}: loop_mode dynamic requires wake_sentinel")

    return errors


def is_loop_process_alive(pidfile: Path) -> bool:
    if not pidfile.is_file():
        return False
    try:
        pid = int(pidfile.read_text(encoding="utf-8").strip())
        os.kill(pid, 0)
        return True
    except (ValueError, ProcessLookupError, PermissionError, OSError):
        return False


def kill_loop_process(pidfile: Path) -> bool:
    if not pidfile.is_file():
        return False
    try:
        pid = int(pidfile.read_text(encoding="utf-8").strip())
        os.kill(pid, 15)
        return True
    except (ValueError, ProcessLookupError, PermissionError, OSError):
        return False


def is_wake_process_alive(loop_id: str, binding: dict | None = None) -> bool:
    path = (
        Path(binding["wake_pidfile"])
        if binding and binding.get("wake_pidfile")
        else resolve_wake_pidfile_path(loop_id)
    )
    return is_loop_process_alive(path)


def kill_wake_process(loop_id: str, binding: dict | None = None) -> bool:
    path = (
        Path(binding["wake_pidfile"])
        if binding and binding.get("wake_pidfile")
        else resolve_wake_pidfile_path(loop_id)
    )
    killed = kill_loop_process(path)
    path.unlink(missing_ok=True)
    return killed


def write_last_exit(loop_id: str, reason: str = "SIGTERM") -> None:
    path = resolve_last_exit_path(loop_id)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    path.write_text(f"{now} {reason}\n", encoding="utf-8")
