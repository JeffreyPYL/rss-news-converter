# aw-ship-review: commands, formats, rubrics

Sources and caveats: `docs/research/testability-and-mutation.md`, `docs/research/rust-best-practice.md`. Anything marked (unverified) was not confirmed against a primary source; check once in the consuming repo.

## Present format

```
## aw-ship-review pass N: <change>  -  READY | NOT READY

| Axis / gate        | Result                          |
|--------------------|---------------------------------|
| OpenSpec           | X/Y tasks, N reqs, M gaps       |
| Over-engineering   | net -K lines possible           |
| Standards / Spec   | S standards, P spec findings    |
| Bugs               | N (worst: sev)                  |
| Security           | N (worst: sev)                  |
| Boundaries         | violations (incl. deny wrappers)|
| File size          | pass / fail                     |
| fmt / clippy       | pass / fail                     |
| nextest + doctests | pass / fail (from test-report.json) |
| Coverage (changed) | min file %, pass / fail (from test-report.json) |
| Mutants (diff)     | missed N, pass / fail (from test-report.json) |
| deny / audit       | pass / fail                     |
| CRAP               | pass / fail (from test-report.json) |
| Public API         | matches change? pass / fail     |
```

Blockers: unchecked tasks, unimplemented requirements, any failed gate, high/critical bug or security finding, `rules/` MUST violation, ADR or OpenSpec contradiction. Warnings and suggestions: spec drift, ponytail cuts, style. Keep findings under their own axis; never merge or re-rank across axes.

## Axes

1. **OpenSpec**: completeness (tasks, requirements), correctness (each `#### Scenario:` has a named test), coherence (follows `design.md`). Stale checkbox for finished work: fix it, do not flag it.
2. **Over-engineering**: one line per finding, tagged `delete/stdlib/native/yagni/shrink`, ending `net: -N lines possible`. All suggestions, never blockers. Do not flag the required self-check test.
3. **Standards + Spec**: `/code-review` with fixed point = the base, spec = the change's `proposal.md` + `specs/**`, standards = every `rules/*.md`. Rule MUST violation is a blocker; smells and drift are warnings. Keep the two reports separate.
4. **Bugs**: one fresh subagent, diff only. High/critical blocks.
5. **Security**: cross-check `rules/01-security.md`: new `unsafe` without `SAFETY:`, secrets in code or logs, unvalidated input at trust boundaries, internal error text in responses, new dependencies.
6. **Boundaries and structure**: every new crate has a `deny.toml` `[bans]` entry whose `wrappers` list its allowed dependents (`rules/09-module-boundaries.md`, ADR 0002); no upward or layer-skipping `Cargo.toml` edge; every new file has a recorded layer; visibility is the narrowest that compiles; no `pub` item that `unreachable_pub` would flag; one concept per file, unit tests in sibling `tests.rs` (`rules/10-file-structure.md`); tests have readable names, a `///` use case, and `rstest` cases where only data varies.

## Gate commands

```bash
base=$(git merge-base origin/main HEAD)
git diff "$base"...HEAD > pr.diff
files=$(git diff --name-only "$base"...HEAD -- '*.rs')
```

Changed crates:

```bash
cargo metadata --no-deps --format-version 1 \
  | jq -r '.packages[] | "\(.name) \(.manifest_path | rtrimstr("/Cargo.toml"))"' > /tmp/crates.txt
# for each changed file, pick the package whose directory is the longest prefix of the file path
```

Baseline gates:

```bash
cargo fmt --all --check
cargo clippy --workspace --all-targets --all-features -- -D warnings
cargo nextest run --workspace --all-features
cargo test --workspace --doc          # nextest skips doctests
RUSTDOCFLAGS="-D warnings" cargo doc --no-deps --all-features
cargo deny check            # includes [bans] wrappers = crate visibility
cargo audit
just file-size
```

Coverage (90% line coverage per changed file; llvm-cov has no diff mode):

```bash
cargo llvm-cov nextest --workspace --all-features --lcov --output-path lcov.info --ignore-filename-regex '(/tests/|/tests\.rs$|_tests\.rs$)'
# per changed file: LH/LF from the lcov SF block
awk -F: '/^SF:/{f=$2} /^LF:/{lf[f]=$2} /^LH:/{lh[f]=$2} END{for(f in lf) if(lf[f]>0) printf "%s %.1f\n", f, 100*lh[f]/lf[f]}' lcov.info
```

Compare only non-test files in `$files` (coverage and CRAP are production code only); paths in lcov are absolute (unverified). A changed file with `LF` 0 has nothing to cover.

Mutants, behavior lock (per changed crate, unit tests only):

```bash
cargo mutants --in-diff pr.diff -p <crate> --baseline=skip --timeout 60 -- --lib
```

- Run only after tests are green (`--baseline=skip` assumes it).
- Any missed mutant on changed lines fails. A diff touching only tests yields zero mutants; that is correct.
- Fix root cause: a missing assertion, a missing seam, a branch that should not exist (make the illegal state unrepresentable). Do not whack the single mutant.
- `#[mutants::skip]` needs a trailing comment with the reason. Files (config, consts, `main.rs`, generated) belong in `.cargo/mutants.toml` `exclude_globs`; categories (Debug, Display, logging) in `exclude_re`.
- Unit tests only: always `-- --lib`. Integration tests in `tests/` are never used for mutation (`rules/05-testing.md`).

CRAP (pinned version only; young tool):

```bash
cargo crap --lcov lcov.info --workspace --fail-regression
```

How the regression baseline is saved is (unverified): read `cargo crap --help` and record it in the repo. Changed-file filtering is not a flag; use `-p <crate>` or filter `--format json` by `$files`. Cut CRAP by splitting functions and pushing logic into pure functions and types, not by adding tests alone.

Public API (gate = diff against the OpenSpec change):

```bash
cargo public-api diff origin/main..HEAD -p <crate>
```

Needs nightly for rustdoc JSON (`cargo +stable install cargo-public-api --locked`); the exact ref syntax is (unverified), check `--help`. Compare the output with the change's `## Public API` line by line. Missing from the list: the code leaked an item, make it narrower. Missing from the code: the spec is stale or work is unfinished. Either way it is a blocker.

Published or depended-on crates also run:

```bash
cargo semver-checks --baseline-rev origin/main -p <crate>   # exit 100 = violation
```

## Docs gate

For anything touched, validate and update: README and `rules/08-documentation.md` items, rustdoc on public items (`# Errors`, `# Panics`, `# Safety`, doctest examples), ADRs, OpenSpec `tasks.md`. Docs are auto-fixed here; report what changed.

## Fix loop notes

- Never start fixing before the user has seen the whole picture.
- Grill every finding, even mechanical ones, to confirm seam and domain term.
- Fixes stay inside three fences: the OpenSpec spec, ADRs, and `rules/`.
- New code can create new findings; the loop ends only on a clean fresh pass.

## Ship and CI monitor

After `/aw-pr` pushes: `gh pr checks --watch` (cap the wait; record pending in the handoff). Red: write failing check names to `aw-handoff.md`, Next `/aw-address-pr-issues` in a new session. Green: report; do not merge unless asked.
