# Ritual — code-health

**extends:** `engineer` (refactor variant)  
**base:** [`../_template/RITUAL.base.md`](../_template/RITUAL.base.md)

## Phase 2 — Orient

`git status`; `git log -10 --oneline`; `git diff --stat`; patchwork clusters; update `LAST_REVIEW`.

## Phase 3 — Select

Resume `IN_PROGRESS` OR top `REFACTOR_BACKLOG` / `BUG_BACKLOG` OR next `SCAN_COVERAGE` row.

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
cd server && python -m compileall app_api   # when Python touched
git diff --stat HEAD -- pwa/ server/
git diff --stat --cached -- pwa/ server/
```

Set `code_changed`; increment `review_round` if yes. Record `review_diff_range`.

**Regression spot-checks (when area touched):**

| Area | Check |
|------|--------|
| Meal plan queue | Dismiss clears failed ids; remote banner navigates |
| Log swipe | Directions + undo toast |
| Cards | Search/filter + FAB create |
| Offline | Queue banners when server offline |

## Phase 6 — Code review (Round N)

Required when `code_changed=yes`. Phase 4 checklist = self-check; Phase 6 = formal review.

1. [`/code-review`](../../../.cursor/commands/code-review.md) — structure, DRY, naming, patchwork vs root-cause
2. Log findings as `ch-r{N}-{seq}` with `source=round-{N}`
3. Zero issues → sentinel `ch-r{N}-000`

## Phase 7 — Receive review (Round N)

Required when `code_changed=yes`.

1. [`/receiving-code-review`](../../../.cursor/commands/receiving-code-review.md) on round-N rows
2. Implement fix-now; re-verify build if needed
3. Route cross-cutting items to Worker BACKLOG; else REVIEW_FINDINGS or BUG_BACKLOG

## Phase 8 — Close

HISTORY, SCAN_COVERAGE, CHECKPOINT, backlogs. No warn/fail on touched files without backlog entry.

## Phase 9 — Arm

Follow [`../_template/RITUAL.base.md`](../_template/RITUAL.base.md) Phase 9 checklist.

**This window:** `loop_id=code-health`, env from [INSTANCE.md](INSTANCE.md) Loop config table.  
**Evidence:** `--evidence <ch-id>` on checkpoint.
