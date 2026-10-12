---
trigger: glob
globs: '**/*.py, pyproject.toml, uv.lock'
---

# Python testing

## Test runners and plugins
- MUST use **pytest** as the primary test runner.
- MUST use **pytest-xdist** for parallel test execution (`pytest -n auto`).
- MUST use **pytest-cov** for branch and line coverage measurement. Enforce an overall minimum coverage bar of 85% (`--cov-fail-under=85`).
- MUST use **pytest-asyncio** in `strict` or `auto` mode for testing asynchronous coroutines.
- Primary test execution command:
  ```bash
  uv run pytest -n auto --cov=src --cov-report=term-missing --cov-fail-under=85
  ```

## Named test seams
1. **Unit Seam (`tests/unit/` or sibling `test_*.py`)**:
   - Tests pure functions, domain models, and service logic in complete isolation.
   - External dependencies (databases, external APIs) MUST be replaced with in-memory fakes. No network or filesystem I/O allowed in unit tests.
2. **Integration Seam (`tests/integration/`)**:
   - Tests interactions across component layers (e.g. repository talking to a real database container via testcontainers, or API routers with FastAPI `TestClient`).
   - Verifies transactions, schema migrations, and wire serialization.
3. **End-to-End Seam (`tests/e2e/`)**:
   - Tests full application lifecycles from input entry point to output side-effects.

## Mocking hygiene and fakes
- MUST prefer explicit in-memory fakes (e.g. `FakeUserRepository(UserRepository)`) over dynamic mock objects (`MagicMock` or `patch`).
- If `unittest.mock.patch` or `mocker` MUST be used, always specify `autospec=True` or `spec_set` to prevent mocking methods or attributes that do not exist on the real object.
- MUST NOT mock internal implementation details. Mock only at the boundaries of external I/O and non-deterministic providers (time, network, random seeds).

## Mutation testing with mutmut
- Domain models and core service logic MUST undergo mutation testing with `mutmut` to identify surviving mutants and weak assertions.
- Execution:
  ```bash
  uv run mutmut run --paths-to-mutate src/services/
  uv run mutmut results
  ```
- Any surviving mutant in core business logic indicates a missing test assertion and MUST be resolved.

## Property-based testing
- Complex parsing, validation, serialization, or algorithmic logic SHOULD use **Hypothesis** (`@given`) to discover edge cases, null characters, and boundary conditions automatically.

## Test structure and conventions
- MUST follow the Arrange-Act-Assert (AAA) pattern.
- MUST name tests descriptively: `test_<action>_<condition>_<expected_result>()` (e.g. `test_create_user_with_duplicate_email_raises_conflict_error()`).
- MUST NOT share mutable state across tests. Use pytest fixtures with appropriate scopes (`function` by default).
