---
name: aw-implement
description: Implements an approved OpenSpec change by running the apply step under /ponytail inside a new git worktree on a new branch cut from the latest origin/main, asking the layer question for every new file. Use when the user says "implement", "aw-implement", "apply the change", or a handoff names aw-implement as Next.
---

# aw-implement

Implement stage of **propose -> implement -> aw-test -> aw-ship-review -> aw-pr**. Isolates work in a worktree, keeps the diff lazy, encodes module boundaries in every new file, ends with a handoff.

## Quick start

```text
/aw-implement add-rate-limiter
```

## Handoff

Follow `/aw-continue`. Start: read `openspec/changes/<id>/aw-handoff.md` when it exists, before any other file. End: the last step writes the next one. Do not write it while blocked.

## Workflow

- [ ] **Change id**: user arg, else the handoff, else the sole active change, else ask.
- [ ] **Base**: `git fetch origin main`; `base_sha=$(git rev-parse origin/main)`. A user-named base replaces it.
- [ ] **Worktree**: reuse the one in the handoff. Otherwise:
  - Claude Code: use native worktree support (`EnterWorktree`, or start with `claude --worktree <change-id>`), branch from `base_sha`.
  - Antigravity: `invoke_subagent` with Workspace `"branch"` (isolated git worktree) (unverified: exact parameter names).
  - Plain git fallback: `git worktree add -b feat/<change-id> ../<repo>-<change-id> "$base_sha"`.
- [ ] **Carry the change**: if `openspec/changes/<change-id>/` is not on the base, copy it from the primary checkout so the branch owns it.
- [ ] **Lazy mode**: `/ponytail` full for the rest of the session.
- [ ] **Apply**: `/opsx-apply <change-id>` on Claude Code; the `openspec-apply-change` skill on Antigravity. Scope every read, edit, and command to the worktree. Follow the TDD seams in the change; write the failing test first (`/tdd`).
- [ ] **Layer question** for every new file (below).
- [ ] **Gates**: `cargo fmt --all --check`, `cargo clippy --workspace --all-targets --all-features -- -D warnings`, `cargo nextest run --workspace --all-features` green in the worktree. Full testing suite and metrics belong to `/aw-test`.
- [ ] **Hand off**: write `aw-handoff.md` in the worktree with `stage_done: implement`, `branch`, `worktree`, `base_sha`, and `read_targets` for changed ranges. Emit the footer from [`aw-continue/REFERENCE.md`](../aw-continue/REFERENCE.md): **Next:** `/aw-test`, **New session?** yes.
- [ ] **Bounce-back handling**: if invoked with `stage_done: test_failed` or `stage_done: review_failed` in `aw-handoff.md`, resume the existing implementation session when available (`--conversation` or `--resume`), inspect `## failures` or scorecard blockers, apply targeted fixes, and re-hand off to `/aw-test`.

## Layer question (every new file or crate)

Rules: `rules/09-module-boundaries.md`, `rules/10-file-structure.md`, [ADR 0002](../../docs/adr/0002-crate-per-layer-with-deny-wrappers.md). Before creating a file or crate, answer all three, using the plan in the change's `design.md`:

1. Which layer does it belong to? Words: **interface** (api, gql, cli, queue) -> **service** -> **crud**, plus **common** (logging, observability, http client, queue intake). A new layer needs a stated reason.
2. Who may use it?
3. What may it use?

Encode the answers, not a comment:

| Answer | Encoding |
|---|---|
| New layer for a context | its own crate `<ctx>-<layer>` under `crates/`, plus its `deny.toml` `wrappers` entry |
| Context's public face | re-exported from the `<ctx>` facade crate, listed in the change's `## Public API` |
| Only this crate | `pub(crate)` |
| Only the parent module | `pub(super)` |
| Needed by a second context | a new `crates/common-<concern>` crate (never `utils`) |
| Edge to another crate | a `Cargo.toml` dependency allowed by `deny.toml`; never upward |

One concept per file; a file over 400 non-test lines becomes a folder; unit tests go in a sibling `tests.rs`. Default to the narrowest visibility. Wider than the plan says: stop and ask. Unit tests obey the same edges: fakes only, public interface only.

## Boundaries

- Never implement in the primary checkout.
- Do not push, open a PR, or merge. `/aw-ship-review` and `/aw-pr` own that.
- Branch name taken, or the apply step pauses: stop and ask. No handoff while blocked.
- Remove the worktree only after ship or abandonment and user confirm.
