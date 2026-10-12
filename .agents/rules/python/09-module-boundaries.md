---
trigger: model_decision
description: Python package layout, layer dependency direction, visibility rules, and automated import boundary enforcement. Use when creating modules, packages, modifying imports, or configuring boundary linters.
---

# Python module boundaries

## Layer hierarchy and dependency direction
Python projects MUST enforce strict directional dependency rules across layers:

```
┌──────────────────────────────────────────────┐
│                  interface                   │  (API routes, CLI commands, event consumers)
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│                   service                    │  (Domain logic, transaction workflows)
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│                    crud                      │  (Repositories, ORM entities, data queries)
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│                   common                     │  (Config, logging, telemetry, shared utils)
└──────────────────────────────────────────────┘
```

### Dependency rules:
1. **Downwards only**: A layer may only depend on layers below it. Never upward.
2. **No skipping layers**: `interface` MUST NOT bypass `service` to import `crud` directly.
3. **No upward leakage**: `service` MUST NOT import anything from `interface` (no HTTP request/response objects, no route definitions).
4. **Isolated common**: `common` MUST NOT import from `crud`, `service`, or `interface`.
5. **No circular dependencies**: Circular imports across modules or packages are strictly forbidden.

## Automated boundary enforcement
Boundary rules MUST be enforced automatically in CI using **import-linter** or Ruff's `banned-api`.

### import-linter configuration (`.importlinter` or `pyproject.toml`)
```ini
[importlinter]
root_package = myapp

[importlinter:contract:layers]
name = Layered architecture
type = layers
layers =
    myapp.interface
    myapp.service
    myapp.crud
    myapp.common

[importlinter:contract:no-service-web-leak]
name = Service layer must not import transport objects
type = forbidden
source_modules =
    myapp.service
forbidden_modules =
    myapp.interface
    fastapi
    starlette
    litestar
```

- Run boundary check command in CI:
  ```bash
  uv run lint-imports
  ```

## Visibility and module encapsulation
- Public API: Every package MUST declare its public members via `__all__` in `__init__.py`.
- Internal implementation details: Functions, classes, and variables not intended for export MUST be prefixed with a single leading underscore (`_internal_helper()`).
- External consumers MUST NOT import private underscored symbols from sibling or foreign packages.
