## Why

News about Canada, Ottawa, Hong Kong, China, tech, and world affairs is scattered across BBC, CBC, and Globe and Mail — reading it well today means visiting three sites and manually filtering by topic. This change builds a single command that pulls the topics that matter, extracts full articles (not just headlines), and delivers one readable digest to where the reading actually happens: Obsidian and Kindle/email.

## What Changes

- New RSS-based ingestion across 6 topic buckets (Canada, Ottawa, Hong Kong, China, Tech, Global) from BBC, CBC, and Globe and Mail, plus SCMP/RTHK for Hong Kong specifically.
- Full-article extraction via a plain, unauthenticated HTTP fetch + Trafilatura (Defuddle available as a swappable alternative) — no login or browser automation needed.
- Cross-outlet story grouping: the same story covered by multiple outlets is shown once, with every covering outlet's full article included underneath (Kagi News-style: synthesis on top, originals always intact).
- An optional synthesis mode that adds a short cross-outlet synthesis blurb per grouped story, built two ways for comparison: inline during an on-demand run, and via a scheduled Claude Code agent run (no separate LLM API key — synthesis rides on the existing Claude Code subscription either way).
- A single combined EPUB per run (all 6 topics, images included) delivered to an Obsidian vault and via email/Send-to-Kindle.
- Two triggers: an on-demand Claude Code command, and a daily ~7am scheduled run, both sharing the same self-contained script pipeline.
- Persisted run state (last-successful-run timestamp) so lookback is "since last run" with a 48h default on first run, and a missed scheduled day self-heals rather than losing coverage.
- Per-feed failure isolation: a broken/timed-out source is skipped and noted in a digest footer rather than failing the whole run.
- Comments/discussion sections are explicitly out of scope (evaluated and dropped — see design.md).

## Capabilities

### New Capabilities

- `feed-ingestion`: fetching and normalizing raw articles from RSS feeds (BBC, CBC, Globe and Mail, SCMP, RTHK) across the 6 topic buckets, including keyword-filtered fallback coverage for Hong Kong, with per-feed failure isolation and persisted lookback state.
- `article-extraction`: turning a feed item's URL into full article text and images via an unauthenticated HTTP fetch, with Trafilatura as the extractor and Defuddle as a swappable alternative.
- `story-digest`: normalizing titles, grouping same-story coverage across outlets, assigning each story to its most specific topic (narrow-to-broad, once per story), and capping each topic at 10 stories per run.
- `digest-synthesis`: the optional, toggleable cross-outlet synthesis step layered on top of a story group, built both as an inline on-demand step and as a scheduled-agent step.
- `digest-rendering`: producing the single combined EPUB and an Obsidian-flavored Markdown note from a built digest.
- `digest-delivery`: sending the rendered digest via email/Send-to-Kindle and writing it into the configured Obsidian vault path.
- `digest-triggers`: the on-demand Claude Code command and the daily ~7am scheduled run that both invoke the same pipeline.

### Modified Capabilities

_None — this is a greenfield change; no existing specs exist yet._

## Impact

- New Python codebase at `src/news_digest/` (currently no application code exists in this repo — only OpenSpec planning and Claude Code skills/config).
- New runtime dependencies (uv-managed): `httpx`, `feedparser` (or equivalent RSS parser), `trafilatura`, `ebooklib` (or equivalent EPUB writer), plus the Node-based `defuddle` CLI invoked as a subprocess for the alternative extractor.
- New dev/test dependencies: `pytest`, `pytest-httpx`, `mutmut`, `crap4py`, `ruff`, `pyrefly`, `just` — per `CLAUDE.md` and the `python-testing` skill already committed to this repo.
- New required configuration/credentials: Obsidian vault path, SMTP/Kindle-email credentials (both deferred to env vars per earlier decision), and no LLM API key (synthesis rides on the Claude Code subscription, not a billed API).
- New Claude Code artifacts: an on-demand slash command and a scheduled cron routine (via the `schedule` capability), both invoking the same pipeline entrypoint.
