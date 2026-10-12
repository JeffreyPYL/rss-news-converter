---
name: aw-address-pr-issues
description: Addresses feedback on a pull request without a fix-loop. Gathers the whole PR history (review comments, bot findings, CI checks, replies, resolved and unresolved), triages each item as valid, already-addressed, or invalid against the OpenSpec spec, ADRs, and rules, fixes valid ones TDD-style, runs aw-ship-review, pushes, then replies to threads. Use when the user says "address PR comments", "fix PR feedback", "resolve review comments", "handle CI findings on the PR".
---

# aw-address-pr-issues

Defeats the fix-loop by gathering all PR feedback and triaging it against the OpenSpec spec, ADRs, and `rules/` before any code change.

## Handoff

Follow `/aw-continue`. Start: read `aw-handoff.md` (active or archived under `openspec/changes/archive/`). Use its PR URL and `read_targets`. End: the Suggested next step writes the next one in the same directory.

## Scope: pin first

- PR: the open PR for the branch (`gh pr view`). Ambiguous: ask.
- Diff: `git diff <base>...HEAD`. Read-only until Ship.
- OpenSpec change for the branch: its `proposal.md`, `specs/`, `tasks.md` are the spec.
- ADRs under `docs/adr/` for the touched area. A "fix" that contradicts one is not a fix.

## Triage: validate before fixing

One table of every item, each classified with a reason:

| Class | Meaning | Action |
|---|---|---|
| `valid` | Real, open, consistent with spec, ADRs, rules | Fix with `/tdd` |
| `already-addressed` | A later commit or reply handled it, or a stale re-flag | Link it, resolve the thread |
| `invalid` | Contradicts an ADR, the spec, or a `rules/` MUST; or rests on a wrong assumption | No code change; reply citing the source |

Anti-fix-loop rules:

- Read the whole thread, not the last comment. Answered, deferred, or overruled earlier means not open.
- Fix the shared function once, not each caller's symptom.
- A fix that would break a spec, ADR, or rule is an alignment question. Push back with the citation; do not oscillate the code.
- Group related items so one slice closes several comments.

## Workflow

- [ ] **Gather**: every review comment, review summary, conversation comment, bot finding, and CI check; note resolved threads. Failing checks: one subagent per check for root cause. Commands: [REFERENCE.md](REFERENCE.md).
- [ ] **Picture**: load the OpenSpec change, ADRs, and `rules/` for the touched area.
- [ ] **Triage**: classify all, present the table, confirm the plan with the user before editing.
- [ ] **Fix**: per `valid` item, `/tdd`: confirm the seam, failing test, minimum code. Update docs and `tasks.md` in the same slice. New files follow the layer question in `/aw-implement`.
- [ ] **Gates**: run `/aw-ship-review` and drive it to READY. Never widen ignores or lower thresholds.
- [ ] **Ship**: only on explicit user confirm: commit and push (accurate message, no secrets, no force-push to protected branches).
- [ ] **Respond**: reply to and resolve threads (REFERENCE). Reply only where it adds signal.

## Suggested next step

Write `aw-handoff.md` (triage per [`aw-continue/REFERENCE.md`](../aw-continue/REFERENCE.md)), then emit that footer:

| When | Next | New session? |
|------|------|--------------|
| Triage confirmed, fixes not started | `/aw-implement` or continue Fix via handoff | yes |
| Responses posted, shipped | none; a human merges | yes |

Do not emit while triage items are disputed.

## Boundaries

- Gather, Picture, Triage are read-only. Nothing changes until the user confirms the plan.
- Fixes obey `rules/01-security.md`; never put secrets or internal error text in code or PR comments.
- Do not commit while `/aw-ship-review` reports blockers.
