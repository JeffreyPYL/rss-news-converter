---
name: readme-doc-check
description: Add, rename, or remove an env var, a `just` recipe, a delivery target, a prerequisite, or a CLI entry point — or change what the pipeline does or doesn't support end to end. Use whenever touching local setup, configuration, or usage, to check whether README.md needs a corresponding update.
---

`README.md` is a living doc, not a one-time writeup — it goes stale the moment setup steps or behavior drift from what it describes. Before finishing a change, check whether any of these happened, and update `README.md` if so:

- A `NEWS_DIGEST_*` env var was added, renamed, removed, or its meaning changed.
- A `just` recipe was added, renamed, or its behavior changed.
- A prerequisite (a tool, a service, a login) was added or dropped.
- A delivery target or an extractor option was added or removed.
- The CLI's trigger command or invocation shape changed.
- Something listed under "Current status" as unbuilt got built, or vice versa.

If none of these happened — a bug fix inside an existing function, a test-only change, an internal refactor with no setup or behavior impact — `README.md` doesn't need touching. Don't edit it reflexively; edit it when what a reader would do to run this thing, or what it does once running, actually changed.
