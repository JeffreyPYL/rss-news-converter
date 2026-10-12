---
paths:
  - '**/*.ts'
  - '**/*.tsx'
  - package.json
  - tsconfig.json
  - bun.lockb
  - bun.lock
---

# TypeScript security

Applies to every TypeScript task. Universal security rules in `rules/common/01-security-baseline.md` apply across all languages; this document defines TypeScript-specific runtime, library, and supply-chain enforcement.

## Secrets and configuration
- MUST NOT commit secrets, API keys, private tokens, or `.env` files into source control.
- MUST validate and load all environment variables and secrets at application startup into a strongly-typed configuration object using Zod. Prohibit arbitrary, unvalidated `process.env` or `Bun.env` access scattered throughout business logic.
- MUST wrap sensitive values (tokens, credentials) in a dedicated branded type or redaction wrapper that masks values in `toString()`, `util.inspect()`, or `JSON.stringify()` (e.g. printing `[REDACTED]`).
- MUST NOT log sensitive request payloads, authorization headers, credit cards, or personal data (PII). Log identifiers and metadata instead, using structured logging with explicit attribute whitelisting.

```ts
import { z } from "zod";

const EnvSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  PORT: z.coerce.number().default(3000),
  DATABASE_URL: z.string().url(),
  API_SECRET: z.string().min(16),
});

export type EnvConfig = z.infer<typeof EnvSchema>;
export const config: EnvConfig = EnvSchema.parse(process.env);
```

## Prototype pollution and object safety
- MUST NOT use uncontrolled dynamic property assignment (`target[key] = value`) or unsafe recursive object merging on untrusted data.
- MUST reject or sanitize keys matching `__proto__`, `constructor`, or `prototype` when parsing or deep-merging untrusted objects.
- MUST prefer `Map` or `Object.create(null)` for arbitrary user-supplied key-value dictionaries to prevent prototype chain traversal.
- MUST parse untrusted JSON input through validated Zod schemas (`Schema.parse(JSON.parse(payload))`) rather than casting with `as Type`.

## Injection defenses and safe queries
- MUST use parameterized queries or type-safe query builders (e.g. Drizzle ORM, Kysely, Prisma, or Bun SQLite bound statements). NEVER interpolate raw strings or concatenate SQL with template literals: `SELECT * FROM users WHERE id = ${id}`.
- MUST NOT execute shell commands using string concatenation or `sh -c` / `child_process.exec()`.
- MUST use vector-based argument arrays with `Bun.spawn(["binary", "arg1", "arg2"])` or `child_process.spawn()`. Sanitize and validate all dynamic arguments before execution.
- MUST escape and sanitize any user-controlled input before rendering into HTML, SVG, or DOM contexts to prevent Cross-Site Scripting (XSS).

## Cryptography and timing attacks
- MUST use standard cryptographically secure pseudorandom number generators: `crypto.randomBytes()`, `crypto.getRandomValues()`, or `crypto.randomUUID()`. NEVER use `Math.random()` for security-sensitive tokens, IDs, or nonces.
- MUST use constant-time comparison (`crypto.timingSafeEqual()`) when validating authorization tokens, HMAC signatures, or password hashes to prevent timing attacks.
- MUST use modern cryptographic primitives from Web Crypto API or Node `crypto` (e.g. SHA-256, AES-256-GCM, Argon2id). NEVER use MD5 or SHA-1 for security operations.

## Supply chain and dependency auditing
- MUST commit `bun.lockb` or `bun.lock` for all applications and services to guarantee deterministic builds.
- MUST run `bun audit` (or `bun x audit-ci`) in CI and on a recurring schedule to catch vulnerable dependencies against the GitHub Advisory / npm databases.
- MUST review and pin external dependencies; prefer native Bun / Web standard APIs (`fetch`, `WebSocket`, `crypto`, `ReadableStream`) over bloated third-party npm packages.
