---
name: aw-continue
description: Resumes a staged workflow from openspec/changes/<id>/aw-handoff.md. Reads the handoff, follows read_targets with offset/limit instead of whole files, then starts the named next aw- skill. Use when the user says "continue", "aw-continue", "resume handoff", "next stage", or gives a change id after a prior stage ended with a Suggested next step.
---

# aw-continue

Thin hop. It does not re-run the previous stage. It reads the handoff on disk and starts the next stage, preferably in a fresh session.

## Steps

1. Resolve the change id: user arg, else the sole `openspec/changes/*/aw-handoff.md`, else ask.
2. Read only the handoff: `openspec/changes/<id>/aw-handoff.md`, or after `/aw-pr` archives, `openspec/changes/archive/*-<id>/aw-handoff.md`.
3. Read `aw-scorecard.md` or `aw-triage.md` only when the next stage needs the full table.
4. For each `read_targets` entry (`path:start-end - why`), Read that range with offset/limit. Read a whole file only when an edit needs it.
5. Announce the change id, `stage_done`, `Next`, and branch/worktree from `## pointers`.
6. Invoke the `Next` skill (for example `/aw-implement`, `/aw-ship-review`). Pass the handoff path. Do not paste the prior session. `/aw-pr` and `/aw-consolidate-dependency-prs` push and close PRs, so only the user starts them (`disable-model-invocation: true`): tell the user to type the command instead.

## Manual hop

New session (Claude Code: `/clear` or a new `claude` session; Antigravity: a new CLI session):

```text
Use <Next from handoff>. Read only openspec/changes/<id>/aw-handoff.md, then follow its read_targets with offset/limit.
```

## Boundaries

- Refuse when `aw-handoff.md` is missing or `status` is not `ready_for_next`.
- Never invent a next stage that contradicts `## suggested_next_step`.
- Never merge a PR unless the handoff or the human says so.
- Handoff files are committed with the branch.
- Template, footer format, and Next values: [REFERENCE.md](REFERENCE.md).
