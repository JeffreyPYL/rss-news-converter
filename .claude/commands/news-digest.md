---
name: "News Digest"
description: "Run the on-demand news digest pipeline: fetch, extract, group, render, and deliver"
allowed-tools: Bash(uv run:*), Bash(just:*)
category: "Automation"
tags: ["news-digest", "on-demand"]
---

Run the news digest pipeline for this repo right now.

1. Run `uv run python -m news_digest.cli` from the repo root. This runs the full pipeline (ingest, extract, group, render, deliver) end to end via `run_digest` in `src/news_digest/cli.py`. By default the lookback window is since the last successful run (48 hours on the first-ever run). Pass `--since <duration>` (e.g. `--since 3d` or `--since 48h`) to override the lookback for this run only — the run still records its completion time as the new last-success timestamp on success, exactly as an unoverridden run would.
2. Delivery needs `NEWS_DIGEST_SMTP_HOST`/`_PORT`/`_USERNAME`/`_PASSWORD`/`NEWS_DIGEST_EMAIL_FROM`/`_TO` (email/Kindle) and/or `NEWS_DIGEST_OBSIDIAN_VAULT_PATH` (Obsidian) set as environment variables — neither is configured yet. If the command reports a target as "not configured," tell the user which env vars are missing rather than treating it as a bug.
3. **Synthesis is not wired into this command yet.** `NEWS_DIGEST_SYNTHESIS_ENABLED=true` currently has nothing to feed it — the CLI doesn't expose grouped stories for this agent turn to write synthesis into before rendering (see `openspec/changes/news-digest/design.md`'s Open Questions and `tasks.md` 9.2's note). Leave synthesis off until that hook exists; don't try to invent one inline.
4. Report what was delivered and where (Obsidian vault path, email/Kindle address), or report the delivery failures per target if any occurred — per `digest-delivery`'s failure-visibility requirement, one target failing should not be read as the whole run failing.
