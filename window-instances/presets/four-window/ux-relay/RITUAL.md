# Ritual — ux-relay

**extends:** `designer`  
**base:** [`../_template/RITUAL.base.md`](../_template/RITUAL.base.md)

## Phase 2 — Orient

Read `../po-relay/STATE.md` `UI_PROPOSALS`; update `LAST_REVIEW`; `git status`.

## Phase 3 — Select

Top agreed `ui-*` from `UI_POLISH_BACKLOG`; resume `IN_PROGRESS` if set.

## Phase 4 — Execute

1. Web research how reference app implements the target pattern
2. ui-ux-pro-max design-system search
3. 21st-cache / 21st-cli before hand-writing components
4. Ship UI diff for selected `ui-*`

## Phase 5 — Verify

**Build (required):**

```bash
cd pwa && npm run build
git diff --stat HEAD -- pwa/ server/
git diff --stat --cached -- pwa/ server/
```

Set `code_changed`; increment `review_round` if yes. Record `review_diff_range`.

**API (if server touched):**

```bash
python3 -c "import app_api.main"
```

**Live checks (when area touched):**

| Area | Steps |
|------|-------|
| Home | Rings; pull-to-refresh; decision card |
| Log | Swipe right=log; scan flow; queue banner |
| Day | Timeline + habit grid |
| Cards | CRUD persists |
| Agent | Chat streams; voice sheet |
| Settings | Server status |

**UI polish checklist:**

- [ ] ui-ux-pro-max `--design-system` run noted in HISTORY
- [ ] 21st search logged
- [ ] Visual check at **390px**
- [ ] `prefers-reduced-motion` not broken

## Phase 6 — Code review (Round N)

Required when `code_changed=yes`.

1. [`/code-review`](../../../.cursor/commands/code-review.md) on UI diff + 390px visual parity vs IDENTITY matrix
2. Log findings as `ux-r{N}-{seq}` with `source=round-{N}`
3. Zero issues → sentinel `ux-r{N}-000`

## Phase 7 — Receive review (Round N)

Required when `code_changed=yes`.

1. [`/receiving-code-review`](../../../.cursor/commands/receiving-code-review.md) on round-N rows
2. Implement fix-now UI fixes; re-verify build + 390px if needed
3. Also triage `UI_PROPOSALS`; log `UX_GAPS` for PO if new gaps found

## Phase 8 — Close

HISTORY, CHECKPOINT, backlog checkboxes.

## Phase 9 — Arm

Follow [`../_template/RITUAL.base.md`](../_template/RITUAL.base.md) Phase 9 checklist.

**This window:** `loop_id=ux-relay`, env from [INSTANCE.md](INSTANCE.md) Loop config table.  
**Evidence:** `--evidence <ui-id>` on checkpoint.
