# Ritual — worker-relay

**extends:** `engineer`  
**base:** [`../_template/RITUAL.base.md`](../_template/RITUAL.base.md)

## Phase 2 — Orient

STATE CHECKPOINT, IN_PROGRESS, BACKLOG; `git status`; `git log -3`; update `LAST_REVIEW`.

## Phase 3 — Select

Top BACKLOG item or resume IN_PROGRESS. If BACKLOG < 3, refill from BRAINSTORM first.

## Phase 4 — Execute

Ship `task-*` feature code. Chain items in same wake when possible.

## Phase 5 — Verify

```bash
cd pwa && npm run build
python3 -c "import app_api.main"   # if server/ changed
curl -s http://127.0.0.1:8787/healthz   # optional, server running
git diff --stat HEAD -- pwa/ server/
git diff --stat --cached -- pwa/ server/
```

Set `code_changed`; increment `review_round` if yes. Record `review_diff_range`.

Area-specific checks when touching: Home rings, Log swipe/scan, Day timeline, Cards CRUD, Agent chat.

## Phase 6 — Code review (Round N)

Required when `code_changed=yes`.

1. [`/code-review`](../../../.cursor/commands/code-review.md) on diff — bugs, regressions, missing tests, active `task-*` AC
2. Log findings as `wk-r{N}-{seq}` with `source=round-{N}`
3. Zero issues → sentinel `wk-r{N}-000`

## Phase 7 — Receive review (Round N)

Required when `code_changed=yes`.

1. [`/receiving-code-review`](../../../.cursor/commands/receiving-code-review.md) on round-N rows
2. Implement fix-now in `pwa/` / `server/`; re-verify build if needed
3. Backlog non-blockers as new `task-*` or REVIEW_FINDINGS `wk-*`

## Phase 8 — Close

HISTORY, CHECKPOINT (`phase=8-close`, `review_status`), clear IN_PROGRESS, commit.

## Phase 9 — Arm

Follow [`../_template/RITUAL.base.md`](../_template/RITUAL.base.md) Phase 9 checklist.

**This window:** `loop_id=worker-relay`, env from [INSTANCE.md](INSTANCE.md) Loop config table.  
**Evidence:** `--evidence <relay-id>` on checkpoint.
