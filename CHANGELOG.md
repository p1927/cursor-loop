# Changelog

## 0.3.0

- **force-reset.sh** — nuclear cleanup (`--all`, `--loop-id`, `--kill`, `--bindings`, `--locks`)
- **loop_id lock** — one chat per loop_id; bind blocked if another chat owns it
- **validate_contracts.py** — duplicate loop_id/sentinel detection
- **verify-loop.sh** — agent must run before end of turn (enforced in rule)
- **daily-maintenance.sh** — cleanup + status + validate
- Stricter **agent-loop-contract.mdc** — end-of-turn gate checklist
- Survival hook warns at turn 20/25; releases lock on stop
- Contract docs trimmed — arming/survival only in rule

## 0.2.0

- `ARCHITECTURE.md` — system design reference
- `examples/minimal-project/` — smallest consumer setup
- `install-remote.sh` — curl one-liner install
- Binding TTL: `binding_ttl_days` in manifest, `updated_at` on bindings
- `cleanup_bindings.py` + opportunistic prune in bind hook
- Cron example in ARCHITECTURE.md

## 0.1.0

- Initial standalone release
- Manifest-driven hook bootstrap (`package_root`, `contracts_dir`)
- Python hook entrypoints (`hook_bind.py`, `hook_survival.py`)
- Stop flow: `stopped` flag on binding; survival hook respects it
- `install.sh`: `--symlink`, `--copy`, `--package-path`, `--contracts-dir`, `--uninstall`
- Idempotent `hooks.json` merge via `merge_hooks.py`
- JSON-safe tick payloads in `agent-loop.sh`
- `loop-status.sh --json` and `--loop-id`
- `doctor.sh` health check
