# Ritual — code-health

**extends:** `engineer` (refactor variant)  
**base:** [`../_template/RITUAL.base.md`](../_template/RITUAL.base.md)

## Phase 2 — Orient

`git status`; `git log -10 --oneline`; `git diff --stat`; patchwork clusters; update `LAST_REVIEW`.

## Phase 3 — Select

Resume `IN_PROGRESS` OR top `REFACTOR_BACKLOG` / `BUG_BACKLOG` OR next `SCAN_COVERAGE` row.

**Worktree (code items):** mandatory prep then create before Phase 4:

```bash
bash tools/cursor-loop/scripts/prepare_select_tick.sh . \
  --state-file docs/window-instances/code-health/STATE.md \
  --loop-id code-health
bash tools/cursor-loop/scripts/instance_worktree.sh create . \
  --loop-id code-health \
  --item-id <backlog-id> \
  --state-file docs/window-instances/code-health/STATE.md
```

Phases 4–7 run inside `WORKTREE_PATH` (create auto-patches CHECKPOINT).

## Phase 4 — Execute

Brainstorm 2 approaches; pick minimal structural fix. Evaluate touched code against checklist below (self-check before formal review).

### Line-by-line checklist (score pass / warn / fail)

**Correctness:** null guards, error paths, races, offline/queue consistency, no stray `any`

**Robustness:** no patchwork; business rules in lib/hooks once; side effects isolated

**Structure:** sections orchestrate; components present; hooks subscribe; routes thin

**Readability:** intent names; functions ≤ ~40 lines; no mystery booleans; import order

**File naming:** one export per file; filename matches export; hooks `use*`; no `utils.ts` maze

**DRY:** repeated JSX/conditionals (≥2) → component or hook; shared types in `lib/`

**Patchwork signals:** 3+ fixes same file; per-tab banners → shared awareness component; queue state scattered → centralize

## Phase 5 — Verify

```bash
cd pwa && npm run build
cd server && python -m compileall habits_api   # when Python touched
bash tools/cursor-loop/scripts/prepare_review_tick.sh . \
  --state-file docs/window-instances/code-health/STATE.md \
  --loop-id code-health \
  --apply
```

Apply script output: set `code_changed`, increment `review_round` if yes, set `review_status=pending`, record `review_diff_range`.

**Regression spot-checks (when area touched):**

| Area | Check |
|------|--------|
| Meal plan queue | Dismiss clears failed ids; remote banner navigates |
| Log swipe | Directions + undo toast |
| Cards | Search/filter + FAB create |
| Offline | Queue banners when server offline |

## Phase 6 — Code review (Round N)

Required when `code_changed=yes`. Phase 4 checklist = self-check; Phase 6 = formal review.

**Mandatory:** Invoke [`/code-review`](../../../.cursor/commands/code-review.md) — read the full command file first. Announce: "Using /code-review to review Round N."

1. Run `/code-review` — structure, DRY, naming, patchwork vs root-cause
2. Log findings as `ch-r{N}-{seq}` with `source=round-{N}`
3. Zero issues → sentinel `ch-r{N}-000`

## Phase 7 — Receive + backlog reflect (Round N)

Required when `code_changed=yes`.

### Phase 7a — Receive (mandatory skill + command)

Read Superpowers **receiving-code-review** skill, then invoke [`/receiving-code-review`](../../../.cursor/commands/receiving-code-review.md).

1. Triage every round-N row: `fix-now` | `backlog` | `closed` | `pushback`
2. Implement fix-now in worktree; re-verify build if needed
3. Route cross-cutting items to Worker BACKLOG; else REVIEW_FINDINGS or BUG_BACKLOG

### Phase 7b — Backlog reflect (mandatory)

Every deferred finding → backlog row with id, priority, AC. Set `backlog_ref` on the REVIEW_FINDINGS row. Create `ch-*` / BUG_BACKLOG / REFACTOR_BACKLOG items for deferred findings. Cannot close until complete.

## Phase 8 — Close

When `worktree_status=active`:

```bash
bash tools/cursor-loop/scripts/instance_worktree.sh merge . --loop-id code-health \
  --apply
bash tools/cursor-loop/scripts/instance_worktree.sh remove . --loop-id code-health \
  --apply
```

Then set `worktree_status=none` and clear worktree path/branch/item fields.

HISTORY, SCAN_COVERAGE, CHECKPOINT, backlogs. No warn/fail on touched files without backlog entry.

## Phase 9 — Arm

Follow [`../_template/RITUAL.base.md`](../_template/RITUAL.base.md) Phase 9 checklist.

**This window:** `loop_id=code-health`, env from [INSTANCE.md](INSTANCE.md) Loop config table.  
**Evidence:** `--evidence <ch-id>` on checkpoint.
