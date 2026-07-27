# Receiving Code Review

Process findings from Phase 6 `/code-review` for the current review round.

## Mandatory skill + command (Phase 7)

**Phase 7 has two mandatory sub-steps — both required before Phase 8:**

| Sub-step | What to use |
|----------|-------------|
| **7a Receive** | Superpowers **receiving-code-review** skill **then** this Cursor command |
| **7b Backlog reflect** | Deferred findings → backlog rows with id + AC (see below) |

### 7a — Read skill first

1. Read the Superpowers skill: `receiving-code-review` (READ → VERIFY → EVALUATE → RESPOND → IMPLEMENT)
2. Announce: **"Using receiving-code-review skill to triage Round N"**
3. Invoke this command (`/receiving-code-review`) and follow the process below

Do not triage from memory. Do not skip the skill.

**Required when `CHECKPOINT.code_changed=yes`**, immediately after Phase 6 `/code-review`.

Input: `REVIEW_FINDINGS` rows where `source=round-{N}` and `N = CHECKPOINT.review_round`.

## Process (7a)

```
1. READ:    All round-N findings without reacting
2. VERIFY:  Check each against codebase reality
3. EVALUATE: Technically sound for THIS codebase?
4. RESPOND:  Technical acknowledgment or reasoned pushback
5. IMPLEMENT: fix-now items one at a time, test each
6. TRIAGE:   Set action on every round-N row
```

## Forbidden

- Performative agreement ("Great point!", "You're absolutely right!")
- Blind implementation before verification
- Batch fix-now without testing each change
- Skipping Phase 7b when any finding is deferred

## Triage actions (7a)

Update each round-N row:

| action | When |
|--------|------|
| `fix-now` | Valid finding; implement before Phase 8 |
| `backlog` | Valid but deferred — **must** complete Phase 7b |
| `closed` | Already fixed, not applicable, or zero-finding sentinel |
| `pushback` | Invalid for this codebase; document reason in HISTORY |

Set `status=closed` when resolved; `status=open` when deferred to backlog.

## Phase 7b — Backlog reflect (mandatory)

**Separate reflection step — always run after 7a**, even when all findings were fix-now or closed.

Every deferred, low-priority, or non-blocking finding **must** land in a backlog so a future agent can pick it up without re-discovery.

For each round-N row with `action=backlog`:

1. **Create** a backlog item in the correct section (this window's BACKLOG or target window per PO routing):
   - Unique id (`relay-*`, `ui-*`, `ch-*`, `prop-ui-*`, `maint-*`, or `{prefix}-review-r{N}-{seq}`)
   - Priority (low/medium/high)
   - Acceptance criteria (Given/When/Then or concrete done-when)
   - Notes linking to finding id
2. **Link** — set `REVIEW_FINDINGS.backlog_ref` to that id
3. **Leave open** — finding `status=open` until backlog item is shipped; backlog checkbox `- [ ]`

**Low/medium findings you are not fixing this tick:** set `action=backlog` and complete steps 1–3 — do not leave as untriaged `open`.

### PO routing (po-relay)

Do not ship code. Route backlog items to target STATE files:

| Finding type | Target |
|--------------|--------|
| Features | `worker-relay/STATE.md` BACKLOG (`relay-*`) |
| UI polish | `UI_PROPOSALS` (`prop-ui-*`) |
| Refactors / quality | `QUALITY_BACKLOG` (`maint-*`, `ch-*`) |
| UX gaps | note + ux-relay handoff |

Still set `backlog_ref` on the REVIEW_FINDINGS row to the id you created in the target backlog.

## fix-now order

1. Clarify unclear items first — do not partial-implement
2. Blocking issues (breaks, security)
3. Simple fixes (typos, imports)
4. Complex fixes (refactoring, logic)
5. Re-run Phase 5 verify if code changed

## Output (end of Phase 7)

1. Updated `REVIEW_FINDINGS` rows for round-N (every row has `action` + `status`)
2. Backlog rows for every `action=backlog` finding (`backlog_ref` set)
3. Optional HISTORY triage note (especially for pushbacks)
4. Set `review_status=done` (all closed/pushback) or `triaged` (open backlog items remain)
5. Set `CHECKPOINT.last_reviewed_round` to N
6. Set `CHECKPOINT.phase=7-triage`

## Window lenses

### worker-relay / code-health / ux-relay

Implement fix-now in worktree or `pwa/` / `server/`. Re-verify build after fixes.

### po-relay

Route only — no code shipping in this window.

## Pushback example

```
Finding: "Remove legacy API shim"
Action: pushback
Reason: Shim required for Safari 16 localStorage quota — verified in mealPlanQueueStorage.ts
```

Log pushback reason in HISTORY; set finding `status=closed`, `action=pushback`.

## Gate

Cannot proceed to Phase 8 until:

- Every round-N row has `action` and `status` set
- Every `action=backlog` row has non-empty `backlog_ref` matching a backlog entry in STATE (or target window STATE for PO)

**Enforcement:** `arm-wake.sh`, `checkpoint-loop.py --product`, and the **stop hook** block incomplete review (including when wake=ARMED). Manifest must match git (`review_changed_files` / `review_fingerprint`).
