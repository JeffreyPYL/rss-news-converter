---
name: news-digest
description: Run the on-demand news digest pipeline (fetch, extract, group, render, and deliver)
---

# News Digest Pipeline

Run the news digest pipeline for this repository right now.

## Steps

1. Run `uv run python -m news_digest.cli` (or `just dev`) from the repo root. This runs the full pipeline (ingest, extract, group, render, deliver) end to end via `run_digest` in `src/news_digest/cli.py`.
   - By default the lookback window is since the last successful run (48 hours on the first-ever run).
   - Pass `--since <duration>` (e.g. `--since 3d` or `--since 48h`) to override the lookback for this run only — the run still records its completion time as the new last-success timestamp on success, exactly as an unoverridden run would.
2. Delivery configuration:
   - Email/Kindle needs `NEWS_DIGEST_SMTP_HOST`, `NEWS_DIGEST_SMTP_PORT`, `NEWS_DIGEST_SMTP_USERNAME`, `NEWS_DIGEST_SMTP_PASSWORD`, `NEWS_DIGEST_EMAIL_FROM`, `NEWS_DIGEST_EMAIL_TO`.
   - Obsidian needs `NEWS_DIGEST_OBSIDIAN_VAULT_PATH`.
   - Google Drive / Dropbox needs respective `NEWS_DIGEST_GDRIVE_*` / `NEWS_DIGEST_DROPBOX_*` variables.
   - If a target reports "not configured", tell the user which env vars are missing rather than treating it as a bug.
3. **Synthesis Note**:
   - `NEWS_DIGEST_SYNTHESIS_ENABLED=true` toggles cross-outlet synthesis. When synthesis is enabled, synthesis text is supplied before rendering.
4. Report what was delivered and where (Obsidian vault path, email/Kindle address, cloud folders), or report delivery failures per target if any occurred — per `digest-delivery` failure-visibility requirement, one target failing does not fail the entire run.
