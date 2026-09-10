# Article Extraction Specification

## Purpose

Turns a feed item's URL into full article text and images by fetching the live page directly, without needing login, session credentials, or browser automation.

## Requirements

### Requirement: Unauthenticated full-text extraction
The system SHALL retrieve full article text and images from a source URL via a plain, unauthenticated HTTP fetch, without browser automation or stored session/login credentials, across all configured sources including paywalled ones.

#### Scenario: Extracting a paywalled Globe and Mail article without login succeeds
- **WHEN** the system extracts a Globe and Mail article URL
- **THEN** the full article text and its images are returned without any login or session being used

### Requirement: Extractor is swappable
The extraction engine SHALL be configurable between at least two implementations (Trafilatura as the default, Defuddle as an alternative) via configuration, without any other pipeline stage changing.

#### Scenario: Switching extractor config changes only extraction output
- **WHEN** the configured extractor is changed from Trafilatura to Defuddle
- **THEN** only the extracted article content differs; ingestion, grouping, rendering, and delivery behavior are unaffected

### Requirement: Graceful extraction failure
If full-text extraction fails for a specific article (for example, a hard-gated or malformed page), the system SHALL fall back to that article's headline, teaser, and source link rather than failing the run.

#### Scenario: A hard-gated article falls back to teaser and link
- **WHEN** extraction fails for one article in a run
- **THEN** that article appears in the digest with its headline, teaser, and link, and the rest of the run completes normally
