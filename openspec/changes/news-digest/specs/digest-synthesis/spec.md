## Purpose

Optionally adds a short cross-outlet synthesis to a multi-outlet story group, without ever removing or replacing the original full articles it is built from.

## ADDED Requirements

### Requirement: Synthesis is an explicit toggle
Synthesis SHALL be an explicit on/off setting for a given run. When off, the digest SHALL contain only grouped original articles with no generated text.

#### Scenario: A synthesis-off run contains no generated commentary
- **WHEN** a run executes with synthesis disabled
- **THEN** every story entry in the digest contains only original extracted article content, with no generated synthesis text

### Requirement: Synthesis never replaces originals
When synthesis is enabled, the generated synthesis SHALL be presented alongside, and never in place of, the original full articles it summarizes.

#### Scenario: A synthesized story group still shows every original article
- **WHEN** synthesis is enabled and a story group has articles from two outlets
- **THEN** the digest shows the generated synthesis plus both original full articles underneath it

### Requirement: Synthesis works on both trigger paths without a billed API key
Synthesis SHALL be produced the same way (a Claude Code agent turn) whether the run is triggered on-demand or on the daily schedule, and SHALL NOT require a separately billed LLM API key.

#### Scenario: A scheduled run with synthesis on produces a synthesis blurb
- **WHEN** the scheduled daily run executes with synthesis enabled
- **THEN** the delivered digest includes generated synthesis text for its multi-outlet story groups, produced without any API key configuration
