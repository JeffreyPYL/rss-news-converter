set dotenv-load := true

install:
    uv sync

lint:
    uv run ruff check src tests
    uv run ruff format --check src tests

format:
    uv run ruff format src tests

typecheck:
    uv run pyrefly check src

test:
    uv run coverage run -m pytest
    uv run coverage lcov -o coverage.lcov

mutate: test
    uv run mutmut run

crap: test
    uv run crap4py --lcov coverage.lcov src/

dev:
    uv run python -m news_digest.cli
