# cursor-loop

Standalone terminal loop system for **Cursor Agent** chats. One paste per window → agent arms dynamic wake (`arm-wake.sh`) and keeps working.

No MCP. No server. Works in any repo with bash, python3, and Cursor Editor Agent.

---

## Quick start

### 1. Add the package

**curl one-liner** (vendors into `tools/cursor-loop`, no git required):

```bash
curl -fsSL https://raw.githubusercontent.com/p1927/cursor-loop/v0.2.0/install-remote.sh | bash -s -- .
```

**git submodule:**

```bash
git submodule add https://github.com/p1927/cursor-loop.git tools/cursor-loop
bash tools/cursor-loop/install.sh . --symlink
```

**Or copy:**

```bash
cp -R /path/to/cursor-loop ./tools/cursor-loop
bash tools/cursor-loop/install.sh . --symlink
```

### 2. Create a loop contract

```bash
cp tools/cursor-loop/template/AGENT_LOOP_TEMPLATE.md docs/agents/my-task.md
# Edit loop_id, sentinel (unique!), interval_sec, Task
```

### 3. Start working

Open Cursor Agent chat → paste:

```text
@docs/agents/my-task.md keep working
```

---

## Install options

| Flag | Description |
|------|-------------|
| `--symlink` | Symlink rule + hooks to package (default) |
| `--copy` | Copy full package to `tools/cursor-loop` and copy hooks |
| `--package-path PATH` | Package location relative to project root |
| `--contracts-dir DIR` | Where loop contracts live (default: `docs/agents`) |
| `--uninstall` | Remove Cursor artifacts (not the package) |

See [ARCHITECTURE.md](ARCHITECTURE.md) for system design, binding TTL, and failure modes.

**Minimal example:** [examples/minimal-project/](examples/minimal-project/)

---

## What gets installed

| Artifact | Location |
|----------|----------|
| Cursor rule | `.cursor/rules/agent-loop-contract.mdc` |
| Hooks | `.cursor/hooks/loop-bind.sh`, `loop-survival.sh`, `_common.sh` |
| Manifest | `.cursor/cursor-loop.json` |
| Hooks config | merged into `.cursor/hooks.json` |
| Package scripts | stay at `<package_root>/scripts/` |

---

## Daily UX

1. Open one Agent chat per task/window
2. Paste: `@docs/agents/<contract>.md keep working`
3. Walk away

**Stop:** say **stop loop** in that chat.

**Extreme reset** (stuck loops, wrong chat, corrupt bindings):

```bash
bash tools/cursor-loop/scripts/force-reset.sh . --all
```

**Validate contracts** (unique loop_id per window):

```bash
bash tools/cursor-loop/scripts/validate_contracts.py .
```

**After IDE restart:** paste the same line again.

**Maintenance:**

```bash
python3 tools/cursor-loop/scripts/cleanup_bindings.py .        # prune stale bindings
python3 tools/cursor-loop/scripts/cleanup_bindings.py . --dry-run
```

Default TTL: 30 days (`binding_ttl_days` in manifest). Cron example in [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Package layout

```text
cursor-loop/
├── ARCHITECTURE.md
├── install-remote.sh
├── install.sh
├── scripts/
│   ├── agent-loop.sh
│   ├── loop-status.sh
│   ├── loop_hook_lib.py
│   ├── hook_bind.py
│   ├── hook_survival.py
│   ├── merge_hooks.py
│   ├── cleanup_bindings.py
│   ├── force-reset.sh
│   ├── validate_contracts.py
│   ├── verify-loop.sh
│   ├── daily-maintenance.sh
│   └── doctor.sh
├── cursor/
│   ├── rules/agent-loop-contract.mdc
│   └── hooks/
├── examples/minimal-project/
├── template/
└── tests/
```

---

## Loop config (in each contract doc)

| Field | Purpose |
|-------|---------|
| `loop_id` | Unique id; pidfile is `$TMPDIR/cursor-loop-<loop_id>.pid` |
| `sentinel` | Primary tick line prefix |
| `wake_sentinel` | Backup one-shot wake prefix |
| `interval_sec` | Seconds between ticks |
| `monitor_regex` | `notify_on_output` pattern (anchor with `^`) |
| `loop_script` | Path to `agent-loop.sh` (required) |
| `contract_doc` | Path to this contract file |

**One loop per chat. Unique sentinel per window.**

---

## How wake works

1. Agent starts `agent-loop.sh` in a background shell
2. Agent sets `notify_on_output` on the sentinel regex
3. Script prints `SENTINEL {"loop_id":"...","prompt":"..."}` every N seconds
4. Cursor wakes the agent → ritual → loop survival → repeat

Triple redundancy: primary loop + backup wake every turn + stop hook (binding in `.cursor/loop-bindings/`).

The stop hook respects `stopped: true` set when the user says **stop loop**. After 25 agent turns (`loop_limit`), the stop hook stops emitting follow-ups.

---

## Requirements

- Cursor **Editor** Agent (shell + background terminals + output monitoring)
- bash
- python3
- rsync (for `--copy` install)
- Not supported: Cloud Agents, headless ACP without shell monitoring

---

## Development

```bash
bash tests/run-all.sh
```

Test tiers (each cleans up temp state automatically):

| Tier | Path | What it covers |
|------|------|----------------|
| Segment | `tests/segments/` | Single modules, hooks, scripts |
| Integration | `tests/integration/` | Bind → stop → survival, locks, install |
| E2E | `tests/e2e/` | Full install → loop → reset lifecycle |

Run one tier: `python3 -m pytest tests/segments -q` or `bash tests/e2e/test_full_lifecycle.sh`

---

## License

MIT — see [LICENSE](LICENSE).

## Window Instances (v0.5+)

```bash
bash tools/cursor-loop/install.sh . --symlink --preset four-window
export PATH="$PWD/.cursor/bin:$PATH"

cwin status          # all loops + wake state
cwin paste worker-relay
cwin bootstrap --preset habits-pwa --refresh
cwin create qa-relay --archetype qa --interval 180
cwin validate
```

Canonical presets live in `tools/cursor-loop/window-instances/presets/`.
Project runtime state: `docs/window-instances/<loop_id>/STATE.md`.
