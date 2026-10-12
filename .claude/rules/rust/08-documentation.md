
# Documentation

## Rustdoc
- MUST document every public item (`missing_docs` is enabled; see `06-linting-and-formatting.md`) and write a crate-level `//!` overview for each crate.
- MUST give every public function or type an `# Examples` doctest that compiles and runs. Use `?` with a trailing `# Ok::<(), MyError>(())`, and hide setup lines with `#`.
- MUST include `# Errors` (when returning `Result`), `# Panics` (when it can panic), and `# Safety` (for `unsafe fn`) sections.
- Doctest attributes: `no_run`, `should_panic`, `compile_fail`, `ignore` (with a reason). Run with `cargo test --doc`; nextest does not run doctests.
- MUST describe behavior and contract, not implementation. Public docs of a module are the interface other layers rely on.
- CI gate: `RUSTDOCFLAGS="-D warnings" cargo doc --no-deps --all-features` (flag wording `(unverified)` as official guidance). Fix broken intra-doc links.

```rust
/// Parses a user id.
///
/// # Errors
/// Returns [`IdError::Empty`] when `s` is empty.
///
/// # Examples
/// ```
/// # use mycrate::UserId;
/// let id: UserId = "u-1".parse()?;
/// # Ok::<(), mycrate::IdError>(())
/// ```
pub fn parse(s: &str) -> Result<UserId, IdError> { /* ... */ }
```

## Comments
- SHOULD comment why, not what. Every `unsafe` block has `// SAFETY:`; every `#[allow]` and `#[mutants::skip]` has a reason.
- MUST NOT leave `todo!()` or dead commented-out code on `main`.

## README and project docs
- MUST keep a root `README.md`: purpose, prerequisites (toolchain, `just`), build, test, run, and the single command to run all gates (`just ci`). Per-crate `README.md` is optional; the crate-level `//!` doc is the source.
- MUST document the public HTTP contract in `api/openapi.yaml` (`02-openapi.md`), not in prose that can drift.
- MUST keep `docs/security.md` covering threat model, secrets handling, and the dependency policy when the project handles user data.

## ADRs
- MUST record each significant architectural decision as `docs/adr/NNNN-title.md` (status, date, context, decision, consequences, revisit-when). An example is ADR 0001 on compiler-enforced module boundaries.
- MUST NOT edit an accepted ADR's decision; supersede it with a new ADR that links back.
- MUST update docs in the same change that alters behavior or the public API. A public-API change is listed in the OpenSpec change (see `09-module-boundaries.md`), and its rustdoc and examples are updated with it.

Source: `docs/research/rust-best-practice.md` sections 1, 8; `docs/adr/0001-compiler-enforced-module-boundaries.md`. https://doc.rust-lang.org/rustdoc/write-documentation/documentation-tests.html , https://rust-lang.github.io/api-guidelines/documentation.html
