# cursor-loop architecture

Terminal-based wake system for Cursor **Editor Agent** chats. No MCP, no server, no push notifications from outside the IDE.

---

## Problem

Cursor Agent chats go idle after a turn completes. There is no supported API for an external process to **push** work into an arbitrary chat. The reliable primitive is: **print a line to a monitored terminal** → Cursor wakes the agent.

cursor-loop automates that loop so the user pastes one line per window and walks away.

---

## System diagram

```text
┌─────────────────────────────────────────────────────────────────┐
│  User (once per window / after IDE restart)                      │
│  "@docs/agents/my-task.md keep working"                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
  beforeSubmitPrompt    Agent rule         (optional) stop hook
  loop-bind.sh          agent-loop-        loop-survival.sh
                        contract.mdc
         │                   │                   │
         ▼                   ▼                   ▼
  .cursor/loop-bindings/   Arming + Ritual +   followup_message
  <conversation_id>.json   Loop survival      if loop dead &
                           every turn          not stopped
         │
         ▼
  Background bash: agent-loop.sh
  sleep N → print SENTINEL {"loop_id","prompt"}
         │
         ▼
  notify_on_output(regex) → Agent wakes → Ritual → survival → repeat
```

---

## Components

| Layer | Artifact | Role |
|-------|----------|------|
| **Contract** | `docs/agents/*.md` | Task, ritual, loop config table |
| **Manifest** | `.cursor/cursor-loop.json` | `package_root`, `contracts_dir`, `binding_ttl_days` |
| **Primary loop** | `scripts/agent-loop.sh` | Infinite `sleep` + sentinel JSON line |
| **Agent rule** | `.cursor/rules/agent-loop-contract.mdc` | Mandates arming, ritual, backup wake, stop |
| **Bind hook** | `hook_bind.py` via `loop-bind.sh` | Maps `conversation_id` → contract; honors stop / keep working |
| **Survival hook** | `hook_survival.py` via `loop-survival.sh` | Re-arms via `followup_message` if pidfile dead |
| **Bindings store** | `.cursor/loop-bindings/*.json` | Runtime state per chat (gitignored) |

---

## Triple redundancy

1. **Primary loop** — background shell prints sentinel every `interval_sec`.
2. **Backup wake** — agent starts a one-shot `sleep` + wake sentinel at end of **every** turn (rule-enforced).
3. **Stop hook** — if primary loop dies, Cursor's stop hook can inject a follow-up (up to `loop_limit`, default 25).

Any one layer can fail temporarily; the others recover within one turn or one tick.

---

## Binding schema

```json
{
  "schema_version": 1,
  "loop_id": "worker-relay",
  "contract_doc": "docs/agents/worker-relay.md",
  "sentinel": "AGENT_LOOP_TICK_HABITS",
  "interval_sec": "60",
  "loop_script": "tools/cursor-loop/scripts/agent-loop.sh",
  "pidfile": "/var/folders/.../cursor-loop-worker-relay.pid",
  "stopped": false,
  "updated_at": "2026-07-27T09:15:00+00:00"
}
```

| Field | Set by |
|-------|--------|
| `stopped` | Bind hook on "stop loop"; cleared on re-`@` contract or "keep working" |
| `pidfile` | Computed at bind time; survival hook checks this path |
| `updated_at` | Every `write_binding`; used for TTL cleanup |

---

## Manifest schema

```json
{
  "version": "0.2.0",
  "package_root": "tools/cursor-loop",
  "contracts_dir": "docs/agents",
  "contract_globs": [],
  "binding_ttl_days": 30
}
```

Hooks resolve `package_root/scripts/` for Python modules — **not** relative to hook file location. This makes `--copy` install mode work when hooks live in `.cursor/hooks/`.

---

## Stop flow

```text
User: "stop loop"
  → bind hook: binding.stopped = true
  → agent rule: kill PID, remove pidfile, no re-arm
  → survival hook: exit (skipped while stopped)

User: "@contract.md keep working" (same chat)
  → bind hook: new binding, stopped = false
```

Gap: if user says "stop loop" **before** any `@` contract, no binding exists — survival hook won't know to stay quiet until first bind.

---

## Binding TTL / cleanup

Stale bindings in `.cursor/loop-bindings/` are pruned after `binding_ttl_days` (default 30).

| Trigger | Script |
|---------|--------|
| Opportunistic | `hook_bind.py` → `maybe_cleanup_bindings` (max once / 24h) |
| Manual / cron | `scripts/cleanup_bindings.py [--dry-run]` |

Example cron (daily 03:00):

```cron
0 3 * * * cd /path/to/project && python3 tools/cursor-loop/scripts/cleanup_bindings.py
```

---

## Install modes

| Mode | Package | Hooks | Use case |
|------|---------|-------|----------|
| `--symlink` | stays in repo/submodule | symlinked to package | dev, submodule consumers |
| `--copy` | rsync'd to `package_path` | copied to `.cursor/hooks/` | vendor, curl install |
| `install-remote.sh` | curl/git fetch + `--copy` | same as copy | quick try without submodule |

---

## Sentinel isolation

Each window must have a **unique** `sentinel` and `loop_id`. The agent rule instructs ignoring foreign `AGENT_LOOP_TICK_*` lines. Isolation is **convention + agent discipline**, not enforced in bash.

---

## Platform constraints

| Works | Does not work |
|-------|----------------|
| Cursor Editor Agent | Cloud Agents |
| Shell + background terminals | Headless without output monitoring |
| macOS, Linux | Windows (untested; bash assumed) |
| `notify_on_output` on sentinel regex | External push / MCP wake |

---

## Known failure modes

| Symptom | Likely cause |
|---------|----------------|
| Loop stops after ~30s–3min | Cursor cleaned up background shell → survival hook or manual re-paste |
| Stop hook re-arms after "stop loop" | Binding missing or `stopped` not set (stop before first `@`) |
| Wrong window responds to tick | Duplicate sentinel or agent ignored isolation rule |
| Hooks silent | Missing manifest, python3, or wrong `package_root` |
| `loop_limit` hit | 25 stop-hook follow-ups exhausted; paste contract again |

---

## File map

```text
cursor-loop/
├── install.sh              # consumer install
├── install-remote.sh       # curl one-liner entry
├── scripts/
│   ├── agent-loop.sh       # sentinel ticker
│   ├── hook_bind.py        # beforeSubmitPrompt logic
│   ├── hook_survival.py    # stop hook logic
│   ├── loop_hook_lib.py    # shared Python
│   ├── cleanup_bindings.py # TTL prune
│   └── doctor.sh           # health check
├── cursor/
│   ├── rules/agent-loop-contract.mdc
│   └── hooks/              # thin bash → Python
└── examples/minimal-project/
```

See [README.md](README.md) for usage.
