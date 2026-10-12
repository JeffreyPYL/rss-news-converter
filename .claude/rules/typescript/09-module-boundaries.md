---
description: TypeScript module boundaries, directional layering enforcement, path aliases, and package exports maps. Use when creating modules, packages, modifying imports, or configuring layer boundaries.
paths:
  - '**/*.ts'
  - '**/*.tsx'
  - package.json
  - tsconfig.json
  - bun.lockb
  - bun.lock
---

# TypeScript module boundaries and layer enforcement

Applies to TypeScript workspace structure, module imports, path aliases, and package export maps. Enforces strict directional layering and encapsulation.

## Directional dependency rules
Modules MUST respect the strict directional hierarchy:

```
interface -> service -> crud -> common
```

Rules:
1. **No Upward Imports**: A module in an inner or lower layer MUST NEVER import from a higher layer (e.g., `service` importing `interface`, or `crud` importing `service`).
2. **No Circular Dependencies**: Circular imports between files or modules are strictly forbidden.
3. **Facade Re-exports**: Each layer or context MUST expose its public API via an `index.ts` file. External consumers should import from the layer facade rather than deep internal paths.

## Path aliases configuration (`tsconfig.json`)
The `tsconfig.json` MUST define explicit path mappings matching architectural layers:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@interface/*": ["src/interface/*"],
      "@service/*": ["src/service/*"],
      "@crud/*": ["src/crud/*"],
      "@common/*": ["src/common/*"]
    }
  }
}
```

## Boundary enforcement
- Workspaces SHOULD enforce layer boundaries using linter rules or dependency graph checks (e.g. `dependency-cruiser` or Biome's `noRestrictedImports`).
- Disallowed edges:
  - `src/crud/**` MUST NOT import `@service/*` or `@interface/*`
  - `src/service/**` MUST NOT import `@interface/*`
  - `src/common/**` MUST NOT import `@interface/*`, `@service/*`, or `@crud/*`

## Package export maps (`package.json`)
For libraries, SDKs, or monorepos, `package.json` MUST declare explicit `exports` maps to prevent consumers from reaching into private internals:

```json
{
  "name": "@my-org/core",
  "exports": {
    ".": {
      "import": "./dist/index.js",
      "types": "./dist/index.d.ts"
    },
    "./service": {
      "import": "./dist/service/index.js",
      "types": "./dist/service/index.d.ts"
    },
    "./crud": {
      "import": "./dist/crud/index.js",
      "types": "./dist/crud/index.d.ts"
    }
  }
}
```

Internal implementation helpers located outside exposed entry points remain private and inaccessible to external consumers.
