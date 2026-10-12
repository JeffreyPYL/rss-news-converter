---
paths:
  - '**/*.rs'
  - Cargo.toml
  - Cargo.lock
---

# File and folder structure

## One concept per file
- MUST give each concept its own file inside the crate that owns it: each model/struct (the shape of an object), each error type, each distinct function group. Examples: `types/order.rs`, `types/order_item.rs`, `money.rs`, `clock.rs`.
- MUST NOT create a grab-bag `utils.rs` or `types.rs` full of unrelated items. Name files by concern. A folder's parent file holds only `mod` lines and deliberate re-exports.
- MUST keep code in the crate where it is used. Move it into `common-*` only when a second consumer needs it (`09-module-boundaries.md`).
- Use the 2018 layout: `service.rs` plus `service/`, not `service/mod.rs`.

## A big file becomes a folder
- MUST turn a file into a folder module when it passes **400 lines of non-test code** or holds more than one concept. `service.rs` becomes `service.rs` (only `mod` and re-exports) plus `service/place_order.rs`, `service/cancel_order.rs`, split by domain and function.
- `just file-size` fails any `.rs` file over the limit (tests excluded) unless it carries `// size-exempt: <reason>`. Exemptions are reviewed.

## Unit tests live in a sibling file
- MUST declare unit tests from the file under test: `#[cfg(test)] mod tests;`, with the code in `tests.rs` beside it (`service/tests.rs` for `service/`).
- MUST split a big test file the same way: `tests.rs` becomes a `tests/` folder of `<concept>_tests.rs` files. Same 400-line limit.
- Name them `tests.rs`, `*_tests.rs` or put them in a `tests/` directory so `cargo-llvm-cov` excludes them from coverage by default (`(unverified)` locally; see research).
- Integration tests go in the crate's top-level `tests/` and are not mutation-tested. Keep logic in `lib.rs`; `main.rs` stays thin.

Source: `docs/research/file-structure-and-tests.md`. https://doc.rust-lang.org/book/ch11-03-test-organization.html
