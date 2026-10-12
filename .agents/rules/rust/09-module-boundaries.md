---
trigger: model_decision
description: Crate layout, layers, visibility and dependency rules (ADR 0002). Use when creating any new crate, module, or file, changing visibility or public exports, or adding a dependency between crates.
---

# Module boundaries

Decision: [ADR 0002](../../docs/adr/0002-crate-per-layer-with-deny-wrappers.md) (supersedes the file-level part of [ADR 0001](../../docs/adr/0001-compiler-enforced-module-boundaries.md)). Do NOT add a `boundaries.toml`, a checker script, `cargo-pup`, or `modou`.

## Layers and words to use
- **interface** (api, gql, cli, queue): transport in. Parse, validate, map errors and DTOs; call `service`. No business rules.
- **service**: business and application logic. No transport types. Owns the transaction boundary.
- **crud**: data access tied to the context's domain concept (its database tables, its files): fetch, store, update. No business rules.
- **common**: cross-cutting code (logging, observability, http client, queue intake, shared types by concern). Never depends on a context.
- Direction: interface -> service -> crud -> common. Never upward, never skipping a layer.

## Crates: one per layer, flat under `crates/`
```
crates/
  orders/            facade: re-exports the router and the public service API only
  orders-api/ orders-gql/ orders-cli/    interface kinds, one crate each
  orders-service/
  orders-crud/       exports one small trait per aggregate + its real implementation
  common-logging/ common-observability/ common-http/ common-queue/
  app/               main: wires contexts and registers queue handlers
```
- MUST give each layer its own crate. Cargo rejects cycles, so no layer can import upward. A new `Cargo.toml` edge is an architecture change: state it in the OpenSpec change.
- MUST make other contexts depend on the `<ctx>` facade only. The facade exposes the router and the service API, nothing else.
- MUST NOT create a `utils` crate. Name a `common-*` crate by its concern. Move code into `common-*` only when a second consumer needs it.
- Generic clients (HTTP, queue) live in `common-*`. The context-specific fetch/update that uses them lives in `<ctx>-crud`, behind that crud's trait.
- Queues (`(open)` until integrated): consuming is an interface (`<ctx>-queue`); central intake and routing live in `common-queue`; the app crate registers handlers; publishing is outbound like HTTP.

## Who may depend on what: `deny.toml`
- MUST list, for every non-common crate, its allowed direct dependents with `wrappers`. A dependent not listed fails `cargo deny check bans`.
```toml
[bans]
deny = [
  { crate = "orders-crud",    wrappers = ["orders-service"] },
  { crate = "orders-service", wrappers = ["orders", "orders-api", "orders-gql", "orders-cli"] },
  { crate = "orders-api",     wrappers = ["orders", "app"] },
  { crate = "orders-gql",     wrappers = ["orders", "app"] },
  { crate = "orders-cli",     wrappers = ["app"] },
]
```
- MUST add the entries in the same change that adds the crate. A crate without an entry is unrestricted; `aw-ship-review` checks this.
- Tested with cargo-deny 0.20.2 on workspace members (see ADR 0002).

## Visibility inside a crate
- MUST default to `pub(super)` and `pub(crate)`; `pub` only for the crate's deliberate interface. Enable `unreachable_pub`.
- MUST keep `lib.rs` to `mod` declarations and deliberate `pub use` re-exports.
- File and folder layout inside a crate: `10-file-structure.md`.

## The layer question (every new file or crate)
- MUST, before creating it, answer: **which layer, who may use it, what may it use?** Encode the answers in the crate it lives in, its visibility, and its `deny.toml` entry. If unclear, stop and decide before writing code.
- The vocabulary grows with the project; a new layer is a recorded decision (OpenSpec change or ADR).

## Fake seams
- MUST export from each `<ctx>-crud` one small trait per aggregate (`OrderStore`) and its implementation; `<ctx>-service` is generic over it (static dispatch). No god-trait. The same pattern holds between interface and service. Only `app` wires real implementations.
- Unit tests use only a crate's public interface and fakes for the layer below (`05-testing.md`).

## Public API is a reviewed artifact
- MUST list every change to a public interface (new, removed, altered `pub` items and re-exports) in the OpenSpec change before implementing it.
- MUST check: `cargo public-api diff` (or the committed snapshot) must match the declaration, and `cargo semver-checks --baseline-rev origin/main -p <pkg>` must pass for crates with an external contract. `cargo-public-api` needs nightly; `--deny` is `(unverified)`.

Source: ADR 0002, ADR 0001; `docs/research/boundary-enforcement.md`. https://embarkstudios.github.io/cargo-deny/checks/bans/cfg.html , https://rust-lang.github.io/api-guidelines/flexibility.html , https://matklad.github.io/2021/08/22/large-rust-workspaces.html
