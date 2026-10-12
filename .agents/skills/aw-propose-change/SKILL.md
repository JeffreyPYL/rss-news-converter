---
name: aw-propose-change
description: Turns a loose idea into an implementation-ready OpenSpec proposal (grill, draft, TDD seams, layer and public-API plan, architecture opportunities, split plan), then optional GitHub Issues via aw-create-issue. Plans only, never implements. Use when the user says "draft a proposal", "spec this out", "propose a change", "plan this feature", or hands over a loose idea before any code.
---

# aw-propose-change

Front of **propose -> aw-implement -> aw-test -> aw-ship-review -> aw-pr**. Produces OpenSpec change(s) with TDD seams, crate/layer placement, and a public-API list. Never writes implementation code.

## Handoff

Follow `/aw-continue`. Start: read `openspec/changes/<id>/aw-handoff.md` when it exists. End: the Suggested next step writes the next one.

## Scope: pin first

- Destination: OpenSpec change(s) an implementer can pick up.
- Touched area: crates and modules the idea changes.
- Sources of truth: `CONTEXT.md`, `docs/adr/`, `rules/`, `openspec/specs/**`.
- Read-only until artifacts are written.

## Workflow

- [ ] **Align**: `/grilling` over `/domain-modeling`, one decision at a time. Too big for one session: split into several proposals.
- [ ] **Draft**: `openspec new "<name>"`, then fast-forward the artifacts (`/opsx-ff` on Claude Code; the `openspec-ff-change` skill on Antigravity). Cover problem, solution, user stories, implementation and testing decisions, out of scope.
- [ ] **TDD seams**: name the highest seams, confirm with the user, record in `design.md`. One named test per spec scenario (see `rules/05-testing.md`).
- [ ] **Boundaries**: for each new module or file, record its crate, layer, who may use it, and what it may use (`rules/09-module-boundaries.md`, `rules/10-file-structure.md`, ADR 0002); a new crate also lists its `deny.toml` `wrappers`. Add a `## Public API` section listing every added, changed, or removed `pub` item. Ship-review diffs the real API against this list.
- [ ] **Lazy and conformant**: `/ponytail`, `/tdd`, and every MUST in `rules/`. Rule or ADR conflict: ask, do not decide.
- [ ] **Architecture opportunities**: `/codebase-design` on the touched area. Investigate all, ponytail-filter, present ranked (REFERENCE.md), user picks.
- [ ] **Incorporate**: small and coupled: fold in. Large: separate proposal.
- [ ] **Split**: one proposal per PR. Independent: one worktree each. Dependent: stacked branches, foundations first. Output the plan only.
- [ ] **Review**: artifact loop below until clean.
- [ ] **Hand off**: summarize. On confirm, run `/aw-create-issue` once per change. Write the handoff.

## Review the proposal (artifacts, not code)

Run `openspec validate "<name>" --strict` and the rubric in [REFERENCE.md](REFERENCE.md). Blockers: validate failure, unagreed seams, a `rules/` MUST or ADR contradiction, a requirement with no scenario, a new file with no layer decision, missing `## Public API`.

## Suggested next step

Write `openspec/changes/<id>/aw-handoff.md`, then emit the footer from [`aw-continue/REFERENCE.md`](../aw-continue/REFERENCE.md) with **Next:** `/aw-create-issue` if issues are needed, else `/aw-implement`; **New session?** yes. Do not emit while artifacts are blocked.

## Boundaries

- Plans only: no code, branches, agents, or PRs.
- Nothing is written until grilling reaches shared understanding.
- Security MUSTs from `rules/01-security.md` go into the spec (no secret or internal error leakage).
- `CONTEXT.md` is a glossary only. Decisions live in the OpenSpec change.
