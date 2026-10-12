---
trigger: model_decision
description: Web service and UI architecture for Rust (Leptos + axum default, Topcoat alternative), crate layering, error handling, and API shape. Use when building or changing web handlers, server functions, routers, or app state.
---

# Web architecture

## Stack choice
- MUST default to **Leptos 0.8 + axum 0.8** (`leptos_axum` 0.8). Pin compatible 0.8.x versions in `[workspace.dependencies]`. MUST NOT use the 0.9 betas.
- Scaffold with `cargo leptos new --git https://github.com/leptos-rs/start-axum`; install with `cargo install --locked cargo-leptos` and `rustup target add wasm32-unknown-unknown`.
- Whether nightly Rust is still needed for Leptos 0.8 is `(unverified)`; follow the pinned `rust-toolchain.toml` and test the build.
- **Topcoat is the second option, not the default.** Use it only for a spike or a low-risk internal tool. WARNING: tokio-rs/topcoat states "Early-stage and experimental. Expect breaking changes." It is pre-1.0 and v0.10.0 was released 2026-10-03. If used, MUST pin the tag `v0.10.0` / SHA `3e7bb43948a61dadcdba5a79d99c0f3a75de1abc` (or the exact crate `=0.10.0`) and budget for breaking changes on every minor bump.
  ```toml
  topcoat = { git = "https://github.com/tokio-rs/topcoat", rev = "3e7bb43948a61dadcdba5a79d99c0f3a75de1abc" }
  ```
- Topcoat has no OpenAPI support and no WASM client. Serve any JSON API from separate axum handlers. Whether it builds on axum is `(unverified)`.

## One crate per bounded context
- MUST structure each context as one crate per layer plus a facade (layout, vocabulary, and `deny.toml` visibility rules in `09-module-boundaries.md`). Flow: interface -> service -> crud -> common.
- `<ctx>-api` (interface): thin transport only. Parse and validate input, call `service`, map errors and DTOs. Axum handlers and `#[server]` fns live here.
- `<ctx>-service`: business rules and orchestration. Owns the transaction boundary. No HTTP types.
- `<ctx>-crud`: the context's own data access. No business rules. Generic HTTP and queue clients are `common-*`.
- The `app` crate composes contexts: builds `AppState`, merges each facade's router with `.leptos_routes(...)`, applies layers, and handles shutdown.
- Cross-context calls MUST go through the other context's `<ctx>` facade, never its `crud`.

## Axum conventions
- MUST expose `pub fn router(state: AppState) -> Router` per context so tests inject fakes.
- MUST share state through the `State` extractor with a cheaply cloneable type (`Arc` inside), using `FromRef` for sub-states. Avoid `Extension`, which is checked at runtime.
- MUST keep the body-consuming extractor last in handler arguments.
- MUST define an `AppError` enum implementing `IntoResponse` (status plus JSON body) and `FromServerFnError` for server fns; handlers return `Result<T, AppError>` (pattern `(unverified)` against the docs page; standard axum practice).
- MUST add `TraceLayer`, a timeout, and a body limit as tower layers, and use `axum::serve(..).with_graceful_shutdown(signal)` on SIGTERM and Ctrl-C (`(unverified)`, from general axum knowledge).
- Configuration comes from one typed `Config` loaded at startup; no env reads in handlers.
- Expose liveness and readiness endpoints on a separate internal router/port from the public one.

## Leptos conventions
- MUST gate with features: `ssr` (server) and `hydrate` (browser). Server-only dependencies are `optional = true` and enabled only by `ssr`; otherwise the wasm build fails. `service`, `crud`, and axum code are `ssr`-only; shared `types` sit outside the gate.
- MUST keep `#[server]` fns thin adapters (`01-security.md` applies). Use a custom error implementing `FromServerFnError`. Do not use `usize`/`isize` in arguments (wasm32 vs 64-bit).
- MUST NOT branch on `cfg!(target_arch = "wasm32")` inside views; avoid invalid HTML nesting (`<div>` in `<p>`); write `<tbody>` explicitly. Gate browser-only crates (`gloo-net`) so they never run on the server.

## API shape
- REST routes follow the committed spec (`02-openapi.md`). Version in the path, paginate lists, use idempotency keys for retried commands (principle, from the old standard; not sourced).
- Webhook ingress verifies the signature on the raw body before parsing.

Source: `docs/research/rust-web-stack.md` sections 1-3, 5. https://book.leptos.dev/ , https://github.com/leptos-rs/start-axum , https://docs.rs/axum/latest/axum/ , https://docs.rs/leptos_axum/latest/leptos_axum/ , https://github.com/tokio-rs/topcoat . Layering is design guidance, not a fetched fact.
