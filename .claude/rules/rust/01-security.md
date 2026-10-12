---
paths:
  - '**/*.rs'
  - Cargo.toml
  - Cargo.lock
---

# Security

Applies to every Rust task. Rules are context, not enforcement: the gates in `07-ci-and-scaffold.md` enforce them.

## Unsafe code
- MUST set `unsafe_code = "forbid"` in `[workspace.lints.rust]`. A crate that truly needs `unsafe` MAY downgrade itself to `deny` and allow it in one small module.
- MUST put a `// SAFETY:` comment on every `unsafe` block and a `# Safety` section on every `unsafe fn`. Enable `clippy::undocumented_unsafe_blocks`.
- MUST wrap `unsafe` in a safe abstraction. Never expose it through a safe public API.
- SHOULD run `cargo +nightly miri test` on any crate that contains `unsafe`.
- Edition 2024: `unsafe extern "C" { ... }` and `&raw const` / `&raw mut`; `unsafe_op_in_unsafe_fn` applies.

## Secrets and config
- MUST NOT commit secrets, tokens, keys, or `.env` files. Load secrets from the environment into a typed `Config` struct once, at startup. No `std::env::var` calls scattered through business code.
- MUST wrap secrets in a newtype whose `Debug`/`Display` print `[REDACTED]` (for example `secrecy::SecretString`). Never derive `Debug` on a struct that holds a raw secret.
- MUST NOT log request bodies, credentials, tokens, or personal data. Log identifiers, not payloads. Format with structured fields (`tracing::info!(user_id = %id, "...")`).

## Errors and responses
- MUST NOT return internal error text (`e.to_string()`, `{:?}`, SQL errors, file paths) to a client. Map every internal error to a stable status code plus a fixed public message, and log the detail server-side.
- MUST NOT use `unwrap()` / `expect()` on external input or I/O. Return `Result`.

## Input validation and authorization
- MUST validate at the trust boundary (handler, `#[server]` fn, CLI arg parse) and convert into validated newtypes (`UserId`, `Email`). Inner layers accept only validated types.
- MUST set body-size limits, timeouts, and pagination caps on every network-facing route (tower layers: `RequestBodyLimitLayer`, `TimeoutLayer`).
- MUST derive the acting principal from the authenticated session, never from a client-supplied id, and thread it explicitly into service calls (IDOR defense). Every query on user-owned data filters by principal.
- MUST treat every Leptos `#[server]` fn as a public HTTP endpoint: add authn, authz, rate limiting, and validation yourself (the Leptos book says server functions are "syntax sugar for defining a public API").
- MUST use parameterized queries only (`sqlx::query!`, bind params). Never build SQL with `format!`.

## Supply chain
- MUST commit `Cargo.lock` for binaries and applications.
- MUST run `cargo deny check` (advisories, licenses, bans, sources) in CI; run advisories on a schedule as well, because a new advisory can break unrelated PRs. Generate the baseline with `cargo deny init`.
- MUST run `cargo audit` (RustSec) on a schedule. Every ignored advisory needs a reason and expiry date in a comment.
- MUST keep the license allow-list explicit and set `[sources] unknown-registry = "deny"`, `unknown-git = "deny"`.
- SHOULD pin third-party GitHub Actions by commit SHA (general supply-chain advice, not Rust-specific).
- SHOULD justify each new dependency; prefer the standard library or an already-present crate.

```toml
# deny.toml (excerpt)
[advisories]
unmaintained = "all"
unsound = "all"
ignore = []          # "RUSTSEC-YYYY-NNNN" // reason, expires YYYY-MM-DD
[licenses]
allow = ["MIT", "Apache-2.0"]   # extend deliberately
[bans]
wildcards = "deny"
[sources]
unknown-registry = "deny"
unknown-git = "deny"
```

Source: `docs/research/rust-best-practice.md` sections 2, 7; `docs/research/rust-web-stack.md` section 1. https://doc.rust-lang.org/book/ch20-01-unsafe-rust.html , https://rustsec.org/ , https://embarkstudios.github.io/cargo-deny/checks/cfg.html , https://book.leptos.dev/server/25_server_functions.html . The `cargo audit` ignore syntax and the license allow-list contents are `(unverified)`; confirm with `cargo deny init` output.
