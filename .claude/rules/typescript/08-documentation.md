
# TypeScript documentation

Applies to all TypeScript documentation, TSDoc comments, API documentation generation, and architectural decision records.

## TSDoc syntax standards
- All public functions, classes, interfaces, types, and exported constants MUST be documented using standard **TSDoc** syntax (`/** ... */`).
- MUST use standard TSDoc tags:
  - `@param` - Documents each parameter, its purpose, and constraints.
  - `@returns` - Explains return value shapes and meaning.
  - `@throws` - Details unrecoverable errors thrown (if any).
  - `@typeParam` - Explains generic type parameters.
  - `@example` - Code sample demonstrating correct usage.
  - `@deprecated` - Identifies deprecated APIs with migration instructions.
- Private implementation details SHOULD use standard `//` comments rather than docblocks.

```ts
/**
 * Calculates the discounted total for a given order line item.
 *
 * @param item - The line item containing quantity and unit price in cents.
 * @param discountPercent - Discount to apply, between 0 and 100 inclusive.
 * @returns The final discounted price in integer cents.
 *
 * @example
 * ```ts
 * const total = calculateDiscountedPrice({ qty: 2, unitPriceCents: 1000 }, 10);
 * // returns 1800
 * ```
 */
export function calculateDiscountedPrice(
  item: Readonly<{ qty: number; unitPriceCents: number }>,
  discountPercent: number
): number {
  const subtotal = item.qty * item.unitPriceCents;
  return Math.round(subtotal * (1 - discountPercent / 100));
}
```

## Documentation generation with TypeDoc
- Public packages, libraries, and SDKs SHOULD use **TypeDoc** (`typedoc`) to automatically generate API documentation from source code and TSDoc comments.
- Generated docs MUST NOT be committed to git if generated as part of a build artifact; generate on demand or in CI deployment pipelines.

## README architecture
Every TypeScript service or package MUST include a root `README.md` structured as follows:
1. **Title and Purpose**: One-paragraph summary of what the service does and its role in the system.
2. **Architecture**: High-level block diagram or list of core modules (interface, service, crud, common).
3. **Prerequisites**: Required Bun version (`bun --version`) and system dependencies.
4. **Development Workflow**: Clear list of `just` recipes (`just fmt`, `just lint`, `just typecheck`, `just test`, `just dev`).
5. **Environment Configuration**: Table detailing all required and optional environment variables validated by Zod.

## Architectural Decision Records (ADRs)
- Non-trivial technical choices (e.g. database client, web framework selection, authentication mechanism) MUST be documented as an ADR under `docs/adr/`.
- Format: Title, Status, Context, Decision, Consequences, and Alternatives Considered.
