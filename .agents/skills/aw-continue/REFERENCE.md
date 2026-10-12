# Stage handoff: template and rules

One rolling file per OpenSpec change: `openspec/changes/<change-id>/aw-handoff.md`.

`/aw-pr` archives before it opens the PR. Archive moves the file to `openspec/changes/archive/<YYYY-MM-DD>-<change-id>/aw-handoff.md`. After that, read and update it there. Do not recreate the active change directory.

Commit this file with the branch. Same for sibling `aw-scorecard.md` / `aw-triage.md`.

## When to write

At the end of a stage, when artifacts are complete and the footer would say `New session? yes`. Overwrite; do not append.

## Scorecard / triage size

| Size | Where |
|------|-------|
| Table 40 lines or fewer | Inline under `## scorecard` / `## triage` |
| Longer | Sibling `aw-scorecard.md` / `aw-triage.md`; the handoff keeps status, blocker count, and a link |

## Template

```markdown
# aw-handoff: <change-id>
updated: <ISO-8601>
stage_done: <propose|issue|implement|test|ship-review|pr|triage|...>
status: ready_for_next

## pointers
- repo: <path or remote>
- branch: <name>
- worktree: <absolute path or none>
- base_sha: <sha of origin/main at branch creation unless overridden>
- pr: <url or none>
- issues: <#123, #124 or none>
- ci: <green|red|pending|none>

## facts
- openspec: openspec/changes/<change-id>/
- verification: <3 lines max; gates run and result>

## scorecard
- status: READY|NOT READY
- blockers: <n>
- full: openspec/changes/<change-id>/aw-scorecard.md

## triage
<optional; same size rule>

## read_targets
- path/to/file.rs:120-155 - why this range matters

## suggested_next_step
- Next: <skill>
- New session?: yes|no
- Carry forward: openspec/changes/<change-id>/aw-handoff.md
```

## read_targets

When summarizing code for a later stage or a cheap reader: bullet findings, no prose dump; then one `path:start-end - why` per range the next agent may need. The next agent reads only those ranges.

## Footer

This file owns the footer. Stage skills write the handoff, set Next and New session, then print:

```text
## Suggested next step
- **Next:** <from handoff>
- **New session?** yes|no - <reason>
- **Carry forward:** openspec/changes/<id>/aw-handoff.md
- **Hop:** new session, then `/aw-continue <id>`
```

| Stage done | Common Next |
|------------|-------------|
| propose (issues still needed) | `/aw-create-issue` |
| propose or issue | `/aw-implement` |
| implement | `/aw-test` (or `/aw-ship-review`) |
| test_failed | `/aw-implement` (session resumption: `New session? no`) |
| test_passed | `/aw-ship-review` |
| review_failed | `/aw-implement` (session resumption: `New session? no`) |
| ship-review READY / ship_review_ready | `/aw-pr` |
| pr open | CI watch, then human merge; feedback goes to `/aw-address-pr-issues` |

## Policy

- Merge: only when the human explicitly asks.
- Base and worktree: latest `origin/main`, isolated worktree, record paths in `## pointers`, remove when done and confirmed.
- Gates: `/aw-ship-review` owns them.
- CI monitor: after push, watch checks and write `ci:`. Red: fix stage in a new session. Green: human merge.
