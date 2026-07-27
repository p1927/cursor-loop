# Code Review

Review the current branch changes or uncommitted diff with a critical eye.

## Mandatory invocation (Phase 6)

**You MUST invoke this Cursor command in Phase 6** — read this entire file first; do not freestyle review or substitute ad-hoc checklists.

Announce: **"Using /code-review to review Round N diff"** then follow the process below.

**Required on every code-changing tick** in all window instances (`worker-relay`, `ux-relay`, `code-health`, `po-relay`) before Phase 8 close.

Trigger: `CHECKPOINT.code_changed=yes` (set at end of Phase 5 via `prepare_review_tick.sh`).

If no diff in **this window's review scope** → skip with `review_status=skipped` and `review_skip_reason`.

Phase 7 **must** follow with [`/receiving-code-review`](receiving-code-review.md) on the same Round N.

## Review scope (per window)

Review **all changes this window made** — not a global `pwa/`/`server/` filter unless that is the window's scope.

Run Phase 5 prep to print paths:

```bash
bash tools/cursor-loop/scripts/prepare_review_tick.sh . \
  --state-file <STATE.md> --loop-id <loop_id> \
  --apply
```

| Window | Default review paths |
|--------|----------------------|
| worker-relay | `pwa/`, `server/`, instance bundle |
| ux-relay | `pwa/`, instance bundle |
| code-health | `pwa/`, `server/`, `tools/cursor-loop/`, instance bundle |
| po-relay | `docs/window-instances/po-relay/`, maintenance/agents docs, instance bundle |

Phase 6 `/code-review` must cover the full diff on those paths (use `CHECKPOINT.review_diff_range` + `git diff` with the printed `review_paths`).

**PO exception:** When reviewing shipped product code (typical every tick), also run `git diff main...HEAD` on `pwa/` and `server/` per [`po-relay/RITUAL.md`](../../docs/window-instances/po-relay/RITUAL.md) — that is additive to PO's own doc mutations.

## Focus areas

1. **Bugs** — logic errors, null/undefined paths, race conditions, off-by-one
2. **Regressions** — behavior changes that break existing flows
3. **Security** — injection, auth gaps, secrets in code
4. **Missing tests** — critical paths without coverage
5. **Performance** — unnecessary re-renders, waterfalls, layout thrashing

## Process

0. If `CHECKPOINT.review_changed_files` is empty or stale vs git, run Phase 5 prep with `--apply` first.
1. Read `review_paths` and `CHECKPOINT.review_changed_files` from Phase 5 prep (or wake JSON `changed_files`).
2. Run `git diff --name-only` on `review_paths`; **open and read every file** in `changed_files`.
3. Read changed files in full context — not just diff hunks.
4. List findings by severity: critical, high, medium, low.
5. For each finding: cite `path:line` (or file-level for config/docs), issue, suggested fix.

**Sentinel rule:** `{prefix}-r{N}-000` is allowed **only** when `changed_files` is empty. Arm gate and stop hook reject sentinel-only review when files changed.

## Round numbering

Use `CHECKPOINT.review_round` as **Round N**.

- Log every finding with id `{prefix}-r{N}-{seq}` (instance prefix: `rf`, `ux`, `pr`, `ch`)
- Set `source=round-{N}` in REVIEW_FINDINGS
- If zero issues, add sentinel row:

```
{prefix}-r{N}-000 | low | No issues in reviewed diff | round-{N} /code-review | closed | — | closed
```

## Output format

Log findings to STATE `REVIEW_FINDINGS` table:

| id | severity | finding | source | action | backlog_ref | status |

Leave `action` as `open` or unset until Phase 7 triage.

## Worker window

When invoked from **worker-relay**, add feature lens:

- Bugs and regressions in shipped diff
- AC coverage for active `relay-*` backlog item
- Missing tests on critical paths
- Cross-tab regressions (Home, Log, Day, Cards, Agent)

## PO window — custom instructions

When invoked from **po-relay**, add product owner lens:

- Shipped vs backlog alignment
- Missing features (relay-* candidates with RICE)
- UI proposals (prop-ui-*)
- Quality flags (maint-* / ch-* for Code window)
- AC gaps on open backlog items

Log structured output as REVIEW_FINDINGS rows (not freeform blocks). See [`po-relay/RITUAL.md`](../../docs/window-instances/po-relay/RITUAL.md).

## UX window

Add 390px visual check per [`ux-relay/RITUAL.md`](../../docs/window-instances/ux-relay/RITUAL.md) Phase 5.

## Code window

Focus on structure, DRY, naming clarity, patchwork vs root-cause fixes. Include `tools/cursor-loop/` when this window changed loop package code.

## Next step

After logging findings, proceed to **Phase 7a** — read the Superpowers **receiving-code-review** skill and invoke [`/receiving-code-review`](receiving-code-review.md) for the same Round N, then complete **Phase 7b Backlog reflect** (mandatory).
