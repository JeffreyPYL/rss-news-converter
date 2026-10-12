---
name: aw-bootstrap-rust-project
description: Bootstraps a Rust workspace with lint, format, toolchain, dependency-policy, mutation-testing, justfile, and GitHub Actions CI templates matching the aw- gates. Use when the user says "bootstrap a Rust project", "set up a Rust workspace", "add CI and lints to this Rust repo", or starts a new Rust service or library.
---

# aw-bootstrap-rust-project

Copies the templates in `templates/` into a Rust repo and tunes them. The files encode the gates that `/aw-ship-review` runs, so keep them in sync.

## Templates

| Template | Destination |
|---|---|
| `Cargo.toml` | repo root (`[workspace]`, `[workspace.lints]`) |
| `rust-toolchain.toml` | repo root |
| `rustfmt.toml` | repo root |
| `clippy.toml` | repo root |
| `deny.toml` | repo root |
| `justfile` | repo root |
| `mutants.toml` | `.cargo/mutants.toml` |
| `ci.yml` | `.github/workflows/ci.yml` |

## Steps

1. Inspect the target: existing `Cargo.toml`, workspace members, toolchain, CI. Never overwrite a file without showing the diff and getting confirm; merge instead.
2. Ask only what the templates cannot default: first bounded-context crate name(s), MSRV, license, published or not.
3. Copy templates to their destinations. Merge `[workspace.lints]` into an existing workspace; each member gets `[lints] workspace = true` and `edition.workspace = true`.
4. Create flat `crates/` entries per bounded context: the `<ctx>` facade plus only the layer crates (`<ctx>-service`, `<ctx>-crud`, interface kinds) the first change needs, a thin `app` crate, and `common-*` crates only for concerns with a real second consumer (`rules/09-module-boundaries.md`, ADR 0002). Add each crate's `deny.toml` `wrappers` entry in the same step. No empty layers, no `utils` crate.
5. Tune: MSRV in `Cargo.toml`, `ci.yml` (`dtolnay/rust-toolchain@<MSRV>` and `cargo +<MSRV>` in the msrv job), and `rust-toolchain.toml` channel (keep it at or above MSRV). Add licenses to `deny.toml` until `cargo deny check` passes with `ignore = []`.
6. Install tools (pin the young one): `cargo install cargo-nextest cargo-llvm-cov cargo-mutants cargo-deny cargo-audit just --locked`, `cargo install cargo-crap --locked --version 0.6.1`, `cargo +stable install cargo-public-api cargo-semver-checks --locked`. `cargo-public-api` also needs a nightly toolchain for rustdoc JSON.
7. Binary-only crates: relax `missing_docs` in that crate's `[lints]` section instead of editing the workspace table.
8. Verify: `just ci` passes on the empty skeleton. Fix template problems here, not by loosening lints.

## Notes

- Versions and lint names come from `docs/research/rust-best-practice.md`; restriction lint names and the `.cargo/mutants.toml` keys as a whole are (unverified) until `just ci` and `cargo mutants --list` run clean.
- `cargo crap --fail-regression` needs a saved baseline; how it is stored is (unverified). Read `cargo crap --help` and wire it into the `crap` recipe.
- CI runs mutants on the diff only. A scheduled full run is optional; add it only when the team wants the trend.
- Pin actions to commit SHAs before the first merge (supply chain).

## Boundaries

- Do not scaffold application code beyond the minimum skeleton.
- Web stack choice (Leptos + axum or other) is a separate decision: `rules/03-web-architecture.md`.
- Do not disable a lint or gate to make the skeleton pass.
