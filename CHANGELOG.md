# Changelog

## 0.5.8

- **`--mode steady`** — `validate_instance.py --strict-review` accepts completed `phase=9-arm` between ticks
- **Arm recovery** — `phase=9-arm` normalizes to `8-close` for `arm-wake.sh` gate (prior cycle complete)
- **`prepare_select_tick.sh`** — Phase 3 worktree requirement detection by archetype + IN_PROGRESS
- **`instance_worktree.sh create --state-file`** — auto-patches CHECKPOINT worktree fields
- **Phase 4–7 gate** — engineer/designer/qa require active worktree when item selected
- **`git_root_for_checkpoint`** — review diff scoped to active worktree path
- **Wake JSON** — `worktree_command` when worktree required; doctor warns on main-scope diff without worktree
- **Live STATE** — consolidated CHECKPOINT tables (worktree fields inline)

## 0.5.7

- **Git-derived file manifest** — `list_changed_files`, `files_fingerprint`, `manifest_matches_git` in `review_scope.py`
- **`prepare_review_tick.sh --apply`** — writes `review_changed_files` + `review_fingerprint` to CHECKPOINT
- **Hard gates** — manifest must match live git at Phase 8; rejects sentinel-only review when changed files exist
- **Stop hook review gate** — `review_stop_needed()` emits followup at Phase 5+ even when wake=ARMED, with enumerated `changed_files`
- **Wake JSON** — includes `review_paths`, `changed_files`, `review_fingerprint`, `review_diff_range`
- **Templates + commands synced** — `_template` STATE/SPEC/RITUAL, `/code-review`, `/receiving-code-review`, 8 presets, live `docs/window-instances/*`
- **Tests** — manifest, gate, stop hook, `--apply` segments

## 0.5.6

- **Mandatory review skills** — Phase 6 must invoke `/code-review` command (read full file); Phase 7a must read Superpowers **receiving-code-review** skill then `/receiving-code-review`
- **Phase 7b Backlog reflect** — deferred/low-priority findings must become backlog rows with id + AC + `backlog_ref`; gated in `ritual_phase.py`
- **Wake prompt** — notes for skill + 7b when git diff present
- **Templates + live instances synced** — `_template`, 8 presets, `docs/window-instances/*`; fixed corrupted RITUAL headers from worktree batch

## 0.5.5

- **Git worktree isolation** — per-window worktrees at `.worktrees/<loop_id>/`, branch `loop/<loop_id>/<item-id>`
- **`instance_worktree.sh`** — create | status | merge | remove | prune (rebase + ff-only merge)
- **Phase gates** — cannot arm or close while `worktree_status=active`
- **`migrate_state_checkpoint.py`** — additive CHECKPOINT field migration from `_template/STATE.md`
- **`cwin worktree-status`**, **`cwin worktree-prune`**, **`cwin template-check`**; `cwin sync` runs migrate
- **Templates** — worktree fields in STATE/SPEC/RITUAL.base; 8 preset RITUAL/IDENTITY synced
- **`.gitignore`** — add `.worktrees/` (required before first create)

## 0.5.4

- **Window-scoped review paths** — `review_scope.py` replaces hard-coded `pwa/`/`server/` filter; each loop reviews all changes in its territory
- **code-health** scope includes `tools/cursor-loop/` (loop package changes now trigger Phase 6)
- **PO** scope includes docs/backlog paths; PO Phase 6 still adds `main...HEAD` on app code per RITUAL
- **`detect_code_changed.sh`** — accepts `--loop-id` and `--state-file`; delegates to `review_scope.py`
- **`audit_review.py`** — stale check uses `round < last_reviewed` (not `<=`) when git diff present with findings

## 0.5.3

- **`prepare_review_tick.sh`** — Phase 5 prep: detect git diff, suggest `review_round` bump, set `review_status=pending`
- **Fresh-review gate** — `ritual_phase.py` rejects stale `review_status=done` when git diff exists or `review_round <= last_reviewed_round`
- **Wake prompt** — mandatory `/code-review` + `/receiving-code-review` when git diff non-empty (not only stale CHECKPOINT)
- **`last_reviewed_round`** — new CHECKPOINT field; set at Phase 7 completion
- **`cwin audit-review`** — compare HISTORY vs REVIEW_FINDINGS; report ticks that shipped code without review
- **RITUAL Phase 5** — all presets call `prepare_review_tick.sh`

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
