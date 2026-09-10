# Digest Delivery Specification

## Purpose

Gets the rendered digest to where it is actually read: an Obsidian vault and a Kindle/email inbox.

## Requirements

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

### Requirement: Google Drive delivery
The system SHALL support uploading the rendered EPUB to a configured Google Drive folder as an optional, independently-configured delivery target, named with the date and time it was generated.

#### Scenario: A successful run uploads the EPUB to the configured Drive folder
- **WHEN** a run completes rendering with Google Drive delivery configured
- **THEN** the EPUB is uploaded to the configured Google Drive folder, named with that run's generation date and time

#### Scenario: Google Drive delivery is skipped when not configured
- **WHEN** a run completes and no Google Drive credentials/folder are configured
- **THEN** the run does not attempt Google Drive delivery and does not treat this as a failure

### Requirement: Dropbox delivery
The system SHALL support delivering the rendered EPUB to Dropbox as an optional, independently-configured delivery target, via either or both of two mechanisms: direct upload to a configured Dropbox folder, and email to a configured Dropbox-linked address. Either mechanism's delivered file SHALL be named with the date and time it was generated.

#### Scenario: A successful run uploads the EPUB directly to the configured Dropbox folder
- **WHEN** a run completes rendering with Dropbox API delivery configured
- **THEN** the EPUB is uploaded to the configured Dropbox folder, named with that run's generation date and time

#### Scenario: A successful run emails the EPUB to the configured Dropbox-linked address
- **WHEN** a run completes rendering with Dropbox email delivery configured
- **THEN** the EPUB is sent by email to the configured Dropbox-linked address, named with that run's generation date and time

#### Scenario: Both Dropbox mechanisms can be configured and run independently
- **WHEN** a run completes with both Dropbox API delivery and Dropbox email delivery configured
- **THEN** both are attempted, and one failing does not prevent the other from completing

#### Scenario: Dropbox delivery is skipped when neither mechanism is configured
- **WHEN** a run completes and neither Dropbox delivery mechanism is configured
- **THEN** the run does not attempt Dropbox delivery and does not treat this as a failure

### Requirement: New delivery targets follow existing failure isolation
A failure in Google Drive delivery or either Dropbox delivery mechanism SHALL be reported by name, without blocking delivery to any other configured target (Kindle/email, Obsidian, vault EPUB copy, or the other Kobo-related targets).

#### Scenario: A failed Dropbox upload does not block other configured targets
- **WHEN** Dropbox API delivery fails during a run that also has Obsidian delivery configured
- **THEN** the Obsidian delivery still completes, and the run's outcome reports the Dropbox delivery failure by name

### Requirement: Delivery failure visibility
If a delivery target fails, the run SHALL report which target failed and why, while still completing delivery to any other configured target.

#### Scenario: Email delivery fails but Obsidian delivery still succeeds
- **WHEN** email delivery fails during a run
- **THEN** the Obsidian delivery still completes, and the run's outcome reports the email delivery failure
