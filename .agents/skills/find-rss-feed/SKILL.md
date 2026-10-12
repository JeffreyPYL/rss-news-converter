---
name: find-rss-feed
description: Find a working RSS feed URL for a news outlet, or fix one that broke (a redirect, a timeout, a 404) in feeds.json. Use when the user wants to add a new source or topic to the digest, or when a run reports a source skipped.
---

Outlets move and rename their RSS endpoints without notice — this project has already hit a stale CBC path, a dead RTHK URL, and an SCMP feed that now 301-redirects. Verify a candidate URL actually works before writing it down; don't guess from a docs page or an old blog post, they go stale too.

## Steps

1. **Find candidates.** Check the outlet's own feed index page first (e.g. `bbc.co.uk/news/10628494`, `cbc.ca/rss`, an outlet's `/rss` or `/feeds` path) or search the web for `<outlet> rss feed <section>`. Prefer a feed already scoped to the topic (e.g. a dedicated "Technology" feed) over a general one — that's what earns a `direct` entry instead of a `keyword_filtered` one (see step 3).

2. **Verify it, following redirects to the final URL.** Run:
   ```bash
   curl -sIL "<candidate-url>"
   ```
   `-L` follows redirects — read the *last* `HTTP/` status line and use the URL it settled on, not the one you started with (this is exactly the SCMP bug: the old URL 301s to a new path, and `RssFeedSource`'s default client now follows redirects automatically, but a fresher URL means one less hop on every run). Confirm the final status is `200`. Then confirm it's actually RSS/Atom, not an HTML error page dressed as 200:
   ```bash
   curl -sL "<candidate-url>" | head -c 300
   ```
   Look for a `<rss` or `<feed` root element near the top.

3. **Decide `direct` vs `keyword_filtered`.** A feed dedicated to the topic (every item is in-scope) is `direct`. A broader feed (World, Asia, general) that needs filtering down is `keyword_filtered` — pick keywords the way existing entries in `feeds.json` do: lowercase, covering the obvious name variants (see the Hong Kong and China entries for the pattern).

4. **Add it to `src/news_digest/infrastructure/feeds/feeds.json`.** Find the topic's key (`ottawa`, `canada`, `hong-kong`, `china`, `tech`, or `global` — these match `Topic`'s values in `domain/models.py`; add the key with empty `direct`/`keyword_filtered` arrays if the topic isn't in the file yet) and append the new feed object under `direct` or `keyword_filtered` per step 3. No code change needed — `RssFeedSource` reads this file directly.

5. **Smoke-test it** without running a full delivery: 
   ```bash
   uv run python -c "
   from news_digest.infrastructure.feeds.rss_feed import RssFeedSource
   from news_digest.domain.models import Topic
   from datetime import datetime, timedelta, UTC
   source = RssFeedSource()
   articles = source.fetch_topic(Topic.<TOPIC>, since=datetime.now(UTC) - timedelta(hours=48))
   print(len(articles), 'articles')
   print(source.skipped)
   "
   ```
   An empty `skipped` list and at least one article (if the outlet published anything in the last 48h) confirms the feed is live and parses. If it shows up in `skipped` instead, the URL still isn't right — go back to step 2.
