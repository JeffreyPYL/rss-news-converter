# Feed Ingestion Specification

## Purpose

Fetches and normalizes raw articles from configured news sources across topic buckets for a run, keeping each source's failures isolated so one bad feed never blocks the rest.

## Requirements

### Requirement: Topic-to-source mapping
The system SHALL fetch candidate articles for each of the 6 configured topics (Canada, Ottawa, Hong Kong, China, Tech, Global) from that topic's configured sources: BBC, CBC, and Globe and Mail RSS feeds for all topics; SCMP and RTHK feeds additionally for Hong Kong; and keyword-filtered items from BBC/CBC/Globe and Mail's World/Asia feeds as additional Hong Kong coverage.

#### Scenario: Fetching a topic pulls from all its configured sources
- **WHEN** a run fetches the Hong Kong topic
- **THEN** candidate articles are drawn from BBC, CBC, Globe and Mail, SCMP, RTHK, and keyword-filtered World/Asia items

#### Scenario: A non-Hong-Kong topic uses only its outlet feeds
- **WHEN** a run fetches the Canada topic
- **THEN** candidate articles are drawn only from BBC, CBC, and Globe and Mail feeds, with no SCMP/RTHK involvement

### Requirement: Per-source failure isolation
A source that times out or returns an error SHALL be skipped without failing the run, and SHALL be recorded so the run's outcome can report which sources were skipped and why.

#### Scenario: One broken feed doesn't block the rest
- **WHEN** one configured source times out during a run
- **THEN** the run completes using the remaining sources, and the broken source is recorded as skipped

### Requirement: Lookback window state
The system SHALL only consider articles published since the last successful run. The first-ever run SHALL default to a 48-hour lookback. A missed scheduled run SHALL NOT create a coverage gap — the next successful run SHALL cover everything published since the last success.

#### Scenario: Normal run covers since last success
- **WHEN** a run starts and a prior successful run's timestamp is recorded
- **THEN** only articles published after that timestamp are considered

#### Scenario: First-ever run defaults to 48 hours
- **WHEN** a run starts with no prior successful run recorded
- **THEN** articles published in the last 48 hours are considered

#### Scenario: A missed scheduled run self-heals
- **WHEN** a scheduled run does not execute on a given day and the next run occurs a day later
- **THEN** the next successful run considers articles published since the last actual success, covering the missed day

### Requirement: User-editable feed configuration
Every feed's outlet, URL, topic assignment, and keyword filters SHALL be defined in an external, user-editable configuration file rather than hardcoded, so a feed can be added, removed, or repointed without a code change.

#### Scenario: Adding a feed requires no code change
- **WHEN** a new feed entry is added to the feed configuration file under a topic
- **THEN** the next run fetches candidate articles from that feed for that topic

### Requirement: Per-feed request timeout override
The system SHALL allow a feed's configuration entry to set its own request timeout, overriding the system's default, for an outlet that is slower or less reliable than the rest.

#### Scenario: A feed without its own timeout uses the system default
- **WHEN** a feed's configuration entry does not set a timeout
- **THEN** its request uses the system's default timeout

#### Scenario: A feed's own timeout is honored
- **WHEN** a feed's configuration entry sets its own timeout
- **THEN** its request uses that timeout instead of the default
