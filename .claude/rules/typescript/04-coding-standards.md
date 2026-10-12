---
paths:
  - '**/*.ts'
  - '**/*.tsx'
  - package.json
  - tsconfig.json
  - bun.lockb
  - bun.lock
---

# TypeScript coding standards

Applies to all TypeScript codebases. Enforces strict compiler typing, boundary validation, typed errors, and immutable design patterns.

## Strict compiler options (`tsconfig.json`)
All projects MUST enable strict mode compiler options in `tsconfig.json`:
- `"strict": true` (enables all core strict checks: `noImplicitAny`, `strictNullChecks`, `strictFunctionTypes`, `strictBindCallApply`, `strictPropertyInitialization`, `noImplicitThis`, `useUnknownInCatchVariables`)
- `"noUncheckedIndexedAccess": true` (treats property lookups on objects without explicit index fields as `T | undefined`)
- `"exactOptionalPropertyTypes": true` (distinguishes between optional properties omitted vs. assigned `undefined`)
- `"isolatedModules": true` (ensures single-file transpilation safety)
- `"verbatimModuleSyntax": true` (enforces explicit `import type` syntax)
- `"forceConsistentCasingInFileNames": true`

## Forbid `any` and unsafe assertions
- The `any` type is **STRICTLY FORBIDDEN** in application and domain code.
- Where a value's shape is unknown (e.g. raw external input, dynamic JSON), use `unknown` and narrow the type using type predicates (`val is Type`), `typeof`, `instanceof`, or Zod schemas.
- MUST NOT use non-null assertions (`!`) unless immediately preceded by a narrowing check or within unit test setups.
- MUST NOT use unsafe type casts (`as TargetType`) on unverified data. Use Zod parsing or user-defined type guards instead.
- MUST use `import type { ... }` when importing symbols only used for type declarations.

## Boundary validation and schema modeling with Zod
- MUST define all boundary contracts (HTTP request bodies, query strings, headers, environment variables, queue messages) using `Zod` schemas.
- MUST derive domain types directly from schemas via `z.infer<typeof Schema>` to keep validation logic and type signatures in sync.
- MUST set `.strict()` or `.strip()` on object schemas to prevent undeclared properties from polluting domain objects.

```ts
import { z } from "zod";

export const CreateUserRequestSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
  role: z.enum(["admin", "member"]).default("member"),
}).strict();

export type CreateUserRequest = z.infer<typeof CreateUserRequestSchema>;
```

## Discriminated unions and exhaustive matching
- Domain entities, state machines, and lifecycle transitions MUST be modeled as discriminated unions with a common literal discriminator tag (`kind`, `status`, or `type`).
- Branching logic on discriminated unions MUST be exhaustively handled with a `never` check:

```ts
type OrderState =
  | { status: "pending"; createdAt: Date }
  | { status: "paid"; paidAt: Date; transactionId: string }
  | { status: "cancelled"; reason: string };

function formatOrder(order: OrderState): string {
  switch (order.status) {
    case "pending":
      return `Pending since ${order.createdAt.toISOString()}`;
    case "paid":
      return `Paid txn:${order.transactionId}`;
    case "cancelled":
      return `Cancelled: ${order.reason}`;
    default: {
      const _exhaustive: never = order;
      throw new Error(`Unhandled order state: ${JSON.stringify(_exhaustive)}`);
    }
  }
}
```

## Typed error handling and Result pattern
- Operational and domain failures MUST be represented as explicit, typed return values rather than thrown exceptions.
- Domain and service functions MUST return a `Result<T, E>` discriminated union:

```ts
export type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

export function ok<T>(value: T): Result<T, never> {
  return { ok: true, value };
}

export function err<E>(error: E): Result<never, E> {
  return { ok: false, error };
}
```

- Thrown exceptions (`throw new Error(...)`) are reserved exclusively for unrecoverable programmatic bugs, invariant violations, or infrastructure panics.
- Handlers at the application boundary MUST catch unhandled exceptions and translate them into safe error responses without leaking internal stack traces.

## Immutability and purity
- MUST prefer immutable data structures: use `readonly` modifier on interfaces, `Readonly<T>`, and `readonly T[]`.
- Functions MUST avoid mutating arguments in place; return new objects or arrays instead.
- Avoid global mutable state. Inject dependencies explicitly via constructors or factory functions.
