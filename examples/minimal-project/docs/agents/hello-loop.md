# Agent Loop — Hello World

> Paste: `@docs/agents/hello-loop.md keep working`

## Loop config

| Field | Value |
|-------|-------|
| loop_id | `hello-loop` |
| sentinel | `AGENT_LOOP_TICK_HELLO` |
| wake_sentinel | `AGENT_LOOP_WAKE_HELLO` |
| interval_sec | `60` |
| monitor_regex | `^AGENT_LOOP_TICK_HELLO` |
| loop_script | `vendor/cursor-loop/scripts/agent-loop.sh` |
| contract_doc | `docs/agents/hello-loop.md` |

---

## Task

On each tick, append one line to `notes/tick-log.md` with an ISO timestamp and a short status message. Then run loop survival.

---

## Ritual (every tick)

1. Read this file
2. Append one line to `notes/tick-log.md`
3. Loop survival (see `.cursor/rules/agent-loop-contract.mdc`)

---

## Stop

Say **stop loop** in this chat.
