# aw-test: commands, phasing, and report schema

Sources and caveats: `docs/research/testability-and-mutation.md`, `docs/research/rust-best-practice.md`.

## 3-Phase Execution Commands

### Setup diff and changed crates

```bash
base=$(git merge-base origin/main HEAD)
git diff "$base"...HEAD > pr.diff
files=$(git diff --name-only "$base"...HEAD -- '*.rs')

# Map changed files to workspace crates:
cargo metadata --no-deps --format-version 1 \
  | jq -r '.packages[] | "\(.name) \(.manifest_path | rtrimstr("/Cargo.toml"))"' > /tmp/crates.txt
```

### Phase 1: Functional & Doc Tests

```bash
# Unit, integration, and functional tests across all targets and features:
cargo nextest run --workspace --all-targets --all-features

# Doctests (nextest skips doctests):
cargo test --workspace --doc
```

*Fail condition*: Any test failure halts execution immediately.

---

### Phase 2: Line Coverage (≥ 90% on changed files)

```bash
mkdir -p target/llvm-cov/html
cargo llvm-cov nextest --workspace --all-features \
  --lcov --output-path target/llvm-cov/lcov.info \
  --html --output-dir target/llvm-cov/html \
  --ignore-filename-regex '(/tests/|/tests\.rs$|_tests\.rs$)'

# Extract coverage for changed non-test files:
awk -F: '
  /^SF:/{f=$2}
  /^LF:/{lf[f]=$2}
  /^LH:/{lh[f]=$2}
  END {
    for (f in lf) {
      if (lf[f] > 0) printf "%s %.1f\n", f, 100 * lh[f] / lf[f]
    }
  }
' target/llvm-cov/lcov.info > /tmp/coverage.txt
```

*Fail condition*: If any changed production `.rs` file in `$files` has line coverage < 90.0%, halt and report missing line numbers.

---

### Phase 3: Deep Verification (Mutants & CRAP)

Run only after Phase 1 and Phase 2 are completely green:

```bash
# 1. Mutation testing scoped to the diff (per changed crate, unit tests only):
for crate in $(cat /tmp/changed_crates.txt); do
  cargo mutants --in-diff pr.diff -p "$crate" --baseline=skip --timeout 60 -- --lib || exit 1
done

# 2. CRAP complexity check (against regression baseline):
cargo crap --lcov target/llvm-cov/lcov.info --workspace --fail-regression
```

*Fail condition*: Any missed mutant on changed lines or any CRAP score regression fails.

---

## Artifact Schema: `test-report.json`

Written to `openspec/changes/<change-id>/test-report.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "change_id": "add-rate-limiter",
  "timestamp": "2026-10-04T22:00:00Z",
  "git_commit": "e3a1b0c9...",
  "git_base": "f12c8b0a...",
  "overall_status": "pass",
  "phases": {
    "functional": {
      "status": "pass",
      "tests_passed": 42,
      "tests_failed": 0
    },
    "coverage": {
      "status": "pass",
      "threshold_percent": 90.0,
      "min_file_percent": 94.2,
      "files_evaluated": [
        { "path": "crates/rate-limiter/src/lib.rs", "line_coverage_pct": 94.2 }
      ],
      "lcov_pointer": "target/llvm-cov/lcov.info",
      "html_pointer": "target/llvm-cov/html/index.html"
    },
    "mutants": {
      "status": "pass",
      "missed_mutants": 0,
      "caught_mutants": 12
    },
    "crap": {
      "status": "pass",
      "max_crap_score": 12.0
    }
  }
}
```
