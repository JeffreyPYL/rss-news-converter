## Why

The codebase has accumulated architectural boundary violations, environment desynchronization, tooling gaps, and test suite rot that prevent full compliance with the repository's documented Python standards (`CLAUDE.md`, `ARCHITECTURE.md`, and the `python-testing` skill). Furthermore, the repository's AI agent rules and workflow scaffolding are single-agent bound to Claude Code (`CLAUDE.md`, `.claude/skills/`, `.claude/commands/`) while Antigravity (`agy`) is also actively used, creating agent configuration drift and missing skill discoveries in `.agents/`. Specifically:
1. `application/synthesis.py` illegally imports from `infrastructure/settings.py` and couples docstrings/caller assumptions solely to Claude Code turns.
2. Antigravity (`agy`) lacks repository rules (`GEMINI.md` / `AGENTS.md`) and workspace skills in `.agents/skills/` (such as `python-testing`, `architecture-doc-check`, `find-rss-feed`, `readme-doc-check`).
3. Virtual environment shebangs point to a stale directory path breaking standard tool spawning (`uv run pytest`).
4. Pyrefly type checking fails due to missing interpreter/search configuration.
5. Time drift causes test suite failures alongside surviving mutants.

Addressing these brings the repository into 100% compliance with its clean architecture rules, type checks, quality gates, and multi-agent AI pair-programming standards for both Claude Code and Antigravity (`agy`).

## What Changes

- **Multi-Agent Ruleset Compliance & Skills Parity**:
  - Add root agent rules (`GEMINI.md` / `AGENTS.md`) establishing the exact same Python stack, uv workflow, architectural boundaries, and testing discipline as `CLAUDE.md`.
  - Mirror project skills from `.claude/skills/` into `.agents/skills/` (`python-testing`, `architecture-doc-check`, `find-rss-feed`, `readme-doc-check`) so both Claude Code and Antigravity (`agy`) discover them natively.
  - Add an on-demand digest workflow/skill under `.agents/skills/` matching `.claude/commands/news-digest.md` for `agy`.
- **Clean Architecture & Agent-Agnostic Synthesis**:
  - Decouple `application/synthesis.py` from `infrastructure/settings.py` by removing the cross-layer import and having synthesis enablement injected via caller arguments (`cli.py` and application orchestrators), preserving the strict inward dependency rule (`domain` <- `application` <- `infrastructure`).
  - Generalize synthesis contracts so synthesis text can be provided by any calling AI agent turn (Claude Code or Antigravity `agy`) or automated trigger.
- **Tooling & Typecheck Scaffolding**: Add `pyrefly.toml` to configure Pyrefly with proper module search paths and site-packages resolution, making `just typecheck` succeed cleanly without manual path flags.
- **Ruff Linter Configuration**: Explicitly configure `[tool.ruff]` in `pyproject.toml` (rule selections, target Python 3.13, formatting) and ensure Ruff caching does not conflict with sandbox/permissions.
- **Environment & Spawn Fix**: Reinstall/relink `.venv` entry points to eliminate stale `/Users/jeffreyleung/dev/claude-news/` shebang paths so `uv run pytest` and CLI tools execute properly.
- **Test Suite Time-Drift Fix**: Fix `test_run_digest_delivers_to_email_obsidian_and_the_epub_copy` in `tests/functional/test_cli.py` to prevent hardcoded August 2026 timestamps from being discarded by the 48-hour lookback window, restoring a 100% green test suite.
- **Mutation Testing Compliance**: Address surviving and suspicious mutants identified by `mutmut` across `application/build_digest.py`, `infrastructure/feeds/rss_feed.py`, `infrastructure/delivery/google_drive_delivery.py`, and renderers/extractors.
- **Documentation Alignment**: Update `ARCHITECTURE.md`'s injected seams table to document `DropboxClient` (Dropbox) and `DriveFilesResource`/`DriveExecutable` (Google Drive), satisfying the living doc requirement. Update `README.md` and `openspec/config.yaml` to reference both `CLAUDE.md` and `GEMINI.md`.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
None (`skip_specs: true` enabled in `.openspec.yaml` as this is an internal refactoring, tooling, multi-agent configuration, and test quality change that does not alter externally observable feature requirements).

## Impact

- **Affected Code & Configuration**: `GEMINI.md`, `AGENTS.md`, `.agents/skills/`, `src/news_digest/application/synthesis.py`, `src/news_digest/cli.py`, `ARCHITECTURE.md`, `README.md`, `openspec/config.yaml`, `pyproject.toml`, `pyrefly.toml`, `tests/functional/test_cli.py`, and test assertions for surviving mutants.
- **Dependencies & Tooling**: Rebuilt `.venv` bin shebangs; configured Pyrefly (`pyrefly.toml`); configured Ruff in `pyproject.toml`; multi-agent discovery enabled for Antigravity (`agy`) and Claude.
- **Breaking Changes**: None. Internal interfaces between CLI and application for synthesis are updated, but CLI flags and external behavior remain unchanged.
