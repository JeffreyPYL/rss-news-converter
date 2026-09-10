---
name: architecture-doc-check
description: Add, remove, move, or change the shape of a file under src/news_digest/ — a new module, a new port or adapter, a folder reorganization. Use whenever touching the domain/application/infrastructure structure, to check whether ARCHITECTURE.md needs a corresponding update.
---

`ARCHITECTURE.md` is a living doc, not a one-time writeup — it goes stale the moment the code it describes moves and nobody edits it. Before finishing a change that touches `src/news_digest/`, check whether any of these happened, and update `ARCHITECTURE.md` if so:

- A new file, module, or folder was added, removed, or renamed.
- A new `Protocol` was added to `application/ports.py`, or a new adapter implements an existing one.
- A pipeline stage was added, removed, or reordered (`ARCHITECTURE.md`'s Pipeline section).
- An injected seam (like `SmtpSender`, `ProcessRunner`, `ExtractFn`) was added for testability.

If none of these happened — a bug fix inside an existing function, a test-only change — `ARCHITECTURE.md` doesn't need touching. Don't edit it reflexively; edit it when the structure it documents actually changed.
