---
name: aw-bulk-read
description: Answers questions about large files through the bulk-reader subagent so the parent session receives findings, not whole files. Use when a read hook blocks a large read, the user asks what a large file or several files do, or the task is understanding code without editing it.
---

# aw-bulk-read

Send oversized reads to the `bulk-reader` subagent. Do not paste file bodies into this session.

## Steps

1. Confirm the task is understanding, not editing, debugging, or security review, and the paths are specific files.
2. Delegate with the question and absolute paths:
   - Claude Code: the Agent tool with `subagent_type: bulk-reader`.
   - Antigravity: `invoke_subagent` with agent `bulk-reader`, Workspace `"inherit"` (unverified: exact parameter names).
3. Keep its bullet findings and `read_targets`.
4. Read a `read_targets` range here only when about to edit it.

```text
Use the bulk-reader subagent.
Question: Which functions write to the database?
Paths:
- /abs/path/service.rs
- /abs/path/repo.rs
```

## Handoff

If the question belongs to an OpenSpec change, follow `/aw-continue`: read `openspec/changes/<id>/aw-handoff.md` first when it exists, and add this reply's `read_targets` to it when done. No change: skip.

## Boundaries

- Not for generating code: use `/aw-code-write`.
- A denied read means the file was over the size guard. Retrying the same whole-file read will be denied again.
