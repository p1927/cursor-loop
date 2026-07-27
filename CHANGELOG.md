# Changelog

## 0.5.2

- **Strict phase line** — `ritual_phase.py` state machine; phases 1→9 sequential, no jumps
- **`validate_ritual_gate.py`** — hard block at `arm-wake.sh` and `checkpoint-loop.py --product` with guided `allowed_phase`
- **Wake prompt** — always `allowed_phase=1-wake`; includes phase line + mandatory_commands
- **`stop-tests.sh`** — kill hung `run-all.sh` / pytest runners
- **`detect_code_changed.sh`** — Phase 5 git diff helper
- **Doctor/validate** — fix round-0 review bypass; `--strict-review` flag

## 0.5.1

- **Dynamic-only enforcement** — agent-loop-contract forbids `agent-loop.sh` in dynamic mode; persistent loops reported as STALE in `loop-status` / `instance-doctor`
- **`cwin sync`** — re-link rules, bootstrap preset, kill stale loops (run after `git pull`)
- **Worker interval** — habits-pwa worker-relay 60s → 120s (fewer false DOWN windows during long turns)
- **Stop-hook** — recovery message says never start `agent-loop.sh` in dynamic mode

## 0.4.0

- **Dynamic wake default** (`loop_mode: dynamic`) — `arm-wake.sh` one-shot sleeper per turn instead of persistent `while true` (avoids ~35s SIGTERM)
- **`verify-wake.sh`** — check dynamic wake pidfile alive
- **`checkpoint-loop.sh`** — product/infra checkpoint with `--product`, `--blocker`, `--infra-only`
- **`build_wake_prompt.py`** — JSON wake payloads from contract paths
- **`refresh-loops.sh`** — stop legacy + cursor-loop processes; preserve bindings
- **`force-reset.sh --all`** requires **`--yes`**; clears wake pidfiles
- **Work-first recovery** — survival hook + rule forbid infra-only re-arm turns
- **`hook_survival.py`** — dynamic wake DOWN check; deliverable-first followup
- Contract **`monitor_regex`** → `^AGENT_LOOP_WAKE_*` for dynamic mode
- **`loop-status.sh`** — reports persistent + dynamic wake state

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
