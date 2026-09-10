# news-digest

A personal automation that pulls news from RSS feeds (BBC, CBC, Globe and Mail, SCMP, RTHK) across six topics — Canada, Ottawa, Hong Kong, China, Tech, Global — extracts full article text, groups same-story coverage across outlets, and delivers a single digest (EPUB + Obsidian note) to wherever you actually read. Both formats include a navigable index — every story links back to it, so hopping between articles on an e-reader or in Obsidian doesn't mean scrolling through the whole thing.

Full design and requirements live in `openspec/changes/news-digest/`. This file only covers getting it running on your machine.

## Prerequisites

- **[uv](https://docs.astral.sh/uv/)** — manages the Python version and all dependencies; you don't need Python installed separately.
- **Node.js / npm** (for `npx`) — the Defuddle extractor (an alternative to the default Trafilatura extractor) shells out to `npx defuddle`. Not required if you only ever use the default extractor, but the setup steps below install it either way for convenience.
- **[just](https://github.com/casey/just)** — the command runner used for every task below (`brew install just` on macOS).

## Setup

```bash
git clone <this-repo>
cd news-digest
just install    # uv sync — installs Python + all runtime and dev dependencies
just test       # sanity check: should show all tests passing
```

## Configuration

Nothing is delivered until you set the environment variables for at least one target below. Neither is required to run the pipeline itself — without any configured, `/news-digest` will run, log what it *would* have delivered, and exit non-zero.

Every variable below can be set as a real environment variable, or in a `.env` file in the repo root — copy `.env.example` to `.env` and fill it in. Config is read via [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) (`infrastructure/settings.py`); a real environment variable always overrides the same key in `.env`. `just` also loads `.env` automatically (`set dotenv-load`), so `just dev` picks it up with no extra step. Every data object in the pipeline (articles, stories, delivery results, the run-state file) is a [pydantic](https://docs.pydantic.dev/) model too, not just config — so a corrupted `run_state.json`, for instance, fails with a clear validation error rather than a silent bad read.

### Email / Send-to-Kindle

```bash
export NEWS_DIGEST_SMTP_HOST=smtp.gmail.com
export NEWS_DIGEST_SMTP_PORT=465
export NEWS_DIGEST_SMTP_USERNAME=you@gmail.com
export NEWS_DIGEST_SMTP_PASSWORD=your-app-password   # not your regular password — use an app password
export NEWS_DIGEST_EMAIL_FROM=you@gmail.com
export NEWS_DIGEST_EMAIL_TO=your-kindle-address@kindle.com
```

For Kindle delivery specifically, `NEWS_DIGEST_EMAIL_FROM` must be on your Kindle's **Approved Personal Document E-mail List** (Amazon account settings → Devices → your Kindle's email) — that step is manual and can't be automated.

The attached EPUB is named `<date> <time> digest.epub` (e.g. `2026-08-29 1400 digest.epub` — date prefix, then 24-hour time with no seconds), so it's easy to tell which run's digest you're looking at on the device.

#### Using Fastmail

Fastmail's SMTP settings, if that's your provider:

```bash
export NEWS_DIGEST_SMTP_HOST=smtp.fastmail.com
export NEWS_DIGEST_SMTP_PORT=465
export NEWS_DIGEST_SMTP_USERNAME=you@fastmail.com
export NEWS_DIGEST_SMTP_PASSWORD=your-app-password
export NEWS_DIGEST_EMAIL_FROM=you@fastmail.com
export NEWS_DIGEST_EMAIL_TO=your-kindle-address@kindle.com
```

Generate the app password at Fastmail → Settings → Privacy & Security → **App Passwords**, scoped to "Mail" — your regular account password won't work for SMTP. Port 465 is implicit TLS, which matches how `EmailDelivery` connects (`smtplib.SMTP_SSL`); Fastmail's STARTTLS port (587) won't work without a code change.

**On an MCP server for this**: there's no Fastmail MCP connected in this project, and even if there were, it wouldn't fit here — `EmailDelivery` sends over plain SMTP specifically so it can run outside an active Claude Code session (the same reason the scheduled-trigger design in `design.md` ruled out a Claude Code cloud routine: it needs to work unattended, which an MCP-based send doesn't). The app-password route above is the actual integration point.

### Obsidian vault

```bash
export NEWS_DIGEST_OBSIDIAN_VAULT_PATH="/path/to/your/vault"
```

Writes a note into that folder on every run, named `<date> <time> News Digest.md` (e.g. `2026-08-29 1400 News Digest.md` — date prefix, then 24-hour time with no seconds) so successive runs accumulate as separate notes instead of overwriting each other.

If email/Kindle delivery is also configured, the exact EPUB attached to that email is *also* saved into this same vault folder, as `<date> <time> digest.epub` (same timestamp as the note from that run). This gives you a local, always-available copy of what a run actually generated, independent of whether the email itself made it all the way to your Kindle — useful for confirming content without needing SMTP or Amazon delivery to have worked.

### Kobo (Google Drive / Dropbox)

Kobo has no Kindle-style built-in send-to-device email address — a Kobo pulls new books from a linked cloud folder on its own Wi-Fi sync schedule instead, so delivery here is "drop it in the folder" rather than "push it to the device." Google Drive and Dropbox are each independent, optional targets; Dropbox additionally supports an email-based route. Configure any subset.

#### Google Drive

```bash
export NEWS_DIGEST_GDRIVE_FOLDER_ID=your-drive-folder-id
export NEWS_DIGEST_GDRIVE_CLIENT_ID=your-oauth-client-id
export NEWS_DIGEST_GDRIVE_CLIENT_SECRET=your-oauth-client-secret
export NEWS_DIGEST_GDRIVE_REFRESH_TOKEN=your-refresh-token
```

One-time setup to get these values (you only do this once per Google account):

1. In the [Google Cloud Console](https://console.cloud.google.com/), create a project (or use an existing one) and enable the **Google Drive API** (APIs & Services → Library).
2. Under APIs & Services → Credentials, create an **OAuth client ID** of type **Web application**. Under "Authorized redirect URIs," add exactly `https://developers.google.com/oauthplayground`. Note the Client ID and Client Secret this generates — these are `NEWS_DIGEST_GDRIVE_CLIENT_ID`/`_CLIENT_SECRET`.
3. Open the [OAuth 2.0 Playground](https://developers.google.com/oauthplayground/), click the gear icon (top right), check **"Use your own OAuth credentials,"** and paste in the Client ID/Secret from step 2.
4. In the left panel (Step 1), find **Drive API v3**, select the `https://www.googleapis.com/auth/drive.file` scope, and click **Authorize APIs** — sign in and consent with the Google account whose Drive you want to use.
5. Click **Exchange authorization code for tokens**. The refresh token shown is `NEWS_DIGEST_GDRIVE_REFRESH_TOKEN` — it does not expire on its own as long as you used your own credentials (not the Playground's shared ones) in step 3.
6. `NEWS_DIGEST_GDRIVE_FOLDER_ID` is the id in a Drive folder's URL: `https://drive.google.com/drive/folders/<this-part>`.

#### Dropbox

Direct API upload:

```bash
export NEWS_DIGEST_DROPBOX_FOLDER_PATH=/kobo
export NEWS_DIGEST_DROPBOX_APP_KEY=your-app-key
export NEWS_DIGEST_DROPBOX_APP_SECRET=your-app-secret
export NEWS_DIGEST_DROPBOX_REFRESH_TOKEN=your-refresh-token
```

One-time setup:

1. Create an app at the [Dropbox App Console](https://www.dropbox.com/developers/apps) — "Scoped access," either "App folder" (simplest — isolates the app to its own folder) or "Full Dropbox." Note the App key and App secret (`NEWS_DIGEST_DROPBOX_APP_KEY`/`_APP_SECRET`).
2. Under the app's **Permissions** tab, enable `files.content.write`, then save.
3. Visit `https://www.dropbox.com/oauth2/authorize?client_id=<your-app-key>&response_type=code&token_access_type=offline` in a browser (signed in to the account you want) and click **Allow**. Since no redirect URI is configured, Dropbox displays the authorization code directly on the page for you to copy.
4. Exchange it for a refresh token:
   ```bash
   curl -u '<your-app-key>:<your-app-secret>' \
     -d code=<code-from-step-3> \
     -d grant_type=authorization_code \
     https://api.dropboxapi.com/oauth2/token
   ```
   The `refresh_token` field in the response is `NEWS_DIGEST_DROPBOX_REFRESH_TOKEN` — it doesn't expire.

Email to Kobo's Dropbox-linked address (works independently of, or alongside, the API route above):

```bash
export NEWS_DIGEST_DROPBOX_EMAIL_TO=your-unique-address@dropbox.com
```

Get this address from your Kobo device itself (or Kobo/Dropbox's account settings, model-dependent) after enabling Dropbox sync on the device — this reuses the same SMTP configuration from the Email/Send-to-Kindle section above, just a second recipient.

### Optional

```bash
export NEWS_DIGEST_EXTRACTOR=trafilatura       # or "defuddle" — default is trafilatura
export NEWS_DIGEST_SYNTHESIS_ENABLED=true      # default is off; see design.md before enabling — the
                                                # scheduled path's synthesis mechanism isn't wired up yet
export NEWS_DIGEST_STATE_PATH="/custom/path/run_state.json"  # default: ~/.local/state/news-digest/run_state.json
export NEWS_DIGEST_FEEDS_CONFIG_PATH="/custom/path/feeds.json"  # default: the packaged feeds.json below
```

### RSS feed sources

Every feed the digest pulls from — which outlets, which topics, which are keyword-filtered — lives in `src/news_digest/infrastructure/feeds/feeds.json`, not in code. Add, remove, or re-point a feed by editing that file directly; no rebuild or code change needed. Each topic key (`ottawa`, `canada`, `hong-kong`, `china`, `tech`, `global`) holds a `direct` list (feeds fully dedicated to that topic) and a `keyword_filtered` list (broader feeds — World, Asia — filtered down by keyword match). Use the `find-rss-feed` Claude Code skill to look up and verify a working feed URL for a new outlet before adding it (outlets move these without notice — this file has already needed fixes for a dead RTHK URL and a redirecting SCMP one).

By default every topic shares one story cap (10, see `domain/topics.py::STORIES_PER_TOPIC_CAP`) across all its feeds. Add `"cap": N` to any feed entry to exempt it from that shared cap and give it its own limit instead — e.g. The Verge's full-content feed is high-volume enough that it would otherwise crowd out slower outlets, so it's configured with `"cap": 20` of its own:

```json
{ "outlet": "The Verge", "url": "https://www.theverge.com/rss/partner/subscriber-only-full-feed/rss.xml", "cap": 20 }
```

Every fetch also has a request timeout — `RssFeedSource`'s default is 15 seconds (`rss_feed.py::DEFAULT_TIMEOUT_SECONDS`). Add `"timeout": N` (seconds) to a feed entry to give it more or less time than that default — CBC's feeds are set to 20s after intermittent read timeouts showed up in practice even though the feeds themselves respond in well under a second in isolation, which points to transient slowness on CBC's end (rate limiting, load) rather than a wrong URL or a genuinely slow feed:

```json
{ "outlet": "CBC", "url": "https://www.cbc.ca/webfeed/rss/rss-world", "timeout": 20 }
```

A topic's feeds are fetched concurrently (up to 8 at once, `RssFeedSource`'s `max_workers`), and every candidate article's full-text extraction runs concurrently too (`build_digest`'s `max_workers`, also 8 by default) — both are independent network I/O, so this is a real wall-clock speedup, not just a config knob.

## Running it

From Claude Code, the on-demand command:

```
/news-digest
```

Or directly:

```bash
uv run python -m news_digest.cli
```

By default the lookback window is since the last successful run (48 hours on the very first run). Override it for one run with `--since <duration>` (a number plus `d` or `h`, e.g. `3d` or `48h`):

```bash
uv run python -m news_digest.cli --since 3d
```

A `--since` run still records its completion time as the new last-success timestamp on success, so the next unoverridden run continues forward from there.

There is no scheduled/unattended run yet — see "Current status" below.

## Development workflow

```bash
just lint        # ruff check + format check
just format      # ruff format (auto-fix)
just typecheck    # pyrefly
just test         # pytest, functional-first (see the python-testing skill for conventions)
just mutate       # mutmut — mutation testing over src/, using the same test suite
just crap         # crap4py — flags any function that's both complex and undertested
```

`just mutate` and `just crap` are slower; run them before finishing a change, not on every save. `just test` deliberately includes one real integration test that shells out to `npx defuddle` — if that one fails and everything else passes, check that Node/npm is installed and you have network access, rather than assuming the pipeline itself is broken.

## Current status

This is mid-implementation. What works end to end today:

- On-demand ingestion → extraction → cross-outlet grouping → EPUB + Obsidian rendering → delivery to email/Kindle, Obsidian vault, a local vault EPUB copy, Google Drive, and Dropbox (API upload and/or email-to-Dropbox, for Kobo), all covered by functional tests.

What's explicitly not built yet (see `openspec/changes/news-digest/design.md`'s Open Questions):

- **Scheduled/unattended runs.** A Claude Code cloud routine was evaluated and ruled out (no local filesystem access, needs a git remote). The likely direction is a local `launchd` job, not yet implemented.
- **Synthesis on the scheduled path.** The on-demand command can generate a cross-outlet synthesis inline; the scheduled path has no equivalent hook yet.
- Comment/discussion sections from any outlet — evaluated and deliberately out of scope (see `proposal.md`).

## Project layout

See `CLAUDE.md` for the tooling stack and `ARCHITECTURE.md` for the folder layout, the pipeline, and every port/adapter pairing.
