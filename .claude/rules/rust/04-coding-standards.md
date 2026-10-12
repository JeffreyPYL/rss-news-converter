---
paths:
  - '**/*.rs'
  - Cargo.toml
  - Cargo.lock
---

# Rust coding standards

## API design
- MUST follow the Rust API Guidelines: RFC 430 casing, `as_`/`to_`/`into_` conversion names, `From`/`AsRef` over bespoke converters, `Debug` on every public type, private struct fields, sealed traits where extension is not intended.
- MUST use newtypes for domain ids and units (`UserId(Uuid)`, not `Uuid`; no bare `u64` for money) and enums instead of `bool` flags or strings.
- MUST put `# Errors`, `# Panics`, and `# Safety` sections in docs of public items where they apply.
- SHOULD use a builder or validated constructor when a struct has 5+ fields or invariants. Group 5+ parameters into a value type (`clippy::too_many_arguments` default threshold is 7).

## Errors and panics
- MUST return `Result` for expected failures. Panic only for bugs that cannot be encoded in types.
- MUST NOT use `unwrap()` / `expect()` outside tests, examples, and prototypes. `expect("...")` is allowed only when infallibility is provable; the message states why.
- Libraries and domain crates: typed errors with `thiserror` 2.x (`#[error]`, `#[from]`, `#[source]`). Applications, binaries, and tests: `anyhow::Result` with `.context()`.
- MUST NOT expose `anyhow::Error` in a library's public API (community convention, `(unverified)` as a quote).
- MUST make invalid states unrepresentable: validated newtypes with a private field and fallible constructor; `enum` over flag combinations; `NonZero*` where zero is invalid.

```rust
#[derive(Debug, thiserror::Error)]
pub enum OrderError {
    #[error("order {0} not found")]
    NotFound(OrderId),
    #[error(transparent)]
    Store(#[from] StoreError),
}
```

## Ownership and style
- MUST take `&str`/`&[T]`/`impl AsRef<..>` in parameters; return owned types. Clone only with a reason; never to silence the borrow checker without thought.
- MUST prefer immutable bindings, iterators, and `match` over index loops and flag variables. Use guard clauses (early `return` / `?`) to keep functions flat.
- MUST keep pure logic in functions over values and do I/O at the edge (see `06-linting-and-formatting.md`).
- MUST NOT use magic numbers; name constants.
- Imports go at module top. Edition 2024; `rust-version` set in `Cargo.toml`.
- Handle time as UTC internally (`jiff` or `chrono`); convert at the edge only.

## Async and tokio
- MUST NOT block in async code (sync I/O, heavy CPU, `std::thread::sleep`). Use `tokio::task::spawn_blocking` (cannot be aborted once started) or `block_in_place` (multi-thread runtime only).
- MUST NOT hold a `std::sync::Mutex` guard across `.await` (makes the future `!Send`; clippy `await_holding_lock`, lint name `(unverified)`). Scope the guard, wrap state in a struct with sync methods, or use a task plus channel. Use `tokio::sync::Mutex` only when the lock must span an await.
- MUST treat `select!` branches as cancellable. Cancel-safe: `mpsc::Receiver::recv`, `broadcast::Receiver::recv`, `watch::Receiver::changed`, `TcpListener::accept`. NOT cancel-safe: `read_exact`, `read_to_end`, `write_all`, lock/semaphore acquires. In loops, pin the future outside or use a cancel-safe API.
- Dropping a future cancels it at its next `.await`. `JoinHandle::abort()` returns immediately; await the handle to confirm shutdown.
- MUST put timeouts and retry limits with backoff on every external call.

## Dependencies
- MUST declare shared versions in `[workspace.dependencies]` and inherit with `dep.workspace = true`.
- MUST NOT add a dependency for what the standard library or an existing dependency does.

Source: `docs/research/rust-best-practice.md` sections 1, 2, 9, 10. https://rust-lang.github.io/api-guidelines/checklist.html , https://doc.rust-lang.org/book/ch09-03-to-panic-or-not-to-panic.html , https://docs.rs/thiserror/latest/thiserror/ , https://docs.rs/tokio/latest/tokio/task/index.html , https://tokio.rs/tokio/tutorial/shared-state , https://docs.rs/tokio/latest/tokio/macro.select.html
