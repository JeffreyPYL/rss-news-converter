---
name: aw-code-write
description: Generates one predictable file through the code-writer subagent from a reference file, writing the target directly to disk. Use when scaffolding tests, config stubs, type scaffolds, or mechanical docs that must match an existing file.
---

# aw-code-write

Send patterned file generation to the `code-writer` subagent. It writes the target; this session keeps the path and a one-line summary. Single targeted edits: do them directly.

## Steps

1. Check: a reference file shows the pattern; the target is one new or replaced file; the task is tests, config, types, or mechanical docs.
2. Delegate:
   - Claude Code: the Agent tool with `subagent_type: code-writer`.
   - Antigravity: `invoke_subagent` with agent `code-writer`, Workspace `"inherit"` (unverified: exact parameter names).
3. Run the focused check yourself (`cargo nextest run -p <crate> <filter>`, `cargo check`). Read the target only if it fails.

```text
Use the code-writer subagent.
Spec: Write unit tests for cancel() in the same style as the reference.
Reference: /abs/path/crates/orders-service/src/place_order/tests.rs
Target: /abs/path/crates/orders-service/src/cancel_order/tests.rs
```

## Handoff

If the file belongs to an OpenSpec change, follow `/aw-continue`: read `aw-handoff.md` first when it exists, and record the target path when done. No change: skip.

## Boundaries

- No reference file: do not delegate.
- Never delegate debugging, auth, cryptography, `unsafe`, migrations, secrets, authorization, or business rules.
- New files still need the layer decision (`/aw-implement`, `rules/09-module-boundaries.md`) before delegating; put the answer in the spec and target path.
- First result fails its check: fix the small failure here or send one tighter spec. Do not switch models on your own.
