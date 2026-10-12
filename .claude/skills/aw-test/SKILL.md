---
name: aw-test
description: Multi-phase test and verification stage for Rust changes (unit, doc, functional, and integration tests, line coverage, mutation testing, CRAP complexity). Emits test-report.json with metrics and pointers to raw reports. Supports cost-optimized execution (cheap model runner with bounce-back to aw-implement on failure, or in-session interactive subagent fix loop). Use when the user says "run tests", "aw-test", "verify tests", or a handoff names aw-test as Next.
---

# aw-test

Testing stage of **propose -> aw-implement -> aw-test -> aw-ship-review -> aw-pr**. Runs full dynamic verification and produces `openspec/changes/<id>/test-report.json` with summary metrics and pointers to raw reports, so `aw-ship-review` only reviews artifacts rather than re-running heavy test suites.

## Quick start

```text
/aw-test add-rate-limiter
```

## Handoff

Follow `/aw-continue`. Start: read `openspec/changes/<id>/aw-handoff.md` when it exists. End: write the next handoff.

## Execution modes (Ask on start)

Every time `aw-test` is triggered, prompt the user for execution mode:

1. **Cost-First (Stage Bounce-Back - Default)**:
   - Run tests using a low-cost model (`model: flash` on Antigravity, `model: haiku` on Claude Code).
   - If ANY test fails or coverage/mutation thresholds are unmet, immediately stop, log the failure details into `aw-handoff.md`, and route back to `/aw-implement` (capable model) to fix.
   - Recommended when cost is prioritized over speed.

2. **Speed-First (In-Session Subagent Fix - Option)**:
   - Run test commands via a low-cost subagent (`flash` / `haiku`).
   - If failures occur, the parent session (capable model) diagnoses and applies fixes interactively, re-dispatching the subagent until green.

3. **Deterministic Orchestrator Mode (Conductor / Headless)**:
   - Run tests directly via project test runner (`just test` or `cargo test`).
   - Handled non-interactively by orchestration engines; exit codes and failure logs are captured directly into `aw-handoff.md` via `scripts/aw-handoff.py`.

## 3-Phase Fail-Fast Pipeline

Tests execute in three strict tiers. If any tier fails, execution halts immediately to avoid wasting machine cycles and tokens on downstream phases (especially mutation testing). Details: [REFERENCE.md](REFERENCE.md).

### Phase 1: Functional & Doc Tests (Unit, Integration, Functional)
- `cargo nextest run --workspace --all-targets --all-features`
- `cargo test --workspace --doc`
- *Failure*: Halt immediately. Report failing tests.

### Phase 2: Line Coverage (≥90% on changed files)
- Run `cargo llvm-cov` on changed files (excluding test code).
- Output raw coverage files to `target/llvm-cov/lcov.info` and HTML to `target/llvm-cov/html/index.html`.
- Compute line coverage on each changed production `.rs` file.
- *Failure*: If any changed file has < 90% line coverage, halt immediately and report uncovered lines.

### Phase 3: Deep Verification (Mutants & CRAP)
- Run only after Phase 1 and Phase 2 are 100% green.
- Mutation testing on the diff: `cargo mutants --in-diff pr.diff -p <crate> --baseline=skip --timeout 60 -- --lib`. Zero missed mutants allowed on changed lines.
- CRAP complexity check: `cargo crap --lcov target/llvm-cov/lcov.info --workspace --fail-regression`.
- *Failure*: Halt on missed mutants or CRAP regression.

## Test Artifact: `test-report.json`

On completion (or failure), write `openspec/changes/<id>/test-report.json`:
- Records summary metrics: timestamp, git commit, pass/fail per phase, minimum file coverage %, missed mutants, CRAP status.
- Records pointers (file paths) to raw reports (e.g. `target/llvm-cov/lcov.info` and `target/llvm-cov/html/index.html`) rather than embedding raw blobs into the OpenSpec directory.

## Suggested next step

Write `openspec/changes/<id>/aw-handoff.md`:
- If all phases pass: **Next:** `/aw-ship-review`, **New session?** yes.
- If failed (Cost-First mode): **Next:** `/aw-implement`, **New session?** yes (route back with failure diagnostic).
- If failed (Speed-First mode): continue in current session to fix, or route to `/aw-implement`.

## Boundaries

- Owns dynamic test execution; does not run static linting (`clippy`, `fmt`) or architecture reviews (owned by `aw-ship-review`).
- Never runs mutation testing when unit or integration tests are red.
- Raw coverage data remains in `target/`; only summary metrics and pointers live in `openspec/changes/<id>/test-report.json`.
