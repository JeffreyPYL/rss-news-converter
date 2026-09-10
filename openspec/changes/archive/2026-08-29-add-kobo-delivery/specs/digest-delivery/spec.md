## ADDED Requirements

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
