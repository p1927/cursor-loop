# Ritual — ux-relay

**extends:** `designer`  
**base:** [`../_template/RITUAL.base.md`](../_template/RITUAL.base.md)

## Phase 2 — Orient

Read `../po-relay/STATE.md` `UI_PROPOSALS`; update `LAST_REVIEW`; `git status`.

## Phase 3 — Select

Top agreed `ui-*` from `UI_POLISH_BACKLOG`; resume `IN_PROGRESS` if set.

**Worktree (code items):** mandatory prep then create before Phase 4:

```bash
bash tools/cursor-loop/scripts/prepare_select_tick.sh . \
  --state-file docs/window-instances/ux-relay/STATE.md \
  --loop-id ux-relay
bash tools/cursor-loop/scripts/instance_worktree.sh create . \
  --loop-id ux-relay \
  --item-id <backlog-id> \
  --state-file docs/window-instances/ux-relay/STATE.md
```

Phases 4–7 run inside `WORKTREE_PATH` (create auto-patches CHECKPOINT).

## Phase 4 — Execute

1. Web research how reference app implements the target pattern
2. ui-ux-pro-max design-system search
3. 21st-cache / 21st-cli before hand-writing components
4. Ship UI diff for selected `ui-*`

## Phase 5 — Verify

```bash
cd pwa && npm run build
bash tools/cursor-loop/scripts/prepare_review_tick.sh . \
  --state-file docs/window-instances/ux-relay/STATE.md \
  --loop-id ux-relay \
  --apply
```

Apply script output: set `code_changed`, increment `review_round` if yes, set `review_status=pending`, record `review_diff_range`.

**API (if server touched):**

```bash
python3 -c "import habits_api.main"
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

**Mandatory:** Invoke [`/code-review`](../../../.cursor/commands/code-review.md) — read the full command file first. Announce: "Using /code-review to review Round N."

1. Run `/code-review` on UI diff + 390px visual parity vs IDENTITY matrix
2. Log findings as `ux-r{N}-{seq}` with `source=round-{N}`
3. Zero issues → sentinel `ux-r{N}-000`

## Phase 7 — Receive + backlog reflect (Round N)

Required when `code_changed=yes`.

### Phase 7a — Receive (mandatory skill + command)

Read Superpowers **receiving-code-review** skill, then invoke [`/receiving-code-review`](../../../.cursor/commands/receiving-code-review.md).

1. Triage every round-N row: `fix-now` | `backlog` | `closed` | `pushback`
2. Implement fix-now in worktree / `pwa/`; re-verify build + 390px if needed
3. Also triage `UI_PROPOSALS`; log `UX_GAPS` for PO if new gaps found

### Phase 7b — Backlog reflect (mandatory)

Every deferred finding → backlog row with id, priority, AC. Set `backlog_ref` on the REVIEW_FINDINGS row. Create `ui-*` items in UI_POLISH_BACKLOG for deferred findings. Cannot close until complete.

## Phase 8 — Close

When `worktree_status=active`:

```bash
bash tools/cursor-loop/scripts/instance_worktree.sh merge . --loop-id ux-relay \
  --apply
bash tools/cursor-loop/scripts/instance_worktree.sh remove . --loop-id ux-relay \
  --apply
```

Then set `worktree_status=none` and clear worktree path/branch/item fields.

HISTORY, CHECKPOINT, backlog checkboxes.

## Phase 9 — Arm

Follow [`../_template/RITUAL.base.md`](../_template/RITUAL.base.md) Phase 9 checklist.

**This window:** `loop_id=ux-relay`, env from [INSTANCE.md](INSTANCE.md) Loop config table.  
**Evidence:** `--evidence <ui-id>` on checkpoint.
