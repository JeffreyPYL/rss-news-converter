---
name: aw-ship-review
description: Interactive review-and-fix loop that drives a Rust change to merge-ready. Reviews OpenSpec conformance, over-engineering, standards and spec, rules, bugs, security, static Rust gates (fmt, clippy, deny/audit, file-size, public-API diff), and verifies test artifacts from aw-test. Presents findings, lets the user choose fixes, applies them TDD-style, re-reviews until clean. Use when the user says "ship review", "final review", "pre-merge review", or "get this ready to merge".
---

# aw-ship-review

A loop, not a report: **review -> present -> align -> choose -> fix -> re-review** until zero blockers and green gates, then hand off to `/aw-pr`. Commands, formats, and rubrics: [REFERENCE.md](REFERENCE.md).

## Handoff

Follow `/aw-continue`. Start: read `openspec/changes/<id>/aw-handoff.md` when it exists; use its worktree, branch, and `read_targets`. End: the Suggested next step writes the next one.

## Scope: pin first

- Diff: `git diff <base>...HEAD` (base from the handoff, else `origin/main`). Read-only until Choose.
- OpenSpec change: `openspec/changes/<name>/`. Its `proposal.md`, `specs/`, `tasks.md`, `## Public API`, and `test-report.json` are the spec.
- ADRs under `docs/adr/` for the touched area. Fixes must not contradict them.
- Changed crates: map each changed `.rs` file to its crate (`cargo metadata --no-deps`, match `manifest_path`).

## Staleness check (test artifacts)

Before running review axes, inspect `openspec/changes/<name>/test-report.json`:
- Compare `timestamp` against the newest `.rs` mtime / commit timestamp on the branch.
- If missing or stale (source code modified after tests ran), prompt the user:
  1. *[Recommended]* Run `/aw-test` now.
  2. *Proceed with existing artifact* (override warning).
  3. *Abort review*.

## Review axes

| # | Axis | How |
|---|------|-----|
| 1 | OpenSpec conformance | `/opsx-verify` (Antigravity: `openspec-verify-change` skill) |
| 2 | Over-engineering | `/ponytail-review` |
| 3 | Standards + Spec | `/code-review`, standards = every file in `rules/` |
| 4 | Bugs | fresh subagent over the diff, high/critical = blocker |
| 5 | Security | `/security-review` plus `rules/01-security.md` (Antigravity: fresh subagent with that rule) |
| 6 | Boundaries and structure | every new crate has its `deny.toml` `wrappers` entry; new files have a layer decision; visibility matches `rules/09-module-boundaries.md`; file and test layout matches `rules/10-file-structure.md`; tests are named, use cases stated, data-varying tests parameterised (`rules/05-testing.md`) |

## Rust gates & artifact evaluation

Run after the axes; all must pass. Exact commands and scoping: REFERENCE.

| Gate | Type | Fail is |
|------|------|---------|
| `test-report.json`: functional tests | artifact from `/aw-test` | blocker |
| `test-report.json`: line coverage ≥ 90% on changed files | artifact from `/aw-test` | blocker |
| `test-report.json`: 0 missed mutants on diff | artifact from `/aw-test` | blocker (behavior lock) |
| `test-report.json`: CRAP complexity | artifact from `/aw-test` | blocker |
| `cargo fmt --all --check` | static command | blocker |
| `cargo clippy --workspace --all-targets --all-features -- -D warnings` | static command | blocker |
| `cargo deny check` (includes `bans` visibility) and `cargo audit` | static command | blocker |
| `just file-size` (no `.rs` over 400 non-test lines without `// size-exempt:`) | static command | blocker |
| `cargo public-api` diff equals the change's `## Public API` | static command | blocker on any mismatch |
| `cargo semver-checks` for published crates | static command | blocker |

Never widen ignores, add `#[allow]`, skip a mutant without a reason comment, or lower a threshold to pass.

## Loop

1. **Review**: run axes (subagents in parallel) and gates.
2. **Present**: scorecard plus every finding by axis; show all before fixing.
3. **Align**: `/grilling` each finding so the fix is the right fix.
4. **Choose**: one multi-select, blockers first, with "all blockers" and "explain first".
5. **Fix**: `/tdd` per chosen finding, inside the OpenSpec change, ADRs, and `rules/`. A fix that breaks one is an alignment question. Update docs and `tasks.md` in the same slice. A public-API change that is intended also updates the change's `## Public API`.
6. **Re-review**: recompute the diff and rerun everything. READY needs zero blockers and green gates on a fresh pass.

## Ship

Only on READY. Write the handoff with **Next:** `/aw-pr`. Commit here only if the user says to skip that hop.

## Suggested next step

Write `openspec/changes/<id>/aw-handoff.md` (scorecard per [`aw-continue/REFERENCE.md`](../aw-continue/REFERENCE.md)), then emit that footer:

| When | Next | New session? |
|------|------|--------------|
| READY | `/aw-pr` | yes |
| Mid Choose | continue `/aw-ship-review` | no |
| NOT READY / Blockers present (Headless/Conductor) | `/aw-implement` (record blockers in `## scorecard` and set `stage_done: review_failed`) | yes |
| After fixes or post-ship follow-up | `/aw-implement` or `/aw-address-pr-issues` | yes |

In automated or headless workflows, `aw-ship-review` persists its structured scorecard to `openspec/changes/<id>/aw-scorecard.md` (or inline in `aw-handoff.md`). If blockers exist and execution cannot be resolved interactively, set `status: NOT READY`, `stage_done: review_failed`, and route to `/aw-implement`.

## Boundaries

- Read-only until Choose.
- Gates cover the whole workspace for fmt, clippy, and tests; coverage, mutants, and API diff are scoped to the change.
