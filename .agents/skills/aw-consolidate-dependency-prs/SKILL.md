---
name: aw-consolidate-dependency-prs
description: Consolidates overlapping Dependabot or Renovate pull requests for Cargo and GitHub Actions into tested ecosystem-level replacement PRs, closes superseded bot PRs, and remediates incompatible updates separately. Use when a repo has dependency-bot PR sprawl or the user asks to group, deduplicate, or clean up Dependabot or Renovate PRs.
disable-model-invocation: true
---

# aw-consolidate-dependency-prs

## Handoff

Follow `/aw-continue`. Start: read `openspec/changes/<id>/aw-handoff.md` when the work belongs to a change. End: the completion report writes the next one. No change: skip the file. Do not create OpenSpec changes.

## Inventory

From the target repo:

```sh
gh pr list --state open --json number,title,author,headRefName,files,statusCheckRollup,url \
  --jq '.[] | select(.author.login | test("dependabot|renovate"))'
```

Inspect each PR's body, diff, checks, and versions. Treat the output as evidence, not as a plan.

## Workflow

1. **Plan groups** by manifest, lockfile, and verification seam: Cargo workspace, GitHub Actions, another evidenced ecosystem. Leave a clean grouped PR alone unless another PR overlaps it. Newest safe patched version wins; never regress a version.
2. **Isolate**: one git worktree per independent group, from the current remote default branch, never from a bot branch. Re-resolve with `cargo update -p <crate> --precise <ver>` or `cargo update`; do not hand-merge `Cargo.lock`. Never force-push.
3. **Verify** per [REFERENCE.md](REFERENCE.md). Open the replacement PR only when required local checks pass.
4. **Incompatible updates**: pin the failing update out of the main group, leave its bot PR open, open the passing group first, then fix the migration in a separate tested PR. No safe fix: do not open a broken PR; report the blocker.
5. **Close superseded PRs**: after the replacement is open and local checks pass, re-fetch each bot PR, comment with the replacement link, close it. Never close one whose full change is not in a passing replacement.
6. **Guardrails**: if the sprawl proves a concrete bot-config gap, open a separate guardrail PR. No speculative config changes.

## Completion report

Replacement, remediation, and guardrail PR links; closed and retained bot PRs; checks run; deferred updates with blockers. When every replacement is open and superseded PRs are closed, write the handoff if a change is in play and emit the footer from [`aw-continue/REFERENCE.md`](../aw-continue/REFERENCE.md) with **Next:** none (or `/aw-address-pr-issues` if feedback exists), **New session?** yes. Do not emit while a group is deferred.

## Boundaries

- Do not merge unless the user asks.
- Do not expose secrets from PR bodies, registries, or command output.
- Do not touch unrelated local work or delete worktrees with uncommitted changes.
