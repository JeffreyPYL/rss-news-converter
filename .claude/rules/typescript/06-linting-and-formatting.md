---
paths:
  - '**/*.ts'
  - '**/*.tsx'
  - package.json
  - tsconfig.json
  - bun.lockb
  - bun.lock
---

# TypeScript linting and formatting

Applies to all TypeScript files. Standardizes on Biome as the single unified linter and formatter, coupled with strict `tsc --noEmit` type checking.

## Tooling choice
- MUST use **Biome** (`@biomejs/biome`) as the unified linter and formatter. Do not install ESLint, Prettier, or separate import-sorting plugins; Biome replaces all three with sub-100ms execution.
- MUST use **tsc** (`tsc --noEmit`) as the static type validator.
- Format check command: `bun x @biomejs/biome format .`
- Format fix command: `bun x @biomejs/biome format --write .`
- Lint check command: `bun x @biomejs/biome check .`
- Lint fix command: `bun x @biomejs/biome check --write .`
- Type check command: `bun x tsc --noEmit`

## Formatter standards
- Indentation: 2 spaces (no tabs).
- Quotes: Double quotes (`"`) for strings and JSX.
- Line width: 100 characters.
- Semicolons: Always require semicolons.
- Trailing commas: Multiline trailing commas required where syntactically valid.
- Import organization: Automatically sorted and grouped by Biome (`organizeImports`).

## Linter configuration (`biome.json`)
The workspace MUST contain a root `biome.json` with recommended rules enabled and zero warning tolerance in CI:

```json
{
  "$schema": "https://biomejs.dev/schemas/1.9.4/schema.json",
  "vcs": {
    "enabled": true,
    "clientKind": "git",
    "useIgnoreFile": true
  },
  "files": {
    "ignoreUnknown": false,
    "ignore": ["node_modules", "dist", "build", "coverage", ".worktrees"]
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2,
    "lineWidth": 100
  },
  "javascript": {
    "formatter": {
      "quoteStyle": "double",
      "semicolons": "always",
      "trailingCommas": "all"
    }
  },
  "organizeImports": {
    "enabled": true
  },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true,
      "correctness": {
        "noUnusedVariables": "error",
        "noUnusedImports": "error"
      },
      "style": {
        "useConst": "error",
        "noNonNullAssertion": "warn"
      },
      "suspicious": {
        "noExplicitAny": "error",
        "noDoubleEquals": "error"
      },
      "complexity": {
        "noExtraBooleanCast": "error"
      }
    }
  }
}
```

## Static type checker (`tsconfig.json`)
The workspace MUST contain a root `tsconfig.json` enforcing strict checking:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "noImplicitAny": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "isolatedModules": true,
    "verbatimModuleSyntax": true,
    "forceConsistentCasingInFileNames": true,
    "skipLibCheck": true,
    "noEmit": true
  },
  "include": ["src/**/*", "tests/**/*"]
}
```

## Suppression policy
- Blanket file ignores (`// biome-ignore-all`) are STRICTLY FORBIDDEN.
- Single-line suppression MUST name the exact rule and provide an explanation:
  ```ts
  // biome-ignore lint/suspicious/noExplicitAny: third-party untyped callback argument
  ```
- Unjustified suppressions MUST be rejected in code review.
