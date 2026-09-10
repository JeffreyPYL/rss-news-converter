# Architecture

This is the living map of how `news-digest` is actually built. It tracks the code — when a source file under `src/news_digest/` changes shape (a new port, a new adapter, a moved module), update this file in the same change. `CLAUDE.md` covers tooling and conventions; this file covers structure. `openspec/changes/*/design.md` covers the reasoning behind a specific decision — this file just says what's true now.

## Pipeline

```
ingest (per topic, per outlet)
  -> extract full text
  -> dedupe by URL (same story, two topic lenses)
  -> group cross-outlet coverage into stories
  -> assign each story its most specific topic
  -> cap stories per topic
  -> render (EPUB + Obsidian markdown)
  -> deliver (email/Kindle + Obsidian vault), independently per target
```

`application/build_digest.py` wires the first six steps into one call; `cli.py`'s `run_digest` adds rendering and delivery around it.

## Layers

```
src/news_digest/
  domain/            # pure logic, no I/O
    models.py          Article, Story, Topic
    grouping.py         title normalization + cross-outlet story grouping
    topics.py           dedupe-by-url, topic assignment, per-topic cap

  application/         # use cases orchestrating domain + ports; no concrete adapters
    ports.py             every Protocol interface (see Ports below)
    build_digest.py      ingest -> extract -> dedupe -> group -> assign -> cap
    extraction.py         enrich_with_full_text: graceful extraction failure
    synthesis.py          the on/off toggle + attaching agent-written synthesis text
    deliver_digest.py     runs every configured delivery target independently

  infrastructure/       # concrete adapters — the only layer allowed to touch httpx, the filesystem, or a subprocess
    _http_client.py        DEFAULT_USER_AGENT — shared across every outbound httpx.Client (some outlets' edges reset the default httpx UA)
    feeds/
      config.py            DirectFeed/KeywordFilteredFeed models + load_feeds() — parses feeds.json into the topic -> source mapping
      feeds.json            the user-editable feed list itself (add/remove a feed here, no code change) — path overridable via Settings.feeds_config_path
      rss_feed.py           RssFeedSource: fetches + normalizes, per-source failure isolation
    extraction/
      trafilatura_extractor.py   default extractor
      defuddle_extractor.py       alternative extractor (shells out to `npx defuddle`)
      factory.py                  NEWS_DIGEST_EXTRACTOR-driven selection
      _markdown_images.py          shared image-URL regex for both extractors
    rendering/
      epub_renderer.py             one combined EPUB, images embedded
      obsidian_renderer.py          same content as an Obsidian-flavored note
      _topic_titles.py              shared topic -> display-name map
    delivery/
      email_delivery.py             SMTP send (Kindle is just email; also reused for the Dropbox-email Kobo route)
      obsidian_vault_delivery.py     writes the note into the configured vault path (also reused for the vault EPUB copy)
      dropbox_api_delivery.py        uploads the EPUB to Dropbox via the official `dropbox` SDK (Kobo)
      google_drive_delivery.py       uploads the EPUB to Google Drive via `google-api-python-client` (Kobo)
      _filenames.py                  shared timestamped() helper — every delivered file is named with when it was generated
    state/
      run_state.py                   last-successful-run timestamp, drives the lookback window
    settings.py                      Settings (pydantic-settings): every NEWS_DIGEST_* value, env var or `.env` file

  cli.py               # run_digest (testable, dependency-injected) + main (real wiring from env vars)
```

`domain/` never imports `httpx`, touches the filesystem, or shells out — that's what keeps it fast to test and honest about what's actually business logic versus I/O. It does import `pydantic` (every domain object is a `BaseModel`, for validation-on-construction), but that's a pure in-memory dependency, not an I/O one. `application/` depends only on `domain/` and the `Protocol`s in `ports.py`, never on a concrete `infrastructure/` class directly.

## Ports and their adapters

Every port here has at least two real implementations or a real dependency-injection seam used for testing — none are speculative:

| Port (`application/ports.py`) | Adapters |
|---|---|
| `FeedSource` | `RssFeedSource` |
| `ArticleExtractor` | `TrafilaturaExtractor`, `DefuddleExtractor` (config-selected via `NEWS_DIGEST_EXTRACTOR`) |
| `DigestRenderer` | `EpubRenderer`, `ObsidianRenderer` (both always run — not config-selected, since a run always produces both) |
| `DigestDelivery` | `EmailDelivery`, `ObsidianVaultDelivery`, `DropboxApiDelivery`, `GoogleDriveDelivery` (all run independently per `deliver_digest.py`; one failing doesn't block the others) |

Two adapters additionally take their own injected seam, for the same reason `EmailDelivery` takes an `SmtpSender`: the real dependency (a subprocess, a third-party function) isn't `httpx`, so `pytest-httpx` can't mock it, and it shouldn't be `unittest.mock.patch`ed per the `python-testing` skill's fixture-only rule.

| Class | Injected seam | Real implementation |
|---|---|---|
| `EmailDelivery` | `SmtpSender` | `SmtplibSender` (wraps `smtplib.SMTP_SSL`) |
| `DefuddleExtractor` | `ProcessRunner` | `subprocess.run` |
| `TrafilaturaExtractor` | `ExtractFn` | `trafilatura.extract` |

## Known gaps

The scheduled/unattended trigger and its synthesis path aren't implemented — see `openspec/changes/news-digest/design.md`'s Open Questions for why (a Claude Code cloud routine was evaluated and ruled out) and the likely direction (a local `launchd` job).
