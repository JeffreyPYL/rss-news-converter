---
trigger: glob
globs: '**/*.rs, Cargo.toml, Cargo.lock'
---

# Testing

## Process
- MUST work test-first: red, then green, then refactor. A bug fix starts with a failing test that reproduces it.
- MUST write **one named test per OpenSpec scenario**, named after it (`fn scenario_expired_token_is_rejected()`). A scenario with no test is unfinished.
- Coverage and CRAP measure **production code only**, never test files: pass the test-file ignore regex below (cargo-llvm-cov's own default exclusion of `tests.rs`/`*_tests.rs`/`tests/` is `(unverified)`).
- MUST reach **>= 90% line coverage on every changed file**. `cargo llvm-cov` has no diff mode, so emit lcov and filter by `git diff --name-only <base>` (workflow `(unverified)`, inferred).
- MUST run `cargo nextest run --workspace --all-features --profile ci` plus `cargo test --workspace --doc` (nextest does not run doctests).

```sh
cargo llvm-cov nextest --workspace --lcov --output-path lcov.info --ignore-filename-regex '(/tests/|/tests\.rs$|_tests\.rs$)'
```
```toml
# .config/nextest.toml
[profile.ci]
fail-fast = false
retries = 1
```

## Names, use cases, and parameterised tests
- MUST give every test a human-readable name that states the behavior: `places_order_when_stock_is_available`, `rejects_expired_token`. No `test1`, no `works`.
- MUST put the use case in a `///` line above the test, plus the OpenSpec scenario it covers when one exists.
- MUST parameterise tests that vary only by data, with `rstest` named cases (named cases show in failure output; table-loop indexes do not):
```rust
use rstest::rstest;

/// Discount tiers from spec scenario "volume discount".
#[rstest]
#[case::no_discount_below_ten(9, 0)]
#[case::ten_percent_at_ten(10, 10)]
#[case::twenty_percent_at_fifty(50, 20)]
fn applies_volume_discount(#[case] qty: u32, #[case] pct: u32) {
    assert_eq!(discount_pct(qty), pct);
}
```
- Test files live beside the code and split like code: `10-file-structure.md`.

## Test the public interface only
- MUST exercise a module only through its `pub` API. Put behavior tests in the unit-test file beside the code (`tests.rs`, `10-file-structure.md`) and call only the module's public functions; lower layers are fakes. Never call private helpers, assert on private fields, or assert on call sequences.
- Integration tests (crate-level `tests/`) check wiring end to end. They are not used for coverage-of-changes or mutation. Rust privacy enforces the boundary; tests obey the same layer edges as production code (`09-module-boundaries.md`).
- Refactoring internals MUST NOT require rewriting tests. If it does, the tests were coupled to internals; fix the tests.

## Fakes over mocks, with contract suites
- MUST put a narrow trait at each I/O seam (storage, clock, network, filesystem). The real implementation lives in the shell.
- MUST prefer hand-written in-memory **fakes** that assert on state. Use `mockall` only when the interaction itself is the contract ("notify exactly once") or a fake costs more than it saves.
- MUST write one generic **contract suite** per trait and run it against the fake and the real implementation, so the fake stays honest. Gate the slow real run with `#[ignore]` or a feature.

```rust
fn contract<S: Store>(make: impl Fn() -> S) { /* put/get/delete behavior */ }
#[test] fn fake_honors_contract() { contract(InMemoryStore::new) }
#[test] #[ignore = "needs database"] fn real_honors_contract() { contract(PgStore::temp) }
```
- Handler tests: build `router(state)` with fakes and call it with `tower::ServiceExt::oneshot`, no socket.

## Property tests
- SHOULD use `proptest` for pure logic: parsers, round-trips, ordering, idempotence, oracle versus a naive version. Commit `proptest-regressions/`. One property kills many arithmetic and boundary mutants. Lower `PROPTEST_CASES` for mutation runs (`(unverified)`).

## Mutation testing (cargo-mutants, pinned, 27.x)
- MUST scope mutation to **unit tests** with `-- --lib`, and to changed lines per crate:
```sh
git diff origin/main...HEAD > pr.diff
cargo mutants -p <pkg> --in-diff pr.diff --baseline=skip --timeout 60 -- --lib
```
- Any missed mutant in changed lines fails the change. Test-only diffs yield zero mutants, which is correct. Mutation testing runs on **unit tests only**: always pass `-- --lib`, never mutate against integration tests.
- MUST **ratchet**: the nightly full, sharded run (`--shard k/n`, identical args per shard) records the missed count as an artifact; it MUST NOT increase. cargo-mutants has no built-in ratchet; this is a recipe.
- `#[mutants::skip]` needs a regular dependency on the `mutants` crate (>= 0.0.3). A reason is NOT an attribute parameter: put it in a trailing comment, and it is mandatory.
```rust
#[mutants::skip] // equivalent mutant: result is only used for logging
fn describe(&self) -> String { /* ... */ }
```
- Exclude files and categories whose mutants are endless and meaningless **in config**, not by attribute: config, constants, `main.rs`, generated code, Debug/Display impls, logging. `-e` globs verified with cargo-mutants 27.1.0 (a `tests.rs` declared with `#[cfg(test)] mod tests;` is not mutated either).
```toml
# .cargo/mutants.toml  (keys other than exclude_globs/exclude_re: unverified)
exclude_globs = ["**/config*.rs", "**/config/**", "**/consts*.rs", "**/main.rs", "**/generated/**"]
exclude_re = ["impl Debug", "impl Display", "tracing::"]
test_tool = "nextest"                 # nextest + --lib composition (unverified); benchmark first
additional_cargo_test_args = ["--lib"]
```
- Use per-function `#[mutants::skip]` (with its comment) only for exceptions the config cannot express.
- When using `--baseline=skip` ALWAYS pass `--timeout` (default 300s otherwise). `--list` previews the selected mutants.
- Equivalent-mutant guidance has no primary source (`(unverified)`): skip with a commented attribute, add `exclude_re`, or refactor so the mutation changes behavior.

## Behavior lock
- Before refactoring untested code, MUST write characterization tests that pin current observable behavior through the public interface, confirm cargo-mutants shows no missed mutants for the code, and only then change it.

Source: `docs/research/testability-and-mutation.md` sections 1, 4, 5, 7; `docs/research/rust-best-practice.md` section 8. https://mutants.rs/in-diff.html , https://mutants.rs/attrs.html , https://mutants.rs/cargo-args.html , https://mutants.rs/shards.html , https://nexte.st/docs/running/ , https://github.com/taiki-e/cargo-llvm-cov , https://proptest-rs.github.io/proptest/intro.html
