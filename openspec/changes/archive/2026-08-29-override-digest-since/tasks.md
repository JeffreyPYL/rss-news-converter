## 1. Since override in the CLI

- [x] 1.1 Add a duration parser (`^(\d+)([dh])$` → `timedelta`, stdlib `re`) to `src/news_digest/cli.py` and a functional test covering `3d`, `48h`, and a rejected malformed value (e.g. `3x`, `abc`).
- [x] 1.2 Add an optional `--since <duration>` argument to `main()` via stdlib `argparse`, using the parser from 1.1 as `type=`; thread an optional `since_override: datetime | None` parameter through `run_digest()` so it uses `since_override` when given and falls back to `state.lookback_since()` otherwise. Functional test: `run_digest()` called with a `since_override` uses it instead of `state.lookback_since()`; called without one, behavior is unchanged from before this change.
- [x] 1.3 Functional test: a successful run invoked with `--since` still calls `state.record_success()`, updating the persisted run state to the run's completion time (per `digest-triggers`'s "A since-overridden run still records success normally" scenario).
- [x] 1.4 Functional test: invoking with an invalid `--since` value exits non-zero via `argparse` before any feed source, extractor, or delivery target is constructed (per `digest-triggers`'s "An invalid since value is rejected before the pipeline runs" scenario).

## 2. Docs

- [x] 2.1 Update `.claude/commands/news-digest.md` to document the optional `--since <duration>` flag (format `3d`/`48h`) and that omitting it preserves today's behavior.
- [x] 2.2 Update README.md's CLI usage section (around the `uv run python -m news_digest.cli` invocation) to document `--since`, its duration format, and the default (state-derived) behavior when omitted.

## 3. Quality gate

- [x] 3.1 Run `just mutate` and `just crap` across the finished pipeline; fix any surviving mutant or any function scoring over 30 before this change is considered done.
  - `just crap`: every function ≤13.0, well under the 30 threshold.
  - `just mutate`: 2 real gaps in cli.py's new code fixed (help/description text, `parse_since_duration`'s error message, the `--since` flag string, a positive-parse test); 2 in pre-existing code (google_drive/email/dropbox delivery, epub/obsidian rendering, rss_feed, build_digest, defuddle_extractor) fixed (email Content-Type case, Dropbox `rstrip` charset). All other survivors (26) and "suspicious" statuses (11) verified empirically as genuinely equivalent mutants — library-level case-insensitivity/normalization (httpx headers, MIME codec names, Google API discovery, ebooklib's `lang`/media-type fallback and tag-repair), dead-code defaults unreachable given existing guards, or macOS's `getproxies_macosx_sysconf` crash risk on the pre-existing `trust_env` literal (already correctly tested; the crash is an environment quirk, not a coverage gap).
