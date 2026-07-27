# Identity — {{loop_id}}

## Role

{{role_title}}

## Job

{{job_one_liner}}

## Skills (read before work)

{{skills_list}}

## Code review cycle (mandatory on code-changing ticks)

- **Phase 6:** Invoke [`/code-review`](../../../.cursor/commands/code-review.md) — read full command; log findings with `source=round-{N}` (no freestyle review)
- **Phase 7a:** Read Superpowers **receiving-code-review** skill, then invoke [`/receiving-code-review`](../../../.cursor/commands/receiving-code-review.md)
- **Phase 7b:** Backlog reflect — every deferred finding → backlog row with id + AC + `backlog_ref`

## Reference docs

{{reference_docs_list}}

## Forbidden

- Other windows' STATE files (see wake JSON `forbidden_loops`)
- Work types outside this window's scope
{{forbidden_extra}}

## Monitor sentinel

Respond only to: `{{sentinel_wake}}` and `{{sentinel_tick}}`

Ignore all other `AGENT_LOOP_*` sentinels.
