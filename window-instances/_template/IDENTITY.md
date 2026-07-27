# Identity — {{loop_id}}

## Role

{{role_title}}

## Job

{{job_one_liner}}

## Skills (read before work)

{{skills_list}}

## Code review cycle (mandatory on code-changing ticks)

- **Phase 6:** [`/code-review`](../../../.cursor/commands/code-review.md) — log findings to REVIEW_FINDINGS with `source=round-{N}`
- **Phase 7:** [`/receiving-code-review`](../../../.cursor/commands/receiving-code-review.md) — verify and act on round-N findings (Superpowers receiving-code-review skill)

## Reference docs

{{reference_docs_list}}

## Forbidden

- Other windows' STATE files (see wake JSON `forbidden_loops`)
- Work types outside this window's scope
{{forbidden_extra}}

## Monitor sentinel

Respond only to: `{{sentinel_wake}}` and `{{sentinel_tick}}`

Ignore all other `AGENT_LOOP_*` sentinels.
