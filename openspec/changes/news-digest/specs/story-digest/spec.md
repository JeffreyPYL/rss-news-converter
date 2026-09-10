## Purpose

Groups the same story's coverage across outlets into one entry, assigns each story to its single most specific topic, and bounds how much a single run's digest can contain.

## ADDED Requirements

### Requirement: Cross-outlet story grouping
Articles covering the same underlying story from different configured outlets SHALL be grouped into a single story entry, retaining each outlet's full extracted article within that entry rather than discarding all but one.

#### Scenario: Same story from two outlets groups into one entry
- **WHEN** BBC and CBC both publish articles about the same underlying story in the same run
- **THEN** the digest contains one story entry for that story, with both outlets' full articles attached to it

#### Scenario: An unrelated story from one outlet stays its own entry
- **WHEN** an outlet publishes a story no other configured outlet covers in that run
- **THEN** the digest contains a separate story entry with only that outlet's article

### Requirement: Topic assignment is single and most-specific
A story matching more than one configured topic SHALL appear exactly once in the digest, under its most specific matching topic, ranked narrow to broad: Ottawa, then Canada, then Hong Kong, then China, then Tech, then Global.

#### Scenario: A Hong Kong story is not duplicated into China or Global
- **WHEN** a story matches Hong Kong, China, and Global topics
- **THEN** the digest shows that story only once, under Hong Kong

### Requirement: Per-topic story cap
Each topic SHALL include at most 10 stories per run, except stories from an outlet configured with its own cap override, which SHALL be limited to that outlet's own cap independently rather than competing for the shared limit. When more than a cap's worth of qualifying stories exist, the most recent SHALL be selected; the topic's final story order SHALL remain most-recent-first across both the shared-cap and outlet-capped stories combined.

#### Scenario: An overflow topic is trimmed to its most recent stories
- **WHEN** a topic has 15 qualifying stories in a run, none from an outlet with its own cap override
- **THEN** the digest includes only the 10 most recently published of those stories for that topic

#### Scenario: An outlet with its own cap is exempt from the shared cap
- **WHEN** a topic has more than 10 qualifying stories from outlets sharing the default cap, plus more than 10 qualifying stories from an outlet configured with its own cap of 20
- **THEN** the digest includes up to 10 of the shared-cap outlets' most recent stories and, independently, up to 20 of the capped outlet's most recent stories
