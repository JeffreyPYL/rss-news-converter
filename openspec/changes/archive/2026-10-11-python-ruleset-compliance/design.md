## Context

The repository defines strict standards in `CLAUDE.md`, `ARCHITECTURE.md`, and the `python-testing` skill, but current implementation details have drifted:
1. `src/news_digest/application/synthesis.py` directly imports `Settings` from `news_digest.infrastructure.settings`, violating the core hexagonal rule that `application/` must never depend on concrete `infrastructure/` classes. Furthermore, docstrings and comments assume an exclusively Claude Code runtime rather than an agent-agnostic interface.
2. The project's AI coding guidelines and skills exist only under `CLAUDE.md`, `.claude/skills/`, and `.claude/commands/`. When pairing with Antigravity (`agy`), workspace rules (`GEMINI.md` / `AGENTS.md`) and project skills (`python-testing`, `architecture-doc-check`, `find-rss-feed`, `readme-doc-check`) are missing from `.agents/`, causing inconsistent behavior across AI assistants.
3. The virtual environment `.venv/bin/` contains hardcoded shebangs referencing a previous directory name (`/Users/jeffreyleung/dev/claude-news/`), causing `uv run pytest` / `just test` to fail to spawn.
4. Pyrefly type checking lacks a `pyrefly.toml` project configuration, failing to resolve installed site-packages when run via `just typecheck` (`pyrefly check src`).
5. `pyproject.toml` lacks explicit `[tool.ruff]` linting and formatting configuration.
6. In `tests/functional/test_cli.py`, `NOW` was hardcoded to August 28, 2026. Because `state.lookback_since()` defaults to 48 hours before the current system time, tests run after August 30, 2026 filter out the mocked articles as stale, causing `test_run_digest_delivers_to_email_obsidian_and_the_epub_copy` to fail.
7. Mutation testing (`mutmut`) revealed surviving mutants in feed fetching, digest building, and rendering that need tight test assertions.
8. `ARCHITECTURE.md`'s injected seams table omits `DropboxClient` and `DriveFilesResource` added for Kobo delivery.

See `proposal.md` for motivation.

## Goals / Non-Goals

**Goals:**
- Enforce strict layer boundaries: `application/` depends only on `domain/` and `application/ports.py`.
- Establish first-class multi-agent AI assistant compliance for both Claude Code and Antigravity (`agy`), keeping rules (`CLAUDE.md`, `GEMINI.md`, `AGENTS.md`) and project skills in 100% sync.
- Ensure all quality-gate recipes in `justfile` (`just lint`, `just typecheck`, `just test`, `just crap`, `just mutate`) succeed cleanly.
- Fix test suite failures caused by time-drift and stale shebangs.
- Address surviving mutants from `mutmut` to ensure high test rigor per the `python-testing` skill.
- Synchronize `ARCHITECTURE.md` to reflect all current injected seams.

**Non-Goals:**
- Altering the user-facing CLI arguments or behavior of `news-digest`.
- Introducing new external third-party dependencies.
- Refactoring domain models (`models.py`) or business logic that is already compliant.

## Decisions

### Decision 1: Decouple `application/synthesis.py` from `infrastructure/` and Generalize Agent Interface
- **Choice**: Remove `from news_digest.infrastructure.settings import Settings` from `synthesis.py`.
  - Change `apply_synthesis(digest: dict[Topic, list[Story]], synthesis_by_story_key: dict[str, str], enabled: bool = True) -> None`.
  - Move the settings-parsing function `synthesis_enabled()` into `infrastructure/settings.py` (e.g. as a property on `Settings.is_synthesis_enabled: bool`) or `cli.py`, and pass the boolean flag into `apply_synthesis`.
  - Generalize docstrings so synthesis text is described as supplied by the calling AI agent turn (Claude Code or Antigravity `agy`) or automated runner.
- **Alternatives Considered**:
  - *Keep Settings in synthesis.py*: Rejected because `ARCHITECTURE.md` strictly specifies: "`application/` depends only on `domain/` and the `Protocol`s in `ports.py`, never on a concrete `infrastructure/` class directly."
  - *Define a Settings protocol in ports.py*: Overkill for a single boolean toggle; passing `enabled: bool` directly keeps `application` pure and trivial to test.

