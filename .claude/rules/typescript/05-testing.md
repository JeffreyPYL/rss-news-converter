---
paths:
  - '**/*.ts'
  - '**/*.tsx'
  - package.json
  - tsconfig.json
  - bun.lockb
  - bun.lock
---

# TypeScript testing

Applies to all TypeScript testing suites. Standardizes on Bun test, strict coverage thresholds, mutation testing with Stryker, and clear architectural test seams.

## Test runner
- MUST use **Bun test** (`bun test`) as the default test runner for fast, native TypeScript test execution with built-in mocking and snapshot capabilities.
- Tests execute with standard Jest/Vitest-compatible syntax (`describe`, `it`, `test`, `expect`, `beforeEach`).
- Use Vitest only when specific Vite frontend plugins or complex browser-environment runners are strictly required.

## Coverage thresholds
- Test suites MUST achieve at least **85% statement, branch, and line coverage** across domain and service code:
  ```bash
  bun test --coverage --coverage-threshold=85
  ```
- Critical security, authorization, and financial/billing logic MUST achieve 100% coverage.
- Code changes in PRs MUST NOT degrade overall workspace coverage.

## Mutation testing with Stryker
- Core domain logic, state machines, and business rules MUST be verified using **Stryker** (`@stryker-mutator/core` with `@stryker-mutator/vitest-runner` or `@stryker-mutator/jest-runner`).
- Stryker mutation score MUST achieve at least **75%** on critical business modules, verifying that test suites assert actual behavioral outcomes rather than merely exercising code paths.

## Test organization and naming
- Unit tests MUST reside in sibling test files adjacent to the source under test:
  - Source: `src/service/order-service.ts`
  - Unit test: `src/service/order-service.test.ts`
- Integration and end-to-end test suites spanning multiple subsystems MUST live in a top-level `tests/` or `test/` directory.
- Test descriptions MUST follow Scenario / Given-When-Then phrasing:

```ts
import { describe, expect, it } from "bun:test";
import { OrderService } from "./order-service";

describe("OrderService.createOrder", () => {
  it("given valid items, computes total and creates pending order", async () => {
    // Arrange
    const service = new OrderService(new FakeOrderRepository());
    // Act
    const result = await service.createOrder({ items: [{ id: "sku-1", qty: 2, priceCents: 1000 }] });
    // Assert
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.value.totalCents).toBe(2000);
      expect(result.value.status).toBe("pending");
    }
  });

  it("given empty items, returns validation error result", async () => {
    const service = new OrderService(new FakeOrderRepository());
    const result = await service.createOrder({ items: [] });
    expect(result.ok).toBe(false);
  });
});
```

## Test seams and isolation
- Unit tests MUST isolate external I/O (databases, network APIs, file systems) behind repository or client interfaces.
- Prefer in-memory fakes (e.g. `FakeUserRepository implements UserRepository`) over dynamic mocking libraries. Fakes provide compile-time guarantees when interfaces evolve.
- Unit tests MUST NOT make external network requests or depend on shared external state.
