## Context

`main()` in `src/news_digest/cli.py` currently takes no arguments — it's invoked as `python -m news_digest.cli` (via `just dev` and `.claude/commands/news-digest.md`). `run_digest()` unconditionally computes `since = state.lookback_since()`. See proposal.md for why an override is needed.

## Goals / Non-Goals

**Goals:**
- Let an on-demand run specify how far back to look, bypassing `RunState.lookback_since()` for that one invocation.
- Keep `record_success()` behavior identical whether or not `--since` was used.

**Non-Goals:**
- Changing `STORIES_PER_TOPIC_CAP` or any capping/grouping logic (proposal.md — confirmed unaffected).
- A scheduled-trigger equivalent of `--since` (scheduled trigger isn't wired up yet per `digest-triggers`'s design; out of scope here).
- Persisting or exposing the run's actual `since` value anywhere beyond the run itself.

## Decisions

**Duration format and parsing**: accept `<N><unit>` where unit is `d` or `h` (e.g. `3d`, `48h`), matching the two units already meaningful in this codebase (`RunState.DEFAULT_LOOKBACK` is expressed in hours; day-scale backfills are the stated use case). Parsed with a small stdlib regex (`^(\d+)([dh])$`) into a `timedelta` — no new dependency; this is a two-branch match, not worth a library.

**Argument parsing**: stdlib `argparse`, added directly in `main()`. This is the first CLI argument the tool has ever needed; no argparse subcommands or config-file layering, just one optional flag.

**Where the override is computed**: `main()` parses `--since` and, if present, computes `datetime.now(UTC) - timedelta` itself, passing the result into `run_digest()` as a new optional `since_override: datetime | None` parameter. `run_digest()` uses `since_override` instead of calling `state.lookback_since()` when it's not `None`. `RunState.lookback_since()` itself is untouched — it still exists for the normal (no-override) path, so its "self-heals a missed run" contract (feed-ingestion spec) stays intact for unoverridden runs.

**record_success() stays unconditional**: `run_digest()` already calls `state.record_success()` on any successful delivery, independent of how `since` was computed. No branching needed to satisfy "override becomes the new baseline" — that's just the existing code path, left alone.

**Invalid `--since` fails fast**: `argparse`'s `type=` callback raises on a malformed value, which `argparse` turns into a usage error and a non-zero exit before `main()` constructs any feed source, extractor, or delivery target — so a bad flag never touches the network.

## Risks / Trade-offs

[A `--since` window much wider than the persisted lookback pulls a lot more candidate articles than a normal run, but the existing per-topic cap (10) already bounds how many end up in the digest — no new risk beyond a slower run.] → No mitigation needed; this is the accepted, unchanged capping behavior (see proposal.md).

[`--since` and the persisted `last_success` can drift apart in a way that's surprising in hindsight — e.g. running `--since 7d` at a time when `last_success` was only 1 day old silently expands the window forward, and the next normal run continues from *this* run's completion time, not from the old `last_success`.] → This is the deliberately chosen behavior (override becomes the new baseline, per the proposal); flagged here so it's not rediscovered as a bug later.
