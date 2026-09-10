## Why

The digest currently only reaches a Kindle (via email) and an Obsidian vault. The user reads on a Kobo Libra Colour too, and Kobo has no Kindle-style built-in send-to-device email address — delivery there is necessarily pull-based, through a cloud folder (Google Drive and/or Dropbox) the device syncs from on its own schedule. Confirmed acceptable: that sync delay, versus Kindle's near-immediate email delivery.

## What Changes

- Add Google Drive as an optional delivery target: the rendered EPUB is uploaded directly to a configured Drive folder via Google's official `google-api-python-client` SDK.
- Add Dropbox as an optional delivery target, with **two** independently usable delivery mechanisms:
  - Direct upload to a configured Dropbox folder via Dropbox's official `dropbox` SDK.
  - Email delivery to the Kobo/Dropbox-linked "email to Dropbox" address, reusing the existing `EmailDelivery`/`SmtplibSender` class unchanged — just a second configured recipient, the same pattern already used for the Kindle target and the vault-EPUB-copy target.
- Both new targets are independently optional and configured via `Settings`/`.env`, following the existing pattern (missing config -> target not attempted, reported as "not configured," never a hard failure).
- Both new targets plug into the existing `DigestDelivery` Protocol and `deliver_to_all`'s per-target failure isolation — one target failing (e.g. an expired Dropbox token) never blocks the others.
- Uploaded/emailed files use the same timestamped naming convention already established for the Kindle attachment, Obsidian note, and vault EPUB copy.
- **Out of scope for this change**: any in-pipeline OAuth consent flow. Getting a long-lived Drive/Dropbox credential is a one-time manual setup step the user does outside this pipeline (see design.md); this pipeline only ever reads an already-issued token from `Settings`.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `digest-delivery`: adds Google Drive delivery and Dropbox delivery (API-based and email-based) as additional optional, independently-failing delivery targets alongside the existing Obsidian and email/Kindle ones.

## Impact

- New files: `infrastructure/delivery/google_drive_delivery.py`, `infrastructure/delivery/dropbox_api_delivery.py` (named to disambiguate from the existing email-based route), each a `DigestDelivery` implementation wrapping its provider's SDK client behind an injectable `Protocol` (see design.md's SDK-boundary testing decision).
- `infrastructure/settings.py`: new fields for Drive (folder id, OAuth client id/secret, refresh token) and Dropbox (folder path, app key/secret, refresh token) and a second email recipient for the Dropbox-via-email route.
- `cli.py`: `main()` wires up the two new targets from `Settings`, same pattern as the existing `email_delivery_from_env`/`obsidian_vault_delivery_from_env` factories; `run_digest` gains a general `extra_epub_targets` collection (a design.md decision) rather than more named parameters.
- New dependencies: `dropbox` (official Dropbox SDK) and `google-api-python-client` + `google-auth` (official Google API client and auth library) added to `pyproject.toml`.
- `.claude/skills/python-testing/SKILL.md`: new "Mocking a third-party SDK" section — test at the SDK's own interface via an injectable `Protocol` and a hand-written fake, not by trying to mock the SDK's internal HTTP transport.
- README: new "Kobo (Google Drive / Dropbox)" configuration section documenting the one-time manual credential setup for each provider.
