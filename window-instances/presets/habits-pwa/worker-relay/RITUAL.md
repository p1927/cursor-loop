# Ritual — worker-relay

**extends:** `engineer`  
**base:** [`../_template/RITUAL.base.md`](../_template/RITUAL.base.md)

## Phase 2 — Orient

STATE CHECKPOINT, IN_PROGRESS, BACKLOG; `git status`; `git log -3`; update `LAST_REVIEW`.

## Phase 3 — Select

Top BACKLOG item or resume IN_PROGRESS. If BACKLOG < 3, refill from BRAINSTORM first.

**Worktree (code items):** mandatory prep then create before Phase 4:

```bash
bash tools/cursor-loop/scripts/prepare_select_tick.sh . \
  --state-file docs/window-instances/worker-relay/STATE.md \
  --loop-id worker-relay
bash tools/cursor-loop/scripts/instance_worktree.sh create . \
  --loop-id worker-relay \
  --item-id <backlog-id> \
  --state-file docs/window-instances/worker-relay/STATE.md
```

Phases 4–7 run inside `WORKTREE_PATH` (create auto-patches CHECKPOINT).

## Phase 4 — Execute

Ship `relay-*` feature code. Chain items in same wake when possible.

## Phase 5 — Verify

```bash
cd pwa && npm run build
python3 -c "import habits_api.main"   # if server/ changed
curl -s http://127.0.0.1:8787/healthz   # optional, server running
bash tools/cursor-loop/scripts/prepare_review_tick.sh . \
  --state-file docs/window-instances/worker-relay/STATE.md \
  --loop-id worker-relay \
  --apply
```

Apply script output: set `code_changed`, increment `review_round` if yes, set `review_status=pending`, record `review_diff_range`. Cannot carry `review_status=done` from a prior tick when git diff is non-empty.

Area-specific checks when touching: Home rings, Log swipe/scan, Day timeline, Cards CRUD, Agent chat.

## Phase 6 — Code review (Round N)

Required when `code_changed=yes`.

**Mandatory:** Invoke [`/code-review`](../../../.cursor/commands/code-review.md) — read the full command file first. Announce: "Using /code-review to review Round N."

1. Run `/code-review` on diff — bugs, regressions, missing tests, active `relay-*` AC
2. Log findings as `rf-r{N}-{seq}` with `source=round-{N}`
3. Zero issues → sentinel `rf-r{N}-000`

## Phase 7 — Receive + backlog reflect (Round N)

Required when `code_changed=yes`.

### Phase 7a — Receive (mandatory skill + command)

Read Superpowers **receiving-code-review** skill, then invoke [`/receiving-code-review`](../../../.cursor/commands/receiving-code-review.md).

1. Triage every round-N row: `fix-now` | `backlog` | `closed` | `pushback`
2. Implement fix-now in worktree / `pwa/` / `server/`; re-verify build if needed

### Phase 7b — Backlog reflect (mandatory)

Every deferred finding → backlog row with id, priority, AC. Set `backlog_ref` on the REVIEW_FINDINGS row. Create `relay-*` items in BACKLOG for deferred findings. Cannot close until complete.

## Phase 8 — Close

When `worktree_status=active`:

```bash
bash tools/cursor-loop/scripts/instance_worktree.sh merge . --loop-id worker-relay \
  --apply
bash tools/cursor-loop/scripts/instance_worktree.sh remove . --loop-id worker-relay \
  --apply
```

Then set `worktree_status=none` and clear worktree path/branch/item fields.

HISTORY, CHECKPOINT (`phase=8-close`, `review_status`), clear IN_PROGRESS, commit.

## Phase 9 — Arm

Follow [`../_template/RITUAL.base.md`](../_template/RITUAL.base.md) Phase 9 checklist.

**This window:** `loop_id=worker-relay`, env from [INSTANCE.md](INSTANCE.md) Loop config table.  
**Evidence:** `--evidence <relay-id>` on checkpoint.
