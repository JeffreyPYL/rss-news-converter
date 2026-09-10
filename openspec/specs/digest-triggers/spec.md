# Digest Triggers Specification

## Purpose

Defines how a digest run gets started — on demand or on a schedule — always invoking the same underlying pipeline.

## Requirements

### Requirement: On-demand trigger
A user-invoked Claude Code command SHALL run the full pipeline, from ingestion through delivery, immediately. The command SHALL accept an optional `--since <duration>` argument, where `<duration>` is a relative duration (e.g. `3d`, `48h`), that overrides the run's lookback start for that invocation only; when omitted, the lookback start SHALL be derived from the persisted run state exactly as before.

#### Scenario: Invoking the command produces a delivered digest
- **WHEN** the user invokes the on-demand command
- **THEN** a digest is built and delivered to the configured targets before the command completes

#### Scenario: A since override replaces the persisted lookback for that run
- **WHEN** the user invokes the on-demand command with `--since 3d`
- **THEN** only articles published within the last 3 days of the run's start are considered, regardless of the persisted last-success timestamp

#### Scenario: Omitting since preserves existing lookback behavior
- **WHEN** the user invokes the on-demand command without `--since`
- **THEN** the lookback start comes from the persisted run state, exactly as before this change

#### Scenario: An invalid since value is rejected before the pipeline runs
- **WHEN** the user invokes the on-demand command with a `--since` value that does not match the supported duration format
- **THEN** the command reports an error and exits without fetching, extracting, or delivering anything

#### Scenario: A since-overridden run still records success normally
- **WHEN** a run invoked with `--since` completes successfully
- **THEN** the persisted run state is updated to this run's completion time, exactly as an unoverridden successful run would update it

### Requirement: Scheduled trigger
A daily run at approximately 7am SHALL invoke the same pipeline unattended, with no user interaction required.

#### Scenario: The scheduled run produces a delivered digest without interaction
- **WHEN** the daily ~7am schedule fires
- **THEN** a digest is built and delivered to the configured targets without any user action

### Requirement: Shared pipeline across triggers
On-demand and scheduled triggers SHALL invoke identical pipeline logic; no stage's behavior SHALL differ between the two trigger paths, except for how synthesis text is generated (see the `digest-synthesis` capability).

#### Scenario: Equivalent runs produce equivalent output
- **WHEN** an on-demand run and a scheduled run execute against the same feed state and configuration
- **THEN** they produce equivalent digests, aside from any difference in generated synthesis text
