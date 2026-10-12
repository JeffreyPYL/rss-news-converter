---
name: aw-pr
description: Archives an OpenSpec change, then commits, pushes, and opens one pull request with gh. The PR body links GitHub Issues and uses plain wait-what English. Use when the user says "open a PR", "aw-pr", "archive and ship", or a handoff names aw-pr as Next.
disable-model-invocation: true
---

# aw-pr

Ship stage after `/aw-ship-review` is READY. Archive first, then one commit, one push, one PR.

## Handoff

Follow `/aw-continue`.

- Start: read `openspec/changes/<id>/aw-handoff.md`. Use its branch, worktree, and `issues`. Do not paste the prior session.
- End: after the PR exists, update the handoff in the archived change directory (`openspec/changes/archive/<date>-<id>/aw-handoff.md`) with `stage_done: pr`, the PR URL, `status: ready_for_next`. Emit the footer from [`aw-continue/REFERENCE.md`](../aw-continue/REFERENCE.md). **Next:** `/aw-address-pr-issues` when feedback exists, else CI watch then human merge. **New session?** yes. Do not write it while archive or push is blocked.

## Workflow

- [ ] **Change id**: user arg, else the handoff, else the sole active change, else ask.
- [ ] **Place**: work in the handoff `worktree` on its `branch`. No worktree: stop and name `/aw-implement`.
- [ ] **Archive**: `/opsx-archive <id>` on Claude Code; the `openspec-archive-change` skill on Antigravity. When it offers a sync, sync, then archive. Stop if cancelled.
- [ ] **Commit**: archive plus any uncommitted task work. Message `type(#n): outcome` when an issue exists, else `type: outcome`. No secrets, no empty commit.
- [ ] **Push**: `git push -u origin HEAD`. No force-push.
- [ ] **PR**: if the branch already has an open PR (`gh pr view`), report its URL and stop. Else `gh pr create --title <commit title> --body-file <file>`.

## PR body

Same prose rules as [`aw-create-issue`](../aw-create-issue/SKILL.md): short sentences, one idea each, active voice, terms from `CONTEXT.md`, no em-dashes. A reader understands the change without this session.

```text
## Problem
<what is wrong or missing today>

## What we are solving
<what this change does>

## Issues
- <Closes #123 | none>

## How to check
- <one command or observable check>
```

Issue numbers come from the handoff `issues`, then the branch name, then the OpenSpec change. None: write `none`.

## Boundaries

- Do not merge.
- Do not open the PR before archive succeeds.
- Do not invent issue numbers.
