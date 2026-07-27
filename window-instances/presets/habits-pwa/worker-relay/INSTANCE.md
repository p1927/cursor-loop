# Window Instance — worker-relay

> **Paste in Worker window:** `@docs/window-instances/worker-relay/INSTANCE.md keep working`

## Loop config

| Field | Value |
|-------|-------|
| loop_id | `worker-relay` |
| loop_mode | `dynamic` |
| sentinel | `AGENT_LOOP_TICK_HABITS` |
| wake_sentinel | `AGENT_LOOP_WAKE_HABITS` |
| interval_sec | `120` |
| monitor_regex | `^AGENT_LOOP_WAKE_HABITS` |
| pidfile | `$TMPDIR/cursor-loop-worker-relay.pid` |
| loop_script | `tools/cursor-loop/scripts/agent-loop.sh` |
| state_file | `docs/window-instances/worker-relay/STATE.md` |
| contract_doc | `docs/window-instances/worker-relay/INSTANCE.md` |
| archetype | `engineer` |
| instance_version | `2` |

---

## Bundle

| File | Purpose |
|------|---------|
| [IDENTITY.md](IDENTITY.md) | Role, skills, forbidden |
| [RITUAL.md](RITUAL.md) | 9-phase tick |
| [STATE.md](STATE.md) | Backlog, checkpoint, history |

## Summary

Ship Habits features from the relay backlog. Full engineer ritual on every tick.

Arming and loop survival: [`.cursor/rules/agent-loop-contract.mdc`](../../../.cursor/rules/agent-loop-contract.mdc) (mandatory every turn).

## Stop

**stop loop** in this chat. Extreme reset: `bash tools/cursor-loop/scripts/force-reset.sh . --all`
