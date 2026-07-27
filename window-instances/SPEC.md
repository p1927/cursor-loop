# Window Instance Spec v1

A **Window Instance** is a bundled Cursor loop agent with four required files and a manifest entry.

## Required bundle files

| File | Required | Purpose |
|------|----------|---------|
| `INSTANCE.md` | Yes | Loop config table, paste line, links to siblings |
| `IDENTITY.md` | Yes | Role, skills, job, forbidden, sentinel |
| `RITUAL.md` | Yes | 9 phases; extends archetype base |
| `STATE.md` | Yes | Standard schema (below) |

## INSTANCE.md — Loop config fields

| Field | Example | Purpose |
|-------|---------|---------|
| `loop_id` | `worker-relay` | Unique loop identifier |
| `loop_mode` | `dynamic` | Wake mode |
| `sentinel` | `AGENT_LOOP_TICK_HABITS` | Tick sentinel |
| `wake_sentinel` | `AGENT_LOOP_WAKE_HABITS` | Wake sentinel |
| `interval_sec` | `60` | Wake interval |
| `monitor_regex` | `^AGENT_LOOP_WAKE_HABITS` | Shell monitor pattern |
| `pidfile` | `$TMPDIR/cursor-loop-worker-relay.pid` | PID file path |
| `loop_script` | `tools/cursor-loop/scripts/agent-loop.sh` | Loop script |
| `state_file` | `docs/window-instances/worker-relay/STATE.md` | State path |
| `contract_doc` | `docs/window-instances/worker-relay/INSTANCE.md` | Contract path |
| `archetype` | `engineer` | Ritual variant for phases 4–6 |
| `instance_version` | `1` | Schema migration tag |

## Archetypes

| Archetype | Phase 4 Execute | Phase 5 Verify | Phase 6 Review |
|-----------|-----------------|----------------|----------------|
| `engineer` | Ship feature code | `npm run build` | `/code-review` bugs/regressions |
| `designer` | Ship UI diff | build + 390px | `/code-review` + visual |
| `product` | Brainstorm + backlog mutate | lens sessions logged | Product code review template |
| `qa` | Run test plan | tests pass + repro | `/code-review` + coverage gaps |

## STATE.md — Required sections

Every instance STATE must contain these sections in order:

```markdown
## LAST_REVIEW
## CHECKPOINT
## IN_PROGRESS
## BACKLOG              # or domain-named backlogs (see manifest)
## REVIEW_FINDINGS
## HISTORY
```

Optional sections declared in `instances.manifest.json` (e.g. `UI_PROPOSALS`, `UX_GAPS`, `REFACTOR_BACKLOG`).

## CHECKPOINT fields

| Field | Values | Purpose |
|-------|--------|---------|
| `last_wake` | ISO timestamp | Last wake time |
| `current_item_id` | backlog id | Active item |
| `phase` | `1-wake` … `9-arm` | Recovery resumes here |
| `review_status` | `pending` / `done` / `skipped` / `triaged` | Review gate |
| `review_skip_reason` | text | Required when skipped |
| `confirmed_next` | backlog id | Next item after close |
| `loops` | text | Optional human note: last verify-wake result / arm pid |

## Phase gate rules

1. Agent cannot set `phase: 8-close` unless `review_status` is `done`, `triaged`, or `skipped` (with reason).
2. Agent cannot arm wake (Phase 9) if `phase < 8-close` or `review_status=pending`.
3. Phase 7 triage must move each REVIEW_FINDINGS row to fix-now, backlog, or closed.

### Dynamic wake lifecycle

Dynamic mode (`loop_mode: dynamic`) uses one-shot `arm-wake.sh` per turn:

| When | `verify-wake` | Meaning |
|------|---------------|---------|
| Between turns (healthy) | **ARMED** | Fresh sleeper — `instance-doctor` should show this most of the time |
| After sentinel fired (mid-turn) | **DOWN** | Old cycle finished — re-arm before ending turn |
| End of turn with DOWN | **FAIL** | Re-arm required; see [`RITUAL.base.md`](RITUAL.base.md) Phase 9 |

See [`.cursor/rules/agent-loop-contract.mdc`](../../../.cursor/rules/agent-loop-contract.mdc) for full arming rules.

## Universal 9 phases

| Phase | Name |
|-------|------|
| 1 | Wake |
| 2 | Review |
| 3 | Select |
| 4 | Execute |
| 5 | Verify |
| 6 | Review |
| 7 | Triage |
| 8 | Close |
| 9 | Arm |

See [`RITUAL.base.md`](RITUAL.base.md) for phase actions per archetype.

## REVIEW_FINDINGS schema

| id | severity | finding | source | action | backlog_ref | status |

Severity: `critical` | `high` | `medium` | `low`  
Action: `fix-now` | `backlog` | `closed`  
Status: `open` | `closed`

## Manifest entry

Each instance must be registered in [`instances.manifest.json`](../instances.manifest.json):

```json
{
  "loop_id": "worker-relay",
  "archetype": "engineer",
  "bundle": "docs/window-instances/worker-relay",
  "contract_doc": "docs/window-instances/worker-relay/INSTANCE.md",
  "state_file": "docs/window-instances/worker-relay/STATE.md",
  "sentinel": "AGENT_LOOP_TICK_HABITS",
  "wake_sentinel": "AGENT_LOOP_WAKE_HABITS",
  "interval_sec": 60,
  "backlog_sections": ["BACKLOG"],
  "handoffs_out": ["po-relay", "ux-relay", "code-health"]
}
```

## Validation

```bash
python3 tools/cursor-loop/scripts/validate_instance.py .
```

Fails if any instance misses required files, sections, CHECKPOINT fields, or manifest registration.

## Four-window architecture

| # | loop_id | Wake sentinel | Interval |
|---|---------|---------------|----------|
| 1 | `worker-relay` | `AGENT_LOOP_WAKE_HABITS` | 60s |
| 2 | `ux-relay` | `AGENT_LOOP_WAKE_UX_RELAY` | 300s |
| 3 | `code-health` | `AGENT_LOOP_WAKE_CODE_HEALTH` | 120s |
| 4 | `po-relay` | `AGENT_LOOP_WAKE_PO_RELAY` | 120s |

**One chat = one loop_id.** Default `loop_mode: dynamic` — each turn ends with `arm-wake.sh`.

### Bind / refresh

```bash
bash tools/cursor-loop/scripts/refresh-loops.sh .
```

Then in each chat: `@docs/window-instances/<loop_id>/INSTANCE.md keep working`

### Status

```bash
bash tools/cursor-loop/scripts/loop-status.sh
bash tools/cursor-loop/scripts/instance-doctor.sh
python3 tools/cursor-loop/scripts/validate_instance.py .
```

### Stop one loop

Say **stop loop** in that chat, or:

```bash
bash tools/cursor-loop/scripts/refresh-loops.sh . --loop-id ux-relay
```

### PO ↔ UX agreement

- PO writes `UI_PROPOSALS` only — never `UI_POLISH_BACKLOG`
- UX triages proposals → agreed items land in `UI_POLISH_BACKLOG`
- UX logs gaps in `UX_GAPS`; PO promotes agreed gaps to `UI_PROPOSALS`
- Conflicts → `DESIGN_DECISIONS` in po-relay STATE

Handoff detail lives in each instance's `IDENTITY.md`.
