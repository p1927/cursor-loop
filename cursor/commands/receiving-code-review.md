# Receiving Code Review

Process findings from Phase 6 `/code-review` for the current review round. Follow the Superpowers **receiving-code-review** skill: verify before implementing, no performative agreement.

## Mandatory

**Required on every code-changing tick** when `CHECKPOINT.code_changed=yes`, immediately after Phase 6.

Input: `REVIEW_FINDINGS` rows where `source=round-{N}` and `N = CHECKPOINT.review_round`.

## Process

```
1. READ:    All round-N findings without reacting
2. VERIFY:  Check each against codebase reality
3. EVALUATE: Technically sound for THIS codebase?
4. RESPOND:  Technical acknowledgment or reasoned pushback
5. IMPLEMENT: fix-now items one at a time, test each
6. TRIAGE:   Update action/status on every round-N row
```

Skill reference: Superpowers `receiving-code-review` (READ → VERIFY → EVALUATE → RESPOND → IMPLEMENT).

## Forbidden

- Performative agreement ("Great point!", "You're absolutely right!")
- Blind implementation before verification
- Batch fix-now without testing each change

## Triage actions

Update each round-N row:

| action | When |
|--------|------|
| `fix-now` | Valid finding; implement before Phase 8 |
| `backlog` | Valid but deferred; add backlog id in `backlog_ref` |
| `closed` | Already fixed, not applicable, or zero-finding sentinel |
| `pushback` | Invalid for this codebase; document reason in HISTORY |

Set `status=closed` when resolved; `status=open` when deferred to backlog.

## fix-now order

1. Clarify unclear items first — do not partial-implement
2. Blocking issues (breaks, security)
3. Simple fixes (typos, imports)
4. Complex fixes (refactoring, logic)
5. Re-run Phase 5 verify if code changed

## Output

1. Updated `REVIEW_FINDINGS` rows for round-N
2. Optional HISTORY triage note (especially for pushbacks)
3. Set `review_status=done` (all closed/pushback) or `triaged` (open backlog items remain)
4. Set `CHECKPOINT.phase=7-triage`

## Window lenses

### worker-relay / code-health / ux-relay

Implement fix-now in `pwa/` or `server/` directly. Re-verify build after fixes.

### po-relay

Do not ship code. Route valid findings to target window backlogs:

- Features → `worker-relay/STATE.md` BACKLOG (`relay-*`)
- UI → `UI_PROPOSALS` (`prop-ui-*`)
- Refactors → `QUALITY_BACKLOG` (`maint-*`, `ch-*`)
- UX gaps → note for ux-relay handoff

## Pushback example

```
Finding: "Remove legacy API shim"
Action: pushback
Reason: Shim required for Safari 16 localStorage quota — verified in mealPlanQueueStorage.ts
```

Log pushback reason in HISTORY; set finding `status=closed`, `action=pushback`.

## Gate

Cannot proceed to Phase 8 until every round-N row has `action` and `status` set.
