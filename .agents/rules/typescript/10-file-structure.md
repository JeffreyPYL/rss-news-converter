---
trigger: glob
globs: '**/*.ts, **/*.tsx, package.json, tsconfig.json, bun.lockb, bun.lock'
---

# TypeScript file structure

Applies to all TypeScript source code files and directory organization. Enforces single responsibility per file, strict file length limits, and colocated unit tests.

## One concept per file
- Each source file MUST define exactly one primary concept (domain entity, service class, repository, value object, router).
- Files MUST be named in kebab-case matching the primary concept:
  - `user-service.ts`
  - `order-repository.ts`
  - `auth-middleware.ts`
  - `password-hasher.ts`
- **Garbage-dump files are strictly forbidden**: Never create `utils.ts`, `helpers.ts`, `common.ts`, or `misc.ts`. Decompose utilities into specific, domain-named modules (e.g. `date-formatter.ts`, `currency-calculator.ts`).

## File length limit (400-line rule)
- A TypeScript source file MUST NOT exceed **400 non-test lines of code**.
- When a file exceeds 400 lines, it indicates multiple responsibilities. It MUST be decomposed into a directory module:
  ```
  src/service/order/
  ├── order-service.ts          # Core orchestration facade (<400 lines)
  ├── order-validator.ts        # Order input validation logic
  ├── order-pricing.ts          # Discount and tax calculations
  └── index.ts                  # Public re-exports for the module
  ```

## Sibling test placement
- Unit tests MUST be placed directly adjacent to the file under test using the `.test.ts` or `.spec.ts` suffix:
  ```
  src/service/
  ├── user-service.ts
  └── user-service.test.ts
  ```
- Colocating unit tests ensures tests are updated alongside code changes and makes coverage gaps immediately visible in file trees.
- Integration tests spanning multiple layers or requiring external databases belong in a top-level `tests/` directory (e.g. `tests/integration/order-flow.test.ts`).

## Directory layout reference
```
src/
├── index.ts                  # Main entry point (boots server/CLI)
├── interface/                # Layer 1: HTTP routes, DTOs, controllers
│   ├── routes/
│   └── dto/
├── service/                  # Layer 2: Business logic, domain rules
│   ├── user-service.ts
│   └── user-service.test.ts
├── crud/                     # Layer 3: Repositories, database queries
│   ├── user-repository.ts
│   └── user-repository.test.ts
└── common/                   # Layer 4: Shared cross-cutting concerns
    ├── config.ts
    ├── logger.ts
    └── result.ts
tests/                        # End-to-end / Integration tests
```
