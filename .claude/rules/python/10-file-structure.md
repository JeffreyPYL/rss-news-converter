---
paths:
  - '**/*.py'
  - pyproject.toml
  - uv.lock
---

# Python file and directory structure

## One concept per file
- MUST dedicate each Python file to one cohesive concept (one primary domain class, a cohesive set of related functions, or one router group).
- Helper functions and private classes belong in the file with their primary consumer, or in a private sibling module (`_helpers.py`) if shared across multiple files in the same package.
- File names MUST be lowercase `snake_case.py`.

## 400-line size limit
- MUST NOT allow any single Python file to exceed **400 lines** of non-test code.
- When a file approaches or exceeds 400 lines, it MUST be decomposed into a subpackage directory:
  - Example: `payment_service.py` exceeding 400 lines becomes a package:
    ```
    payment_service/
    ├── __init__.py      # Re-exports public classes, defines __all__
    ├── models.py        # Pydantic DTOs and value types
    ├── processor.py     # Core payment processing logic
    ├── gateway.py       # Integration with external payment API
    └── errors.py        # Domain-specific exceptions
    ```

## Standard project layout (`src/` layout)
All Python applications and libraries MUST use the `src/` layout to prevent accidental imports of uninstalled local code:

```
my-project/
├── .github/workflows/ci.yml
├── docs/
├── src/
│   └── myapp/
│       ├── __init__.py
│       ├── common/
│       ├── crud/
│       ├── service/
│       └── interface/
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── .python-version
├── justfile
├── pyproject.toml
├── README.md
└── uv.lock
```

## Test file structure and naming
- Test files MUST be prefixed with `test_` (e.g. `test_payment_processor.py`).
- Shared pytest fixtures belong in `conftest.py` scoped to the directory level where they are needed.
- Unit tests test pure units with in-memory fakes under `tests/unit/` mirroring the `src/` hierarchy.
