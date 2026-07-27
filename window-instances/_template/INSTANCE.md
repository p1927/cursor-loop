# Window Instance — {{loop_id}}

> **Paste in window:** `@docs/window-instances/{{loop_id}}/INSTANCE.md keep working`

## Loop config

| Field | Value |
|-------|-------|
| loop_id | `{{loop_id}}` |
| loop_mode | `dynamic` |
| sentinel | `{{sentinel_tick}}` |
| wake_sentinel | `{{sentinel_wake}}` |
| interval_sec | `{{interval_sec}}` |
| monitor_regex | `^{{sentinel_wake}}` |
| pidfile | `$TMPDIR/cursor-loop-{{loop_id}}.pid` |
| loop_script | `tools/cursor-loop/scripts/agent-loop.sh` |
| state_file | `docs/window-instances/{{loop_id}}/STATE.md` |
| contract_doc | `docs/window-instances/{{loop_id}}/INSTANCE.md` |
| archetype | `{{archetype}}` |
| instance_version | `1` |

### Phase 9 arm (copy env from table above)

```bash
LOOP_ID={{loop_id}} \
WAKE_SENTINEL={{sentinel_wake}} \
INTERVAL={{interval_sec}} \
CONTRACT_DOC=docs/window-instances/{{loop_id}}/INSTANCE.md \
STATE_FILE=docs/window-instances/{{loop_id}}/STATE.md \
bash tools/cursor-loop/scripts/arm-wake.sh

bash tools/cursor-loop/scripts/verify-wake.sh {{loop_id}}   # must exit 0 before ending turn
```

See [`../_template/RITUAL.base.md`](../_template/RITUAL.base.md) Phase 9 and agent-loop-contract.mdc.

---

## Bundle

| File | Purpose |
|------|---------|
| [IDENTITY.md](IDENTITY.md) | Role, skills, forbidden |
| [RITUAL.md](RITUAL.md) | 9-phase tick |
| [STATE.md](STATE.md) | Backlog, checkpoint, history |

## Summary

{{summary_one_liner}}

Arming and loop survival: [`.cursor/rules/agent-loop-contract.mdc`](../../../.cursor/rules/agent-loop-contract.mdc) (mandatory every turn).

## Stop

**stop loop** in this chat. Extreme reset: `bash tools/cursor-loop/scripts/force-reset.sh . --all`
