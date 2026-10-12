# rss-news-converter

A personal automation that pulls news from RSS feeds (BBC, CBC, Globe and Mail, SCMP/RTHK) across topic buckets, extracts full article text, groups same-story coverage, and delivers a digest to Obsidian and email/Kindle. Full design lives in `openspec/` — this file is tooling and coding conventions, not the feature spec.

## Stack

- **Python**, package-managed with **uv** (`uv add`, `uv sync`, `uv run`)
- **ruff** for lint and format
- **Pyrefly** (Meta's Rust type checker) for type checking — not mypy/pyright/Pyre
- **pytest** + **pytest-httpx** for functional tests, **mutmut** for mutation testing, **crap4py** for the CRAP-score gate — see the `python-testing` skill for how these three are actually used
- **pydantic** for every domain/application/infrastructure data object (`Article`, `Story`, `ExtractedContent`, `DeliveryResult`, `SkippedSource`, `DirectFeed`, `KeywordFilteredFeed`, `RunStateData`) and **pydantic-settings** for `Settings` (`.env` support) — a deliberate choice over stdlib `dataclasses`, made for validation-on-construction and free (de)serialization even though the codebase's own complexity didn't strictly require it
- **just** as the command runner — see `justfile`:
  - `just install` — `uv sync`
  - `just lint` — `ruff check .` and `ruff format --check .`
  - `just typecheck` — `pyrefly check`
  - `just test` — `pytest`
  - `just mutate` — `mutmut run` (functional suite must be green first)
  - `just crap` — `crap4py` against `src/` using the coverage file from `just test`
  - `just dev` — run the digest CLI locally against real feeds
- **httpx** is the only HTTP client used anywhere in this codebase (RSS fetch, article fetch). This is load-bearing, not a preference: `pytest-httpx` (the test-mocking plugin) only intercepts `httpx`, so `requests`/`urllib`/shelling out to `curl` would be unmockable and untestable.

## Architecture

See `ARCHITECTURE.md` for the folder layout, the pipeline, and every port/adapter pairing. Keep it in sync when a source file under `src/news_digest/` changes shape — the `architecture-doc-check` skill exists to catch this.

## Testing

See the `python-testing` skill for the full TDD, mocking, mutation-testing, and CRAP-score workflow — it applies to every test written in this repo.
