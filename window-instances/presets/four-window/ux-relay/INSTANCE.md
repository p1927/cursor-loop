# Window Instance — ux-relay

> **Paste in UX window:** `@docs/window-instances/ux-relay/INSTANCE.md keep working`

## Loop config

| Field | Value |
|-------|-------|
| loop_id | `ux-relay` |
| loop_mode | `dynamic` |
| sentinel | `AGENT_LOOP_TICK_UX_RELAY` |
| wake_sentinel | `AGENT_LOOP_WAKE_UX_RELAY` |
| interval_sec | `300` |
| monitor_regex | `^AGENT_LOOP_WAKE_UX_RELAY` |
| pidfile | `$TMPDIR/cursor-loop-ux-relay.pid` |
| loop_script | `tools/cursor-loop/scripts/agent-loop.sh` |
| state_file | `docs/window-instances/ux-relay/STATE.md` |
| contract_doc | `docs/window-instances/ux-relay/INSTANCE.md` |
| archetype | `designer` |
| instance_version | `1` |

---

## Bundle

| File | Purpose |
|------|---------|
| [IDENTITY.md](IDENTITY.md) | Role, skills, forbidden |
| [RITUAL.md](RITUAL.md) | 9-phase tick |
| [STATE.md](STATE.md) | Backlog, checkpoint, history |

## Summary

UI/UX polish — web research, triage PO proposals, ship modern UI matching reference apps.

Arming: [`.cursor/rules/agent-loop-contract.mdc`](../../../.cursor/rules/agent-loop-contract.mdc)

## Stop

**stop loop** in this chat.
