---
description: CI pipeline, justfile, and project scaffold for Python repos using uv, ruff, pyrefly, and pytest. Use when creating or editing GitHub Actions workflows, the justfile, pyproject.toml, or bootstrapping a new Python project.
paths:
  - '**/*.py'
  - pyproject.toml
  - uv.lock
---

# Python CI and project scaffold

## Required files
A production Python repository MUST include in its root:
- `pyproject.toml`: Project configuration, dependency specifications, and tool configs (Ruff, Pyrefly, Pytest, Coverage).
- `uv.lock`: Deterministic dependency lockfile committed to source control.
- `.python-version`: Exact Python runtime version pin (e.g. `3.12.7`).
- `justfile`: Unified command runner mirroring CI commands identically for local development.
- `README.md`: Getting started, architecture overview, and developer commands.
- `.github/workflows/ci.yml`: Automated CI pipeline running the identical recipes defined in `justfile`.

## Dependency management with uv
- MUST use **uv** for all dependency installation, virtual environment management, tool execution, and lockfile generation.
- MUST NOT use legacy `requirements.txt`, `pip`, or `poetry`.
- Project initialization: `uv init --app` or `uv init --lib`.
- Adding dependencies: `uv add <package>` (or `uv add --dev <package>`).
- Environment synchronization: `uv sync --frozen --all-extras`.

## Justfile standard recipes
Every repository MUST provide a `justfile` exposing the following standardized recipes:

```just
set shell := ["bash", "-uc"]

# Format code
fmt:
    uv run ruff format .

# Check formatting
fmt-check:
    uv run ruff format --check .

# Run linter
lint:
    uv run ruff check .

# Fix lint errors automatically where supported
lint-fix:
    uv run ruff check --fix .

# Static type checking
typecheck:
    uv run pyrefly check

# Quick test run
test:
    uv run pytest -n auto

# Test with coverage enforcement
cov:
    uv run pytest -n auto --cov=src --cov-report=term-missing --cov-fail-under=85

# Dependency security audit
audit:
    uv audit

# Run all checks required for CI
ci: fmt-check lint typecheck cov audit
```

## GitHub Actions CI workflow
The CI workflow MUST mirror the `just ci` steps using `astral-sh/setup-uv`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v3
        with:
          enable-cache: true
          cache-dependency-glob: "uv.lock"

      - name: Set up Python
        run: uv python install

      - name: Install dependencies
        run: uv sync --frozen --all-extras

      - name: Format check
        run: uv run ruff format --check .

      - name: Lint check
        run: uv run ruff check .

      - name: Type check
        run: uv run pyrefly check

      - name: Test and coverage
        run: uv run pytest -n auto --cov=src --cov-report=xml --cov-fail-under=85

      - name: Security audit
        run: uv audit
```
