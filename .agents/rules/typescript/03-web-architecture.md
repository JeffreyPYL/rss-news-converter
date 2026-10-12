---
trigger: model_decision
description: Web service architecture for TypeScript (Bun HTTP, Elysia, Hono, or Fastify), layered separation (interface -> service -> crud -> common), route DTO validation, and error middleware. Use when building or changing web handlers, routers, services, or middleware.
---

# TypeScript web architecture

Applies to web services, REST APIs, and microservices in TypeScript. Standardizes on high-performance HTTP engines (Bun native HTTP, Elysia, Hono, or Fastify) and strict architectural layering.

## Framework choices
- MUST standardize on modern, high-performance engines:
  - **Bun HTTP** (`Bun.serve`) for minimal-overhead microservices.
  - **Elysia** or **Hono** for high-throughput, type-safe APIs with built-in schema validation.
  - **Fastify** for large enterprise services requiring mature plugin ecosystems.
- Express is **DEPRECATED** for new services due to lack of native async error handling, slow router performance, and outdated type definitions.

## Directional layered architecture
Code MUST adhere to a strict directional dependency hierarchy:

```
interface (routes, controllers, DTOs, transport middleware)
  ↓
service (domain business logic, use cases, orchestrations)
  ↓
crud (data access repositories, database clients, ORM models)
  ↓
common (telemetry, logging, configuration, shared domain errors)
```

Upward dependencies are **STRICTLY PROHIBITED**. A service MUST NOT import route handlers, and a CRUD repository MUST NOT import business services.

### 1. Interface layer (`src/interface/` or `src/api/`)
- Contains HTTP route definitions, request handlers, route parameter schemas, and serialization.
- MUST validate all incoming requests (body, params, query, headers) using Zod schemas before touching business logic.
- Route handlers MUST NOT contain direct database queries or raw SQL.
- Handlers invoke domain services and map the resulting `Result<T, E>` into HTTP status codes:

```ts
import { Hono } from "hono";
import { zValidator } from "@hono/zod-validator";
import { CreateOrderSchema } from "./dto/order.dto";
import type { OrderService } from "../service/order-service";

export function createOrderRouter(orderService: OrderService) {
  const router = new Hono();

  router.post("/", zValidator("json", CreateOrderSchema), async (c) => {
    const data = c.req.valid("json");
    const result = await orderService.createOrder(data);

    if (!result.ok) {
      return c.json({ error: result.error.message }, 400);
    }
    return c.json(result.value, 201);
  });

  return router;
}
```

### 2. Service layer (`src/service/`)
- Houses core business rules, transactional logic, and use-case workflows.
- MUST NOT accept framework-specific HTTP objects (`Request`, `Response`, `Context`). All inputs must be plain, validated domain data.
- Returns explicit `Result<T, E>` types so callers handle all failure modes.
- Coordinates calls across one or more CRUD repositories.

### 3. CRUD / Data access layer (`src/crud/` or `src/repository/`)
- Encapsulates database queries, ORM calls (Drizzle, Kysely, Prisma), and external storage APIs.
- Translates database records into domain entity types before returning them to services.
- Exposes repository interfaces (e.g. `OrderRepository`) to allow seamless in-memory fake injection during unit testing.

### 4. Common layer (`src/common/`)
- Cross-cutting concerns: structured logger, telemetry (OpenTelemetry), application configuration, and base error definitions.
- Free of any domain-specific business logic.

## Centralized error middleware
- Applications MUST install a global error handler at the application boundary to intercept unhandled exceptions.
- Internal errors (stack traces, SQL errors, raw filesystem paths) MUST NEVER be returned to the client in production responses. Log them server-side with structured trace IDs and return a generic RFC 7807 problem detail payload:

```json
{
  "type": "about:blank",
  "title": "Internal Server Error",
  "status": 500,
  "traceId": "c8a4b679-0c6a-4d2b-bb48-8df0c34f2ad5"
}
```
