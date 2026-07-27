# Window Instance — code-health

> **Paste in Code window:** `@docs/window-instances/code-health/INSTANCE.md keep working`

## Loop config

| Field | Value |
|-------|-------|
| loop_id | `code-health` |
| loop_mode | `dynamic` |
| sentinel | `AGENT_LOOP_TICK_CODE_HEALTH` |
| wake_sentinel | `AGENT_LOOP_WAKE_CODE_HEALTH` |
| interval_sec | `120` |
| monitor_regex | `^AGENT_LOOP_WAKE_CODE_HEALTH` |
| pidfile | `$TMPDIR/cursor-loop-code-health.pid` |
| loop_script | `tools/cursor-loop/scripts/agent-loop.sh` |
| state_file | `docs/window-instances/code-health/STATE.md` |
| contract_doc | `docs/window-instances/code-health/INSTANCE.md` |
| archetype | `engineer` |
| instance_version | `1` |

---

## Bundle

| File | Purpose |
|------|---------|
| [IDENTITY.md](IDENTITY.md) | Role, skills, forbidden |
| [RITUAL.md](RITUAL.md) | 9-phase tick |
| [STATE.md](STATE.md) | Backlog, checkpoint, history |

## Summary

Bugs, structural refactor, DRY, naming — independent of relay and UX.

Arming: [`.cursor/rules/agent-loop-contract.mdc`](../../../.cursor/rules/agent-loop-contract.mdc)

## Stop

**stop loop** in this chat.
