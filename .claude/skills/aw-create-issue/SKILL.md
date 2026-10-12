---
name: aw-create-issue
description: Breaks work into tracer-bullet slices, then creates GitHub Issues with the gh CLI in plain English (problem, what we are solving, acceptance criteria, blockers), grouped under a parent tracking issue or milestone. Use when the user asks to create an issue, file work from a proposal, or when aw-propose-change hands off to issue creation.
---

# aw-create-issue

Slices the work itself, then drafts wait-what bodies. This skill is the only thing that creates issues: do not also run `/to-tickets` (it publishes on its own and cannot be invoked by the model). Mutates GitHub only after the user confirms the slice set, titles, bodies, labels, and epic.

## Tone

This skill owns issue prose. Callers invoke it; they do not restate these rules.

1. Short sentences, one idea each, active voice, concrete verbs. No em-dashes, no jargon stacks.
2. Use terms from `CONTEXT.md` (`CONTEXT-MAP.md` if several). Ask before inventing synonyms.
3. Title and Problem make sense without prior chat. A teammate understands the issue without the agent session.

## Handoff

Follow `/aw-continue`. Start: read `openspec/changes/<id>/aw-handoff.md` when it exists. End: the Suggested next step writes the next one.

## Steps

1. Repo: `gh repo view --json nameWithOwner`. Confirm `gh auth status` works.
2. **Slice** (rules below). Present a numbered list: title, blocked by, what it delivers. Ask whether the granularity is right, the blocking edges are real, and whether to merge or split. Iterate until approved. Skip only if the user confirms one atomic issue.
3. Draft each slice with the body template. Label `bug` or `enhancement`; ask for others.
4. Epic: a parent tracking issue (task list of child issues) or a milestone. Find candidates with `gh issue list --label epic --state open` and `gh api repos/{owner}/{repo}/milestones`. Offer the top 1-3 for confirm, or a key, or none. Use one epic per batch unless told otherwise.
5. Assignee: ask once per batch. Default is the invoking user (`gh api user -q .login`).
6. On confirm, create blockers first:
   ```bash
   gh issue create --title "<title>" --body-file <file> --label enhancement --assignee <login> [--milestone "<name>"]
   ```
   Put `Blocked by #<n>` in the body of dependent slices. For a parent tracking issue, add `- [ ] #<n>` lines after children exist (`gh issue edit <parent> --body-file <file>`).
7. Return numbers, URLs, and dependency order. Write the handoff when the batch is done.

## Slicing rules

Adapted from mattpocock-skills `to-tickets` (pinned v1.2.3).

- Each slice is a tracer bullet: a narrow but complete path through every layer it needs (interface, service, crud, tests), demoable or verifiable on its own. Not a horizontal slice of one layer.
- Each slice fits one fresh agent session.
- Prefactoring ("make the change easy") comes first, as its own slice.
- Each slice lists only the slices that truly block it. No blockers means it can start now.
- Wide mechanical refactor (rename or retype across many call sites): expand (add the new form beside the old), migrate in batches sized by blast radius (each blocked by the expand), then contract (delete the old form, blocked by every batch).
- Use the domain terms from `CONTEXT.md` and respect ADRs in the touched area.

## Body template

```
## Problem
<what is wrong or missing today>

## What we are solving
<desired outcome for THIS slice only>

## Acceptance criteria
- <observable done check>

## Blockers
- <none | Blocked by #n>

## Context
<OpenSpec change id, links>
```

Title: one plain phrase naming the outcome.

## Suggested next step

Write `openspec/changes/<id>/aw-handoff.md` (`issues:` filled), then emit the footer from [`aw-continue/REFERENCE.md`](../aw-continue/REFERENCE.md) with **Next:** `/aw-implement`, **New session?** yes. Do not emit while slices await approval.

## Boundaries

- Needs the `gh` CLI. Do not run `/to-tickets` as well: issues would be created twice.
- Never invent the repo, assignee, or milestone: discover or ask.
- Never attach an epic without confirm. Never write product code.
- One OpenSpec change may yield several issues; do not force 1:1.
