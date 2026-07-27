# Ritual — {{loop_id}}

**extends:** `{{archetype}}`  
**base:** [`../_template/RITUAL.base.md`](../_template/RITUAL.base.md)

Follow the universal 9-phase ritual. Archetype `{{archetype}}` defines phases 4–6 execute/verify/review lenses.

## Mandatory review cycle

When `code_changed=yes` after Phase 5:

1. **Phase 6** — [`/code-review`](../../../.cursor/commands/code-review.md) Round N → log `REVIEW_FINDINGS` with `source=round-{N}`
2. **Phase 7** — [`/receiving-code-review`](../../../.cursor/commands/receiving-code-review.md) Round N → triage/implement fix-now

See [`../_template/RITUAL.base.md`](../_template/RITUAL.base.md) for full Phase 6/7 workflow.

## Local notes

{{ritual_local_notes}}

## Phase gate

Update CHECKPOINT.phase after each phase completes. See [`SPEC.md`](../_template/SPEC.md) for gate rules.
