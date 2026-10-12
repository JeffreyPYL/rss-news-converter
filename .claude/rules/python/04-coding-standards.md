---
paths:
  - '**/*.py'
  - pyproject.toml
  - uv.lock
---

# Python coding standards

## Strict static typing and Pyrefly
- MUST type-annotate all function signatures (all parameters and explicit return types, including `-> None`).
- MUST NOT use bare `Any`. Where dynamic typing is unavoidable, use `object` with type narrowing (`isinstance`), `TypeVar`, generic parameters, or explicit `cast()` with an explanatory comment.
- MUST run `pyrefly check` in strict mode in CI. No untyped calls or missing attributes permitted.
- MUST use standard library typing primitives (PEP 585 / PEP 604): `list[str]`, `dict[str, int]`, `tuple[int, ...]`, `int | str`, `T | None` instead of `typing.List`, `typing.Dict`, `typing.Union`, or `typing.Optional`.
- MUST use `typing.Final` or `typing.Literal` for constants and fixed discriminator values.

## Domain modeling with Pydantic v2
- MUST model all external boundaries, API payloads, DTOs, and serialized structures using Pydantic v2 (`pydantic.BaseModel`).
- MUST set `model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)` on domain value models to guarantee immutability and reject unexpected fields.
- MUST use `Annotated` with Pydantic validators (`Field(min_length=...)`, `AfterValidator`, etc.) to enforce domain constraints at initialization.
- MUST use `pydantic_settings.BaseSettings` with typed fields and `SecretStr` for application configuration and environment variables.

## Internal data structures and immutability
- MUST prefer immutable data structures. For internal value objects that do not require validation or deserialization, use `@dataclass(frozen=True, slots=True)` or `typing.NamedTuple`.
- MUST NOT use mutable default arguments (e.g. `def fn(items: list = []):`). Use `def fn(items: Sequence[str] | None = None):` with `items = items or []` or an immutable tuple default `items: tuple[str, ...] = ()`.
- MUST avoid global mutable state. Encapsulate state within lifecycle-managed service objects or dependency injection containers.

## Error handling and failure modes
- Domain operations MUST use explicit, typed errors. Either:
  1. Return a typed `Result[T, E]` union (or a `Result` type pattern) for predictable operational failures, or
  2. Raise domain-specific exceptions inheriting from an application base exception (e.g. `DomainError`).
- MUST NOT catch bare `except:` or catch `Exception` indiscriminately unless at the outermost handler for top-level logging and error mapping.
- When catching and re-raising exceptions, MUST preserve the original cause using `raise NewException(...) from err`.
- MUST NOT use exceptions for normal control flow.

## Functions and API design
- MUST limit functions to a single responsibility. Prefer small, composable functions over monolithic procedures.
- MUST name functions and variables using `snake_case`, classes with `PascalCase`, and constants with `UPPER_SNAKE_CASE`.
- MUST define `__all__` in public library modules to expose only intentional public interfaces.
