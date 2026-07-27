# Universal 9-Phase Ritual (base)

All Window Instances run phases **1–9** in **strict order** — advance one phase at a time; no jumps.

**Phase line:** `1-wake → 2-orient → 3-select → 4-execute → 5-verify → 6-review → 7-triage → 8-close → 9-arm`

Every wake starts at **Phase 1**. `validate_ritual_gate.py` blocks arm if the line is incomplete.

All Window Instances run phases **1–9** with the same names. Phases **4–6** vary by `archetype`.

## Phase overview

| Phase | Name | All windows |
|-------|------|-------------|
| 1 | **Wake** | Read INSTANCE → IDENTITY → STATE → RITUAL; confirm `loop_id` from wake JSON |
| 2 | **Orient** | Update `LAST_REVIEW`; read CHECKPOINT + git status |
| 3 | **Select** | Resume `IN_PROGRESS` or pick top backlog item |
| 4 | **Execute** | Archetype-specific (see table) |
| 5 | **Verify** | Archetype-specific (see table) + change detection (below) |
| 6 | **Code review** | `/code-review` Round N (see below) |
| 7 | **Receive review** | `/receiving-code-review` Round N (see below) |
| 8 | **Close** | HISTORY row, clear IN_PROGRESS, update CHECKPOINT |
| 9 | **Arm** | `checkpoint-loop.py --product` + `arm-wake.sh` per agent-loop-contract |

## Phases 4–6 by archetype

| Phase | engineer | designer | product | qa |
|-------|----------|----------|---------|-----|
| 4 Execute | Ship feature code | Ship UI diff | Brainstorm + backlog mutate | Run test plan / automation |
| 5 Verify | `npm run build` (pwa/) | build + 390px check | lens sessions logged | tests pass + repro steps |
| 6 Code review | `/code-review` bugs/regressions | `/code-review` + visual | Product code review template | `/code-review` + coverage gaps |

## Phase 5 end — change detection

After archetype-specific verify steps:

```bash
git diff --stat HEAD -- pwa/ server/
git diff --stat --cached -- pwa/ server/
```

Set `CHECKPOINT.code_changed` to `yes` or `no`. If `yes`:

1. Increment `CHECKPOINT.review_round`
2. Set `CHECKPOINT.review_diff_range` (e.g. `uncommitted`, `HEAD~1..HEAD`, or tick commit range)

If `no`: may skip Phase 6/7 with `review_status=skipped` and non-empty `review_skip_reason`.

## Phase 6 — Code review (Round N)

**Required when `code_changed=yes`.**

1. Invoke [`/code-review`](../../../.cursor/commands/code-review.md) on `review_diff_range`.
2. Log every finding to `REVIEW_FINDINGS` with id `{prefix}-r{N}-{seq}` and `source=round-{N}`.
3. If zero issues: add sentinel row `{prefix}-r{N}-000 | low | No issues in reviewed diff | round-{N} /code-review | closed | — | closed`.
4. Set `CHECKPOINT.phase=6-review`; keep `review_status=pending`.

## Phase 7 — Receive review (Round N)

**Required when `code_changed=yes`.** Follow [`/receiving-code-review`](../../../.cursor/commands/receiving-code-review.md) against **only** rows where `source=round-{N}`.

1. READ → VERIFY → EVALUATE → RESPOND → IMPLEMENT (fix-now only).
2. Update each row's `action` and `status`; append HISTORY note for pushbacks.
3. Set `review_status=done` (all closed/pushback) or `triaged` (backlog items remain open).
4. Set `CHECKPOINT.phase=7-triage`.

If `code_changed=no`, Phase 7 may triage backlog/handoffs only; set `review_status=skipped`.

## Phase 7 — Triage rules (all ticks)

Sort findings into:

- **Fix now** — blocks closing current item; implement before Phase 8
- **REVIEW_FINDINGS** — non-blocking, stays in STATE until resolved
- **Pushback** — finding rejected with documented technical reason
- **New backlog item** — with id, AC, target window

## Phase 8 — Close checklist

- [ ] Round-N findings triaged (when `code_changed=yes`)
- [ ] HISTORY row appended
- [ ] IN_PROGRESS cleared or updated
- [ ] CHECKPOINT: `phase=8-close`, `review_status` set, `current_item_id` recorded
- [ ] Backlog checkboxes updated

## Phase 9 — Arm (dynamic mode)

**Cannot arm if:**

- `CHECKPOINT.phase < 8-close`
- `review_status=pending`
- `code_changed=yes` and round-N findings untriaged

**Allowed skip:** `review_status=skipped` with `review_skip_reason` (docs-only ticks).

### Dynamic wake lifecycle

| When | `verify-wake` | Meaning |
|------|---------------|---------|
| End of a healthy turn | **ARMED** | Fresh sleeper running — target steady state |
| After old sleeper fired (mid-turn) | **DOWN** | Normal — re-arm before ending turn |
| End of turn with DOWN | **FAIL** | Gate not met — run `arm-wake.sh` again |
| Follow-up turn with DOWN | **FAIL** | Still must re-arm |

One arm = one sleep cycle. DOWN after sentinel is **not** "job done" unless a **new** arm is live (`verify-wake` exit 0).

### Phase 9 checklist

1. `checkpoint-loop.py --product --evidence <item-id>` (or `--blocker`)
2. Arm (background, `block_until_ms: 0`, `notify_on_output` on `^<wake_sentinel>`):

```bash
LOOP_ID=<loop_id> \
WAKE_SENTINEL=<wake_sentinel> \
INTERVAL=<interval_sec> \
CONTRACT_DOC=<contract_doc> \
STATE_FILE=<state_file> \
bash tools/cursor-loop/scripts/arm-wake.sh
```

3. Verify fresh — **never** trust old terminal `WAKE_ARMED` output:

```bash
bash tools/cursor-loop/scripts/verify-wake.sh <loop_id>   # must exit 0
```

4. Set `CHECKPOINT.phase=9-arm` **only after** step 3 passes
5. If verify fails or shell aborted: re-run step 2 once; record in STATE if still DOWN — stop hook will recovery-wake

Full arming rules: [`.cursor/rules/agent-loop-contract.mdc`](../../../.cursor/rules/agent-loop-contract.mdc).
