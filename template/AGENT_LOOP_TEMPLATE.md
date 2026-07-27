# Agent Loop — [Task Name]

> Copy to `docs/agents/<your-task>.md`, fill Loop config + Task, then paste:
> `@docs/agents/<your-task>.md keep working`

## Loop config

| Field | Value |
|-------|-------|
| loop_id | `my-task` |
| sentinel | `AGENT_LOOP_TICK_MY_TASK` |
| wake_sentinel | `AGENT_LOOP_WAKE_MY_TASK` |
| interval_sec | `120` |
| monitor_regex | `^AGENT_LOOP_TICK_MY_TASK` |
| loop_script | `<package_root>/scripts/agent-loop.sh` |
| contract_doc | `docs/agents/my-task.md` |
| state_file | `docs/agents/my-task-STATE.md` |

**Rules:** `loop_id` and `sentinel` must be **unique** per window.  
Pidfile at runtime: `$TMPDIR/cursor-loop-<loop_id>.pid`

---

## Task

Describe what the agent should work on every tick.

---

## Ritual (every tick)

1. Read **this file** and state/backlog docs
2. Do one unit of work toward Task
3. Verify (build, lint, etc.)
4. Update state / commit if applicable
5. **Loop survival** — see `.cursor/rules/agent-loop-contract.mdc`

---

## Stop

User says **stop loop** → kill loop process, clear pidfile, do not re-arm.
