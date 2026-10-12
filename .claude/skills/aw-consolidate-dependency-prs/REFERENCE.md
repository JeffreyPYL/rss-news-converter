# Consolidation reference

## Groups and local verification

| Group | Files | Required checks |
|---|---|---|
| Cargo | `Cargo.toml`, `Cargo.lock` | `cargo build --workspace --all-features --locked`, `cargo nextest run --workspace`, `cargo clippy --workspace --all-targets -- -D warnings`, `cargo deny check`, `cargo audit` |
| GitHub Actions | `.github/workflows/**` | workflow lint if the repo has one, plus CI validation |
| Other evidenced ecosystem | its manifests | its build and test commands |

Add a group only when files and verification seam differ materially. Do not merge ecosystems just to reduce PR count.

## Version resolution

1. Read every bot PR body and diff.
2. Map direct and transitive updates by manifest and lockfile.
3. Drop updates superseded by a newer safe version.
4. Apply the union from the default branch with Cargo.
5. Keep intentional constraints (`=` pins, documented deferrals).
6. A failing major update: pin it back in the main group and remediate separately. Check `rust-version` (MSRV) still holds.
7. Changes that alter the public API of a published crate: run `cargo semver-checks`.

## PR protocol

- Follow the repo's PR title convention.
- Say which bot PRs the replacement covers and which were excluded.
- Include the test plan and actual local results.
- Push with upstream tracking; no force-push.
- Wait for local checks, not remote CI, before closing covered PRs.
- Close comment: `Superseded by <replacement URL>, which contains this update and passed <checks>.`

## Remediation follow-up

1. Reproduce the failure in its own worktree.
2. Classify: API break, dependency conflict, changed tool behavior, project defect.
3. Smallest migration that preserves behavior.
4. Add or update tests at the highest existing seam.
5. Run the group's checks.
6. Open a separate PR; close the original bot PR only if fully covered.

## Guardrail evidence

Open a guardrail PR only when inventory shows a recurrence source:

- a workspace directory or `Cargo.toml` missing from `.github/dependabot.yml` or the Renovate config;
- security updates not covered by a group;
- two bots updating the same lockfile.

Validate config against its schema. Prefer grouped updates in the bot config over ad hoc routing.

## Safety

- Re-fetch PR state immediately before closing; stale inventory is not authority.
- Abort closure if a bot PR gained commits or files not in the replacement.
