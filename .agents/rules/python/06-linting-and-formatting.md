---
trigger: glob
globs: '**/*.py, pyproject.toml, uv.lock'
---

# Python linting and formatting

## Tooling choice
- MUST use **Ruff** for both formatting and linting. Do not combine Black, Flake8, or isort; Ruff replaces all three with sub-second execution.
- MUST use **Pyrefly** in strict mode as the primary static type linter.
- Format check command: `ruff format --check .`
- Lint check command: `ruff check .`
- Type check command: `pyrefly check`

## Formatter standards
- MUST enforce a consistent line length across the workspace (default: 88, or project-configured 100).
- MUST use double quotes for strings (`quote-style = "double"`) and 4 spaces for indentation.
- Code that does not pass `ruff format --check` MUST fail CI.

## Linter rules and categories
In `pyproject.toml`, under `[tool.ruff.lint]`, the following rule categories MUST be enabled:
- `F`: Pyflakes (logical correctness, undefined variables, syntax errors)
- `E`, `W`: pycodestyle (PEP 8 errors and warnings)
- `I`: isort (deterministic import sorting)
- `B`: flake8-bugbear (subtle bugs and design anti-patterns)
- `C4`: flake8-comprehensions (optimal list/dict/set comprehension usage)
- `TCH`: flake8-type-checking (moves type-only imports into `if TYPE_CHECKING:` guards to prevent circular imports and optimize startup performance)
- `UP`: pyupgrade (automatic modern syntax upgrades for targeted Python version)
- `S`: flake8-bandit (security flaws and hazardous function usage)
- `RUF`: Ruff-native checks (overlapping keys, asyncio pitfalls)

## Type-checking linter (Pyrefly)
- MUST configure Pyrefly with strict type checking enabled.
- MUST resolve all missing type annotations and incompatible assignments.
- MUST NOT suppress type errors using `# type: ignore` without specifying the exact error code and an explanatory comment.

## Configuration reference (`pyproject.toml`)
```toml
[tool.ruff]
target-version = "py312"
line-length = 88

[tool.ruff.lint]
select = [
    "F",    # Pyflakes
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "TCH",  # flake8-type-checking
    "UP",   # pyupgrade
    "S",    # flake8-bandit
    "RUF",  # Ruff-specific rules
]
ignore = []

[tool.ruff.lint.isort]
known-first-party = ["src"]

[tool.ruff.lint.flake8-type-checking]
strict = true

[tool.pyrefly]
mode = "strict"
```

## Suppression policy
- MUST NOT use blanket `# noqa` comments.
- Any lint suppression MUST target the specific rule (e.g. `# noqa: S101`) and MUST include an explanatory comment justifying why the suppression is safe and necessary.
