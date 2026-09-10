## Purpose

Defines how a digest run gets started — on demand or on a schedule — always invoking the same underlying pipeline.

## ADDED Requirements

### Requirement: On-demand trigger
A user-invoked Claude Code command SHALL run the full pipeline, from ingestion through delivery, immediately.

#### Scenario: Invoking the command produces a delivered digest
- **WHEN** the user invokes the on-demand command
- **THEN** a digest is built and delivered to the configured targets before the command completes

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
