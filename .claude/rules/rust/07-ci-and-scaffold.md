---
description: CI pipeline, justfile, and project scaffold for Rust repos. Use when creating or editing GitHub Actions workflows, the justfile, deny.toml, rust-toolchain.toml, or bootstrapping a new Rust project.
paths:
  - '**/*.rs'
  - Cargo.toml
  - Cargo.lock
---

# CI and project scaffold

## Required files
- MUST have in the repo root: `Cargo.toml` (with `[workspace.lints]`, `[workspace.dependencies]`), `Cargo.lock` (binaries), `rust-toolchain.toml`, `clippy.toml`, `rustfmt.toml` (minimal or absent), `deny.toml`, `.cargo/mutants.toml`, `.config/nextest.toml`, `justfile`, `README.md`, `docs/adr/`, and `.github/workflows/ci.yml`.
- Layout: flat `crates/` with one crate per layer per context plus a `<ctx>` facade, `common-*` crates, and one `app` crate that composes them (`09-module-boundaries.md`, ADR 0002). Add `.claude/worktrees/` to `.gitignore` if using Claude worktrees.
- `rust-toolchain.toml`:
```toml
[toolchain]
channel = "1.95.0"          # exact stable; bump deliberately
profile = "minimal"
components = ["rustfmt", "clippy"]
```

## justfile: one entry point, CI runs the same recipes
- MUST define `fmt`, `lint`, `test`, `cov`, `mutants`, `crap`, `file-size`, `deny`, `audit`, `api`, `doc`, and `ci` (depends on the fast ones). The bootstrap template (`aw-bootstrap-rust-project/templates/justfile`) is the full version. CI runs `just ci`, so local and CI results match. (No authoritative `just` convention exists; this shape is a suggestion, `(unverified)`.)
```make
fmt:    cargo fmt --all --check
lint:   cargo clippy --workspace --all-targets --all-features -- -D warnings
test:   cargo nextest run --workspace --all-features --profile ci && cargo test --workspace --doc
cov:    cargo llvm-cov nextest --workspace --lcov --output-path lcov.info --ignore-filename-regex '(/tests/|/tests\.rs$|_tests\.rs$)'
file-size: (see template: fails on .rs over 400 non-test lines)
deny:   cargo deny check
audit:  cargo audit
doc:    RUSTDOCFLAGS="-D warnings" cargo doc --no-deps --all-features
ci:     fmt lint test file-size deny audit doc
```

## GitHub Actions
- MUST use `dtolnay/rust-toolchain` (inputs `toolchain`, `components`, `targets`) then `Swatinem/rust-cache@v2` after it (`save-if: ${{ github.ref == 'refs/heads/main' }}`), and `EmbarkStudios/cargo-deny-action@v2`. Pin actions by SHA where practical.
- MUST run these jobs on every PR: fmt, clippy, test (nextest plus doctests), msrv (`cargo +<rust-version> build --locked`: the `+` is required, because `rust-toolchain.toml` otherwise overrides the toolchain the action installed), deny, coverage, docs, mutants on the diff, and public-API diff.
- MUST run `cargo audit` and cargo-deny advisories on a schedule, plus the full sharded mutation run nightly (report only, ratcheted).
- MUST install CI tools with `--locked` and pinned versions (`cargo install cargo-leptos --locked`, `cargo-crap` 0.6.1, `cargo-mutants` 27.x).
- `RUSTFLAGS: -D warnings` only on lint jobs (convention `(unverified)`); set `CARGO_TERM_COLOR: always`.
- Mutation job: `cargo mutants -p <pkg> --in-diff pr.diff --baseline=skip --timeout 60 -- --lib` per changed package (find packages from `cargo metadata --no-deps`). Use `--in-place` in CI.
- Public API job: `cargo public-api` snapshot test (needs a nightly toolchain for rustdoc JSON) and `cargo semver-checks --baseline-rev origin/main -p <pkg>` for crates with an external API contract. `--deny` on `cargo public-api` is `(unverified)`.
- Leptos projects add `cargo leptos build --release` and optionally `cargo leptos end-to-end` (Playwright).
- API contract: lint `api/openapi.yaml` (`02-openapi.md`); if generated, fail on `git diff --exit-code`.

```yaml
jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with: { components: "rustfmt, clippy" }
      - uses: Swatinem/rust-cache@v2
      - run: just ci
```
- PR titles SHOULD be imperative and concise. Commits MUST NOT contain secrets or generated artifacts other than the committed spec and lockfile.

Source: `docs/research/rust-best-practice.md` sections 5-8, 11; `docs/research/testability-and-mutation.md` sections 1-3, recommended gates. https://github.com/dtolnay/rust-toolchain , https://github.com/Swatinem/rust-cache , https://github.com/EmbarkStudios/cargo-deny-action , https://mutants.rs/ci.html , https://just.systems/man/en/
