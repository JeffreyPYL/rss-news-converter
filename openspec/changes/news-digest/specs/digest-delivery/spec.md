## Purpose

Gets the rendered digest to where it is actually read: an Obsidian vault and a Kindle/email inbox.

## ADDED Requirements

### Requirement: Obsidian delivery
The rendered Obsidian-flavored note SHALL be written into a configured Obsidian vault path, named with the date and time it was generated, so successive runs accumulate as separate notes rather than overwriting each other.

#### Scenario: A successful run writes a note into the configured vault path
- **WHEN** a run completes rendering
- **THEN** the note is written into the configured Obsidian vault path, named with that run's generation date and time

#### Scenario: Successive runs do not overwrite each other's notes
- **WHEN** two runs complete on the same day at different times
- **THEN** both runs' notes exist in the vault path afterward, each named with its own run's generation date and time

### Requirement: Email/Kindle delivery
The rendered EPUB SHALL be sent via email to a configured address, including a Kindle send-to-Kindle address, named with the date and time it was generated.

#### Scenario: A successful run emails the EPUB to the configured address
- **WHEN** a run completes rendering
- **THEN** the EPUB is sent by email to the configured recipient address, named with that run's generation date and time

### Requirement: Local EPUB copy alongside the Obsidian note
When Obsidian delivery is configured, the same EPUB delivered for email/Kindle delivery SHALL also be saved into the Obsidian vault path, independent of whether email delivery is configured or succeeds, so the generated content can be verified locally.

#### Scenario: A run saves the EPUB into the vault alongside the note
- **WHEN** a run completes with Obsidian delivery configured
- **THEN** a copy of the rendered EPUB is saved into the vault path, named with the same run's generation date and time as that run's note

### Requirement: Delivery failure visibility
If a delivery target fails, the run SHALL report which target failed and why, while still completing delivery to any other configured target.

#### Scenario: Email delivery fails but Obsidian delivery still succeeds
- **WHEN** email delivery fails during a run
- **THEN** the Obsidian delivery still completes, and the run's outcome reports the email delivery failure
