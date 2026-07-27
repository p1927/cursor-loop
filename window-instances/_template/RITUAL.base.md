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
| 3 | **Select** | Resume `IN_PROGRESS` or pick top backlog item; **create worktree** when item touches code |
| 4 | **Execute** | Archetype-specific (see table) |
| 5 | **Verify** | Archetype-specific (see table) + change detection (below) |
| 6 | **Code review** | `/code-review` Round N (see below) |
| 7 | **Receive review** | `/receiving-code-review` Round N (see below) |
| 8 | **Close** | Merge worktree to `main`, remove worktree, HISTORY row, clear IN_PROGRESS |
| 9 | **Arm** | `checkpoint-loop.py --product` + `arm-wake.sh` per agent-loop-contract |

## Phases 4–6 by archetype

| Phase | engineer | designer | product | qa |
|-------|----------|----------|---------|-----|
| 4 Execute | Ship feature code | Ship UI diff | Brainstorm + backlog mutate | Run test plan / automation |
| 5 Verify | `npm run build` (pwa/) | build + 390px check | lens sessions logged | tests pass + repro steps |
| 6 Code review | `/code-review` bugs/regressions | `/code-review` + visual | Product code review template | `/code-review` + coverage gaps |

## Phase 5 end — change detection (required)

After archetype-specific verify steps, **always** run:

```bash
bash tools/cursor-loop/scripts/prepare_review_tick.sh . \
  --state-file <STATE.md path> \
  --loop-id <loop_id> \
  --apply
```

Phase 5 **MUST**:

1. Run `prepare_review_tick.sh --apply` (writes `review_changed_files`, `review_fingerprint`, `code_changed`, `review_round`)
2. If `code_changed=yes` → set `review_status=pending`, record `review_diff_range`
3. Cannot enter Phase 8 with stale manifest or `review_status=done` from a prior tick while git diff is non-empty
4. On Phase 7 completion → set `last_reviewed_round` to the round just triaged

Manual fallback (if script unavailable):

```bash
bash tools/cursor-loop/scripts/detect_code_changed.sh . --loop-id <loop_id> --state-file <STATE.md>
```

Set `CHECKPOINT.code_changed` to `yes` or `no`. If `yes`:

1. Increment `CHECKPOINT.review_round` (must be > `last_reviewed_round`)
2. Set `CHECKPOINT.review_diff_range` (e.g. `uncommitted`, `HEAD~1..HEAD`)
3. Set `review_status=pending`

If `no`: may skip Phase 6/7 with `review_status=skipped` and non-empty `review_skip_reason`.

## Phase 3 — Worktree (code items)

**Mandatory prep** (engineer / designer / qa archetypes when item touches code):

```bash
bash tools/cursor-loop/scripts/prepare_select_tick.sh . \
  --state-file <STATE.md path> \
  --loop-id <loop_id>
```

When `requires_worktree=yes`, create before Phase 4:

```bash
bash tools/cursor-loop/scripts/instance_worktree.sh create . \
  --loop-id <loop_id> \
  --item-id <backlog-id> \
  --state-file <STATE.md path>
```

`create --state-file` auto-patches CHECKPOINT: `worktree_status=active`, `worktree_path`, `worktree_branch`, `worktree_item_id`, `current_item_id`.

**PO default:** docs-only ticks skip worktree (`worktree_status=none`).

**Phases 4–7:** `cd` to `WORKTREE_PATH` (or set git cwd there). Run builds, commits, and `prepare_review_tick.sh --apply` inside the worktree. Never commit app code on `main` while `worktree_status=active`.

## Phase 8 — Worktree merge + cleanup (after review)

When `worktree_status=active` and review is complete:

```bash
bash tools/cursor-loop/scripts/instance_worktree.sh merge . --loop-id <loop_id>
bash tools/cursor-loop/scripts/instance_worktree.sh remove . --loop-id <loop_id>
```

Merge policy: **rebase onto `main`, then `--ff-only` merge** (linear history). On conflict: fix in worktree, `git rebase --continue`, retry merge.

Reset CHECKPOINT: `worktree_status=none`, clear `worktree_path` / `worktree_branch` / `worktree_item_id`.

## Phase 6 — Code review (Round N)

**Required when `code_changed=yes`.**

**Mandatory command:** Invoke [`/code-review`](../../../.cursor/commands/code-review.md) — read the full command file before reviewing. Announce: "Using /code-review to review Round N."

1. Run `/code-review` on `review_diff_range` (do not freestyle review).
2. Log every finding to `REVIEW_FINDINGS` with id `{prefix}-r{N}-{seq}` and `source=round-{N}`.
3. If zero issues: add sentinel row `{prefix}-r{N}-000 | low | No issues in reviewed diff | round-{N} /code-review | closed | — | closed`.
4. Set `CHECKPOINT.phase=6-review`; keep `review_status=pending`.

## Phase 7 — Receive + backlog reflect (Round N)

**Required when `code_changed=yes`.** Two mandatory sub-steps:

### Phase 7a — Receive (skill + command)

**Mandatory skill:** Read Superpowers **receiving-code-review** skill first.  
**Mandatory command:** Invoke [`/receiving-code-review`](../../../.cursor/commands/receiving-code-review.md).

Process **only** rows where `source=round-{N}`:

1. READ → VERIFY → EVALUATE → RESPOND → IMPLEMENT (fix-now only).
2. Set `action` on every round-N row: `fix-now` | `backlog` | `closed` | `pushback`.
3. Append HISTORY note for pushbacks.

### Phase 7b — Backlog reflect (mandatory)

**Always run after 7a** — reflection step so deferred work is never lost.

For every round-N row with `action=backlog` (and any low-priority finding not fix-now):

1. Create backlog item with id, priority, acceptance criteria, notes → finding id.
2. Set `REVIEW_FINDINGS.backlog_ref` to that id; finding `status=open`.
3. PO: route to target window backlog per `/receiving-code-review` routing table.

Cannot enter Phase 8 until every round-N row is triaged and every `backlog` row has a real `backlog_ref`.

4. Set `review_status=done` (all closed/pushback) or `triaged` (backlog items remain open).
5. Set `CHECKPOINT.last_reviewed_round` to N.
6. Set `CHECKPOINT.phase=7-triage`.

If `code_changed=no`, Phase 7 may triage backlog/handoffs only; set `review_status=skipped`.

## Phase 7 — Triage rules (all ticks)

Sort findings into:

- **Fix now** — blocks closing current item; implement in 7a before Phase 8
- **Backlog** — deferred; **must** complete 7b with backlog id + AC
- **Pushback** — finding rejected with documented technical reason
- **Closed** — resolved, N/A, or zero-finding sentinel

Do not leave findings as untriaged `open` at Phase 8.

## Phase 8 — Close checklist

- [ ] Round-N findings triaged in 7a; every `backlog` row has `backlog_ref` + backlog entry (7b)
- [ ] Worktree merged to `main` and removed (when `worktree_status=active`)
- [ ] HISTORY row appended
- [ ] IN_PROGRESS cleared or updated
- [ ] CHECKPOINT: `phase=8-close`, `review_status` set, `worktree_status=none`
- [ ] Backlog checkboxes updated

## Phase 9 — Arm (dynamic mode)

**Cannot arm if:**

- `CHECKPOINT.phase < 8-close`
- `review_status=pending`
- `worktree_status=active` (unmerged worktree)
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
