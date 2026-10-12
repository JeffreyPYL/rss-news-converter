## 1. Environment & Tooling Scaffolding

- [x] 1.1 Re-generate virtual environment entry points and fix `.venv/bin/` shebangs so `uv run pytest` and development tools spawn cleanly without referencing stale directory paths, verifying with `uv run pytest --version`.
- [x] 1.2 Create `pyrefly.toml` configuring Python 3.13, project root, and site-packages path, and verify `just typecheck` (`pyrefly check src`) passes with 0 errors.
- [x] 1.3 Configure `[tool.ruff]` and `[tool.ruff.lint]` in `pyproject.toml` (target Python 3.13, select `E`, `F`, `I`, `UP`, `B`, `SIM`), and verify `just lint` succeeds.

## 2. Multi-Agent Ruleset Compliance & Skills Parity

- [x] 2.1 Create `GEMINI.md` and `AGENTS.md` at repo root mirroring `CLAUDE.md` coding standards, Python tooling stack, and testing discipline for Antigravity (`agy`), verifying with `git diff GEMINI.md`.
- [x] 2.2 Synchronize custom project skills from `.claude/skills/` into `.agents/skills/` (`python-testing`, `architecture-doc-check`, `find-rss-feed`, `readme-doc-check`), verifying directory contents with `ls .agents/skills`.
- [x] 2.3 Add an Antigravity on-demand digest workflow/skill in `.agents/skills/` equivalent to `.claude/commands/news-digest.md`, verifying with skill structure check.
- [x] 2.4 Update `README.md` and `openspec/config.yaml` to reference both `CLAUDE.md` and `GEMINI.md` for coding standards, verifying with `git diff README.md openspec/config.yaml`.

## 3. Architecture Boundary Enforcement & Synthesis Generalization

- [x] 3.1 Decouple `src/news_digest/application/synthesis.py` from `news_digest.infrastructure.settings`, moving settings-parsing to caller/infrastructure boundary, passing `enabled` directly to `apply_synthesis`, updating `cli.py` and `tests/functional/test_synthesis.py`, and verifying with `pytest tests/functional/test_synthesis.py`.
- [x] 3.2 Update `synthesis.py` docstrings and interfaces to be agent-agnostic (supporting both Claude Code and Antigravity `agy` turns), verifying clean lint via `just lint`.
- [x] 3.3 Update `ARCHITECTURE.md`'s injected seams table to document `DropboxClient` and `DriveFilesResource`/`DriveExecutable`, and verify documentation matches code via `git diff ARCHITECTURE.md`.

## 4. Test Suite Fixes & Mutation Hardening

- [x] 4.1 Fix time-drift in `tests/functional/test_cli.py::test_run_digest_delivers_to_email_obsidian_and_the_epub_copy` by aligning feed timestamps with the lookback window, and verify all 134 tests pass cleanly via `just test`.
- [x] 4.2 Add targeted functional test assertions for surviving mutants identified in `application/build_digest.py`, `infrastructure/feeds/rss_feed.py`, `infrastructure/delivery/google_drive_delivery.py`, and renderers.

## 5. Quality Gates

- [x] 5.1 Run `just test`, `just crap`, and `just mutate` across the entire codebase, verifying 100% green test suite, zero surviving mutants, and every function scoring under the CRAP score threshold of 30.
