
# Security baseline

Universal security principles applicable across all programming languages, frameworks, and runtime environments. Language-specific rules (such as `rules/rust/01-security.md` or `rules/python/01-security.md`) define concrete library and compiler enforcement mechanisms.

## Secrets and configuration
- MUST NOT commit secrets, tokens, keys, credentials, or `.env` files into source control.
- MUST load secrets from the environment into a strongly-typed configuration structure once, at application startup. Prohibit arbitrary environment variable lookups scattered across business logic.
- MUST wrap sensitive values (tokens, passwords, API keys) in dedicated secret wrapper types (such as `SecretString` in Rust or `SecretStr` in Python) whose string and debug formatting automatically masks or redacts the secret payload (e.g. `[REDACTED]` or `**********`).
- MUST NOT log sensitive headers, request bodies, authentication tokens, or personally identifiable information (PII). Log correlated trace and entity identifiers rather than raw payloads.

## Errors and information leakage
- MUST NOT return internal error messages, stack traces, database exceptions, or local file system paths to external clients.
- MUST map internal errors at the public trust boundary to stable, standardized status codes and opaque error descriptions. Detailed diagnostic errors must be recorded only in server-side logs.
- MUST NOT allow untrusted external inputs or I/O operations to cause unhandled crashes or panics. Handle all error branches explicitly with structured results or exception handlers.

## Input validation and boundary defenses
- MUST validate all inputs at the outer trust boundary (HTTP routes, RPC handlers, CLI argument parsers, message consumers) before passing data to inner domain or service layers.
- MUST reject unexpected or extraneous payload fields by default.
- MUST enforce network boundary guards: maximum request body size limits, request timeouts, and pagination bounds (with enforced upper limits) on all public collection endpoints.
- MUST derive the authenticated actor/principal directly from the validated session or cryptographic token, never trusting an arbitrary client-supplied user or tenant ID (Insecure Direct Object Reference / IDOR defense). Every authorization and data retrieval check MUST filter explicitly by the resolved principal.

## Injection defense and query parameterization
- MUST use parameterized queries or type-safe query builders with bound parameters exclusively. NEVER construct database queries (SQL, NoSQL), system shell commands, LDAP queries, or template expressions using string concatenation or unescaped format strings.
- MUST escape and sanitize all dynamic content rendered in HTML or browser contexts to prevent Cross-Site Scripting (XSS).

## Supply chain and dependency management
- MUST commit cryptographically verified lockfiles for all production applications and services.
- MUST execute automated vulnerability audits (e.g. `cargo audit`, `uv audit`, `pip-audit`, `npm audit`) in CI pipelines and on recurring schedules.
- MUST enforce explicit license allow-lists and verify that no unauthorized third-party registries or unpinned dependencies are consumed.
