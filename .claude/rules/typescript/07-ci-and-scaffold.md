---
description: CI pipeline, justfile, package.json, tsconfig.json, and project scaffold for TypeScript repos using Bun, Biome, and tsc. Use when creating or editing GitHub Actions workflows, the justfile, package.json, or bootstrapping a new TypeScript project.
paths:
  - '**/*.ts'
  - '**/*.tsx'
  - package.json
  - tsconfig.json
  - bun.lockb
  - bun.lock
---

# TypeScript CI pipeline and project scaffold

Applies to TypeScript repository scaffolding, CI pipelines, and build orchestration. Standardizes on Bun, Biome, tsc, and standardized `justfile` recipes.

## Package manager and lockfile
- MUST use **Bun** exclusively for package management, script execution, and lockfile generation.
- MUST commit `bun.lockb` or `bun.lock` for all applications and services.
- Dependencies in CI MUST be installed using `bun install --frozen-lockfile`.

## Standardized `justfile` recipes
Every TypeScript project MUST include a root `justfile` exposing the standard task recipes matching CI steps:

```just
# Standard justfile for TypeScript projects

set shell := ["bash", "-uc"]

# Show recipe listing
default:
    @just --list

# Format code with Biome
fmt:
    bun x @biomejs/biome format --write .

# Check formatting without writing
fmt-check:
    bun x @biomejs/biome format .

# Lint code with Biome
lint:
    bun x @biomejs/biome check --write .

# Check lint rules without writing
lint-check:
    bun x @biomejs/biome check .

# Static type check with TypeScript
typecheck:
    bun x tsc --noEmit

# Run unit and integration tests
test:
    bun test

# Run tests with coverage threshold
cov:
    bun test --coverage --coverage-threshold=85

# Audit dependencies for known vulnerabilities
audit:
    bun audit

# Run all verification gates (matches CI)
ci: fmt-check lint-check typecheck test audit
```

## Project scaffolding (`package.json`)
The root `package.json` MUST configure module boundaries, scripts, and peer dependencies:

```json
{
  "name": "my-service",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "bun --watch src/index.ts",
    "start": "bun src/index.ts",
    "build": "bun build src/index.ts --outdir dist --target bun",
    "typecheck": "tsc --noEmit",
    "lint": "biome check .",
    "format": "biome format --write .",
    "test": "bun test"
  },
  "dependencies": {
    "zod": "^3.23.8"
  },
  "devDependencies": {
    "@biomejs/biome": "1.9.4",
    "@types/bun": "latest",
    "typescript": "^5.6.3"
  }
}
```

## Continuous Integration workflow (`.github/workflows/ci.yml`)
CI MUST enforce formatting, linting, typechecking, tests, and security auditing on every PR and main branch push:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Bun
        uses: oven-sh/setup-bun@v2
        with:
          bun-version: latest

      - name: Install dependencies
        run: bun install --frozen-lockfile

      - name: Format check
        run: bun x @biomejs/biome format .

      - name: Lint check
        run: bun x @biomejs/biome check .

      - name: Type check
        run: bun x tsc --noEmit

      - name: Run tests with coverage
        run: bun test --coverage --coverage-threshold=85

      - name: Dependency audit
        run: bun audit
```
