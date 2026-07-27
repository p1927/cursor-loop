# Agent Loop — [Task Name]

> Copy to `docs/agents/<your-task>.md`, fill Loop config + Task, then paste:
> `@docs/agents/<your-task>.md keep working`

## Loop config

| Field | Value |
|-------|-------|
| loop_mode | `dynamic` |
| loop_id | `my-task` |
| sentinel | `AGENT_LOOP_TICK_MY_TASK` |
| wake_sentinel | `AGENT_LOOP_WAKE_MY_TASK` |
| interval_sec | `120` |
| monitor_regex | `^AGENT_LOOP_WAKE_MY_TASK` |
| loop_script | `<package_root>/scripts/agent-loop.sh` |
| contract_doc | `docs/agents/my-task.md` |
| state_file | `docs/agents/my-task-STATE.md` |

**Rules:** `loop_id` and sentinels must be **unique** per window.  
Dynamic mode: wake pidfile `$TMPDIR/cursor-loop-<loop_id>.wake.pid` (via `arm-wake.sh`).

### Dynamic wake lifecycle

- One `arm-wake.sh` = one sleep cycle. After the sentinel fires, `verify-wake` shows **DOWN** — normal mid-turn, not success.
- **Every turn** must end with a fresh arm so `verify-wake` exit 0 (steady state **ARMED** between turns).
- Follow-up turns are not exempt. Never trust stale terminal `WAKE_ARMED` output — run `verify-wake.sh` fresh.
- Full rules: `.cursor/rules/agent-loop-contract.mdc` → **Dynamic wake lifecycle**.

---

## Task

Describe what the agent should work on every tick.

---

## Ritual (every tick)

1. Read **this file** and state/backlog docs
2. Do one unit of work toward Task
3. Verify (build, lint, etc.)
4. Update state / commit if applicable
5. **Loop survival** — checkpoint + `arm-wake.sh` + `verify-wake.sh` exit 0 (see agent-loop-contract **Dynamic wake lifecycle**; re-arm every turn including follow-ups)

---

## Stop

User says **stop loop** → kill loop process, clear pidfile, do not re-arm.
