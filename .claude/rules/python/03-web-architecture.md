---
description: Web service architecture for Python (FastAPI or Litestar), layer separation (interface -> service -> crud -> common), async practices, and DTO validation. Use when building or changing web handlers, routers, services, or dependencies.
paths:
  - '**/*.py'
  - pyproject.toml
  - uv.lock
---

# Python web architecture

## Framework choices
- MUST default to **FastAPI** (with Pydantic v2) or **Litestar** for asynchronous web APIs.
- Framework version and ASGI server (e.g. `uvicorn` with `uvicorn[standard]`) MUST be pinned in `pyproject.toml`.

## Layered architecture
Code MUST follow a strict directional layering hierarchy:
```
interface (routes, handlers, DTOs)
  ↓
service (domain operations, business logic, transactions)
  ↓
crud (data access, repositories, database models)
  ↓
common (telemetry, logging, configuration, shared exceptions)
```

### 1. Interface layer (`interface/` or `api/`)
- Contains route handlers, endpoint controllers, request/response DTO schemas, and transport middleware.
- MUST validate all incoming payloads using Pydantic v2 models.
- MUST NOT contain business rules or raw database queries.
- Translates domain errors from the service layer into appropriate HTTP status codes (e.g. `NotFoundError` → 404, `ConflictError` → 409).

### 2. Service layer (`service/` or `services/`)
- Contains pure business logic, calculations, workflow orchestration, and domain models.
- MUST accept only validated domain types or DTOs; MUST NOT accept raw `Request` objects or HTTP transport primitives.
- Coordinates database transactions through repository abstractions.
- Raises typed domain exceptions on rule violations.

### 3. CRUD / Data access layer (`crud/` or `repositories/`)
- Encapsulates database tables, ORM models (e.g. SQLAlchemy 2.0 Async or SQLModel), and external persistence adapters.
- Interfaces are exposed via repository protocols (e.g. `UserRepositoryProtocol`).
- MUST NOT know about HTTP controllers, route paths, or web frameworks.

### 4. Common layer (`common/`)
- Shared utilities, configuration schemas (`BaseSettings`), structured logging, and metric instruments.
- May be imported by all layers; MUST NOT import from `interface`, `service`, or `crud`.

## Dependency injection
- Handlers MUST obtain services and database sessions via framework dependency injection (`Depends()` in FastAPI or `Provide()` in Litestar).
- Dependencies MUST be typed with abstract protocols or classes to allow painless substitution with in-memory fakes during unit testing.

## Asynchronous programming practices
- All network I/O, database interactions, and cache queries MUST use non-blocking `async` / `await` calls.
- MUST NOT execute blocking synchronous functions (e.g. `time.sleep()`, synchronous `requests`, or heavy synchronous file I/O) directly inside `async def` event loop threads. Use `anyio.to_thread.run_sync` or `asyncio.to_thread` when blocking operations are unavoidable.
- Database connections MUST be managed using asynchronous connection pools and scoped session context managers (`async with session_maker() as session:`).
