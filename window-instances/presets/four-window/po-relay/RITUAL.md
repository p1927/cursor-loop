# Ritual — po-relay

**extends:** `product`  
**base:** [`../_template/RITUAL.base.md`](../_template/RITUAL.base.md)

## Phase 2 — Orient

Read CHECKPOINT, backlogs, `git log -5 --oneline`; update `LAST_REVIEW`.

## Phase 4 — Execute (3-lens brainstorm)

Run **three separate lens sessions**; append each to `BRAINSTORM_LOG` with tag.

### UX designer lens

- Visual hierarchy on 390px — primary action in 2s?
- Nielsen heuristics: error prevention, recognition over recall
- Per-tab gap vs inspiration matrix (`ux-relay/IDENTITY.md`)
- AI-slop detection — generic grids, purple gradients
- Seed/refine `prop-ui-*` or `ux-*` candidates

### Product owner lens

- Each backlog item traces to user outcome?
- RICE top 5 candidates
- Merge duplicates; drop vague items
- Rewrite AC as Given/When/Then
- Feed `task-*` to `worker-relay/STATE.md` BACKLOG

### Business owner lens

- Core job: "Track health habits without spreadsheet friction"
- Hook loop: trigger → action → variable reward → investment
- Retention: rings viewed + food logged
- ROI vs manual Sheets entry

## Phase 5 — Verify

Log all three lenses in `BRAINSTORM_LOG` with timestamp. At least one backlog mutation (not read-only).

```bash
git diff --stat HEAD -- pwa/ server/
git diff --stat --cached -- pwa/ server/
```

Set `code_changed` (usually `no` for PO — PO does not ship code). If reviewing others' shipped code in Phase 6, set `review_diff_range` to branch range (e.g. `main...HEAD`).

## Phase 6 — Product code review (Round N)

Run when reviewing shipped code (typical every tick) OR when `code_changed=yes`.

1. `git log -10 --oneline` + `git diff main...HEAD --stat`
2. Skim `pwa/src/` and `server/` (read-only)
3. [`/code-review`](../../../.cursor/commands/code-review.md) with PO lens: missing features, weak AC, RICE, cross-feed
4. Validate `UI_PROPOSALS`; read `ux-relay/STATE.md` `UX_GAPS`
5. Cross-check `worker-relay/STATE.md` BACKLOG vs shipped code

Log **all** output as REVIEW_FINDINGS rows (`pr-r{N}-{seq}`, `source=round-{N}`). Do not use freeform Product review blocks.

Categories to cover each tick:

- Shipped vs backlog
- Missing features (`task-*`)
- UI proposals (`prop-ui-*`)
- Quality flags (`maint-*` / `ch-*`)
- AC gaps

Zero issues → sentinel `pr-r{N}-000`.

## Phase 7 — Receive review (Round N)

1. [`/receiving-code-review`](../../../.cursor/commands/receiving-code-review.md) on round-N rows
2. Route valid findings: fix-now (handoff note) | target window backlog | closed | pushback
3. Do not implement code — feed Worker, UX, Code backlogs

Also route: `UI_PROPOSALS` triage, `UX_GAPS` promotion where agreed.

## Phase 8 — Close

Update CHECKPOINT, HISTORY, promote `UX_GAPS` → `UI_PROPOSALS` where agreed.

## Phase 9 — Arm

Follow [`../_template/RITUAL.base.md`](../_template/RITUAL.base.md) Phase 9 checklist.

**This window:** `loop_id=po-relay`, env from [INSTANCE.md](INSTANCE.md) Loop config table.  
**Evidence:** `--evidence <backlog-id-or-path>` on checkpoint.
