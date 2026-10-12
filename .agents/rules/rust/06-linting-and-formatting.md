---
trigger: glob
globs: '**/*.rs, Cargo.toml, Cargo.lock'
---

# Linting and formatting

## Lints live in Cargo.toml
- MUST configure lints in the `[workspace.lints]` table and opt each member in with `[lints] workspace = true`. No crate-level `#![warn(..)]` blocks. Use `priority` so specific lints override groups.
- MUST NOT enable the clippy `restriction` group wholesale; cherry-pick.
- MUST fix `correctness`/`suspicious` findings instead of adding `#[allow]`. Any `#[allow]` needs a trailing reason comment (or `#[expect(.., reason = "..")]`).

```toml
[workspace.lints.rust]
unsafe_code = "forbid"
missing_docs = "warn"
unreachable_pub = "warn"            # pub item not reachable from outside the crate
missing_debug_implementations = "warn"

[workspace.lints.clippy]
all = { level = "warn", priority = -1 }
pedantic = { level = "warn", priority = -1 }
unwrap_used = "warn"
expect_used = "warn"
panic = "warn"
dbg_macro = "warn"
todo = "warn"
undocumented_unsafe_blocks = "warn"
cognitive_complexity = "warn"       # activates the clippy.toml threshold
too_many_lines = "warn"
module_name_repetitions = "allow"
```
```toml
# clippy.toml  (msrv defaults to rust-version; do not duplicate)
cognitive-complexity-threshold = 15   # default 25
too-many-lines-threshold = 80         # default 100
allow-unwrap-in-tests = true
allow-expect-in-tests = true
```
These two files were checked on cargo/clippy 1.95: `unreachable_pub`, `missing_docs`, `unwrap_used` and the thresholds are accepted and fire. `unreachable_pub` and `missing_docs` are allow-by-default rustc lints, so they only work once enabled here.

- MUST keep every public item documented (`missing_docs`) and reachable only deliberately (`unreachable_pub`): use `pub(crate)` / `pub(super)` by default (see `09-module-boundaries.md`).
- CI command: `cargo clippy --workspace --all-targets --all-features -- -D warnings`.

## Format
- MUST run `cargo fmt --all --check` in CI. Edition comes from `Cargo.toml` (`edition = "2024"`); keep `rustfmt.toml` minimal or absent.
- MUST NOT use unstable rustfmt options (`imports_granularity`, `group_imports`, `format_code_in_doc_comments`) on the stable toolchain.

## Edition, MSRV, toolchain
- MUST use edition 2024 and set `rust-version` (bare, e.g. `"1.85"`; edition 2024 needs >= 1.85). Document the MSRV policy; changing MSRV is a minor SemVer incompatibility. CI builds on exactly the `rust-version` toolchain.
- MUST pin an exact stable in `rust-toolchain.toml` with `components = ["rustfmt", "clippy"]`; bump it deliberately. Use `cargo +nightly` explicitly for miri and rustdoc-JSON tools.

## Design for low complexity (functional core, imperative shell)
- MUST keep logic in pure functions over values and push I/O (database, clock, network, filesystem) to a thin shell behind one narrow trait per boundary. Pure code needs no fakes, tests fast, and kills mutants cheaply.
- MUST make illegal states unrepresentable (enums, newtypes, validated constructors) so invalid branches and error arms do not exist. Fewer branches means lower complexity and fewer mutants. (Heuristic, not primary-sourced.)
- SHOULD split a function before it nears the thresholds. A flat `match` over an enum is fine.

## CRAP gate (cargo-crap)
`CRAP = comp^2 * (1 - cov)^3 + comp`. Cover the pure core and the `(1-cov)^3` term vanishes.
- MUST pin the tool: `cargo install cargo-crap --locked --version 0.6.1`. It is under 6 months old with frequent releases; flag churn is possible.
- CRAP scores **production code only**. Test files are excluded from the lcov input, so test helpers never count.
- MUST gate on regression, not absolute score:
```sh
cargo llvm-cov --lcov --output-path lcov.info --ignore-filename-regex '(/tests/|/tests\.rs$|_tests\.rs$)'   # production code only
cargo crap --lcov lcov.info -p <pkg> --fail-regression
```
- How `--fail-regression` stores its baseline, the JSON schema, and any changed-files option are `(unverified)` (README silent). Scope with `-p`. `--threshold` defaults to 30. Do not use `crap4rs` (too immature to gate).

Source: `docs/research/rust-best-practice.md` sections 1, 3-6; `docs/research/testability-and-mutation.md` sections 2, 6. https://doc.rust-lang.org/clippy/lints.html , https://doc.rust-lang.org/clippy/lint_configuration.html , https://doc.rust-lang.org/cargo/reference/manifest.html#the-lints-section , https://doc.rust-lang.org/rustc/lints/listing/allowed-by-default.html , https://github.com/minikin/cargo-crap