### Decision 2: Multi-Agent Parity for Antigravity (`agy`) and Claude Code
- **Choice**:
  1. Add `GEMINI.md` and `AGENTS.md` at repo root mirroring the coding conventions, tech stack, and testing discipline in `CLAUDE.md`.
  2. Sync custom project skills from `.claude/skills/` into `.agents/skills/`:
     - `python-testing`
     - `architecture-doc-check`
     - `find-rss-feed`
     - `readme-doc-check`
  3. Provide an Antigravity workflow/skill under `.agents/skills/` mirroring the on-demand run instruction in `.claude/commands/news-digest.md`.
  4. Update `openspec/config.yaml` context to refer to both `CLAUDE.md` and `GEMINI.md`.
- **Alternatives Considered**:
  - *Symlink `.claude` to `.agents`*: Rejected because git repositories and various OS environments/sandboxes can fail or handle cross-tool symlinks inconsistently; `.agents/` has its own directory structure and conventions. Keeping the skill definitions in `.agents/skills/` conforms directly to the standard Antigravity workspace layout.

### Decision 3: Configure Pyrefly with `pyrefly.toml`
- **Choice**: Create `pyrefly.toml` in the repo root specifying Python version 3.13, project root, and site-package search paths (pointing to `.venv/lib/python3.13/site-packages`).
- **Rationale**: Enables `just typecheck` (`uv run pyrefly check src`) to work without relying on manual command-line flags or failing on missing import resolutions.

### Decision 4: Standardize Ruff configuration in `pyproject.toml`
- **Choice**: Add `[tool.ruff]` and `[tool.ruff.lint]` sections in `pyproject.toml` targeting Python 3.13 and specifying standard rule groups: `E` (pycodestyle errors), `F` (Pyflakes), `I` (isort), `UP` (pyupgrade), `B` (flake8-bugbear), `SIM` (flake8-simplify).
- **Rationale**: Codifies lint rules explicitly rather than relying on unpinned defaults, ensuring long-term consistency.

### Decision 5: Resolve test time-drift in `test_cli.py`
- **Choice**: In `tests/functional/test_cli.py`, initialize the `RunState` fixture or mock test data relative to `datetime.now(UTC)` (or pass an explicit `since_override` / set `state.record_success(at=NOW - timedelta(hours=1))`).
- **Rationale**: The pipeline's `state.lookback_since()` uses `datetime.now(UTC) - 48h` on a first run. Testing with a static timestamp months in the past guarantees that articles will be ignored as expired unless the run state or lookback is explicitly aligned.

### Decision 6: Kill surviving mutants in test suite
- **Choice**: Add assertions to existing test files for branches that survived in `mutmut`:
  - `application/build_digest.py`: assert candidate ordering preservation and empty candidate handling.
  - `infrastructure/feeds/rss_feed.py`: assert feed timeout handling, keyword matching edge cases, and `skipped` reason recording.
  - `infrastructure/rendering/epub_renderer.py` & `obsidian_renderer.py`: assert index linking, image duplicate deduplication, and topic header escaping.
  - `infrastructure/delivery/google_drive_delivery.py`: assert field error handling.
- **Rationale**: Per the `python-testing` skill, surviving mutants indicate assertion gaps that must be closed before a change is done.

### Decision 7: Keep `ARCHITECTURE.md` synchronized
- **Choice**: Update `ARCHITECTURE.md`'s port/adapter and injected seams table to include:
  - `DropboxClient` for `DropboxApiDelivery` (wraps `dropbox.Dropbox`).
  - `DriveFilesResource` and `DriveExecutable` for `GoogleDriveDelivery` (wraps `googleapiclient.discovery.build("drive", "v3").files()`).
- **Rationale**: Satisfies the living documentation rule and the `architecture-doc-check` skill.

## Risks / Trade-offs

- **[Risk] Updating `apply_synthesis` signature affects existing tests** → **Mitigation**: `tests/functional/test_synthesis.py` and `src/news_digest/cli.py` are the only callers and will be updated in the same commit.
- **[Risk] Ruff cache collisions under sandboxed environments** → **Mitigation**: Document or configure Ruff cache directory in `pyproject.toml` or `justfile` if necessary.
- **[Risk] Mutmut suite execution time** → **Mitigation**: Tests remain functional-first with mocked network boundaries; mutmut excludes `@pytest.mark.integration` per configuration.
- **[Risk] Dual agent documentation drift (CLAUDE.md vs GEMINI.md)** → **Mitigation**: Standardize both on identical core sections; mention both in `README.md` and `openspec/config.yaml`.
