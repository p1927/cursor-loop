# Code Review

Review the current branch changes or uncommitted diff with a critical eye.

## Mandatory

**Required on every code-changing tick** in all window instances (`worker-relay`, `ux-relay`, `code-health`, `po-relay`) before Phase 8 close.

Trigger: `CHECKPOINT.code_changed=yes` (set at end of Phase 5).

If no code diff under `pwa/` or `server/` → skip with `review_status=skipped` and `review_skip_reason`.

Phase 7 **must** follow with [`/receiving-code-review`](receiving-code-review.md) on the same Round N.

## Focus areas

1. **Bugs** — logic errors, null/undefined paths, race conditions, off-by-one
2. **Regressions** — behavior changes that break existing flows
3. **Security** — injection, auth gaps, secrets in code
4. **Missing tests** — critical paths without coverage
5. **Performance** — unnecessary re-renders, waterfalls, layout thrashing

## Process

1. Run `git diff` (or `git diff main...HEAD` for branch review) on `CHECKPOINT.review_diff_range`
2. Read changed files in context — not just the diff hunks
3. List findings by severity: critical, high, medium, low
4. For each finding: file path, issue, suggested fix

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

Focus on structure, DRY, naming clarity, patchwork vs root-cause fixes.

## Next step

After logging findings, proceed to Phase 7 [`/receiving-code-review`](receiving-code-review.md) for the same Round N.
