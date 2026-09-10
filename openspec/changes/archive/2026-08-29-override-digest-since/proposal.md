## Why

The on-demand trigger always looks back from `RunState`'s persisted `last_success` (or a 48-hour default on the very first run). There's no way to pull a wider or narrower window on demand — e.g. to backfill a day you know you missed, or to re-run a shorter test window — without hand-editing `run_state.json`.

## What Changes

- Add an optional `--since <duration>` CLI flag to `python -m news_digest.cli`, accepting a relative duration (`3d`, `48h`) that overrides the lookback start for that run only.
- When `--since` is omitted, behavior is unchanged: the lookback comes from `RunState.lookback_since()` as today.
- A run started with `--since` still calls `state.record_success()` on success exactly as an unoverridden run does — the override changes only where this run's window starts, not how the next run's window is computed. No special-case "restore the old state" logic.
- Per-topic story caps (`STORIES_PER_TOPIC_CAP = 10`) are unaffected — a `--since` run pulling a multi-day window still caps at 10 most-recent stories per topic for the whole run, same as any other run. No spec or code change to `story-digest`.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `digest-triggers`: the on-demand trigger requirement gains an optional `--since` override input that replaces the state-derived lookback for that invocation.

## Impact

- `src/news_digest/cli.py`: `main()` gains argument parsing (stdlib `argparse`) for `--since`; `run_digest()` accepts an optional pre-computed `since` override instead of always calling `state.lookback_since()`.
- `.claude/commands/news-digest.md`: documents the new `--since` flag for on-demand invocation.
- No change to `src/news_digest/infrastructure/state/run_state.py`, `domain/topics.py`, or any other pipeline stage.
