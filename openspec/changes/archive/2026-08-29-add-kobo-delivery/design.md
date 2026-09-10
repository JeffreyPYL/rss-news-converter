## Context

`digest-delivery` today has three targets, each a `DigestDelivery` implementation (`deliver(rendered: bytes, generated_at: datetime) -> None`, raising `DeliveryError` on failure): `EmailDelivery` (plain `smtplib`), `ObsidianVaultDelivery` (writes bytes to a vault-relative path, reused unchanged for both the Markdown note and the vault EPUB copy), and the vault EPUB copy itself. `cli.run_digest` builds a `targets: dict[str, tuple[DigestDelivery, bytes]]` from whichever of its optional delivery parameters are non-`None`, then calls `deliver_to_all(targets, generated_at)`, which attempts each independently and reports failures by name without blocking the others. `cli.main()` wires concrete instances from `Settings` via small `*_from_env` factory functions that raise `ValueError` when required config is missing.

CLAUDE.md makes `httpx` the only HTTP client anywhere in this codebase for calls this codebase itself makes — load-bearing, since `pytest-httpx`'s `httpx_mock` fixture only intercepts `httpx`. That rule governs code we write against a plain REST API; it does not extend to a third-party SDK's internal transport, which this codebase doesn't maintain and shouldn't try to mock (see the `python-testing` skill's "Mocking a third-party SDK" section, added alongside this change). Confirmed while researching this change: Dropbox's official SDK (`dropbox`) is built on `requests`; Google's (`google-api-python-client`) defaults to `httplib2`, not `requests` — the two SDKs don't even share a transport, which is itself part of why testing against the SDK boundary rather than its HTTP layer is the only approach that generalizes across both.

See `proposal.md` for the motivating "why" — this covers the "how."

## Goals / Non-Goals

**Goals:**
- Google Drive delivery and Dropbox delivery (API-based) as new `DigestDelivery` implementations, built on each provider's official SDK.
- Dropbox email delivery reusing `EmailDelivery` unchanged, as a second configured recipient.
- All three new targets independently optional, independently failing, and following the existing timestamped-filename convention.
- A `run_digest`/`cli.main()` wiring approach that doesn't grow an unbounded list of named delivery parameters as more targets get added.

**Non-Goals:**
- No in-pipeline OAuth consent/browser flow. This pipeline only ever reads an already-issued, long-lived credential from `Settings` — obtaining that credential is a one-time step the user does outside a normal run.
- No changes to the existing Kindle/email, Obsidian, or vault-EPUB-copy targets' behavior.
- No token-refresh caching across runs — each run's process is short-lived (a single CLI invocation), so refreshing once per run is enough; no persistent cache needed.

## Decisions

**1. Use each provider's official SDK (`dropbox`, `google-api-python-client`), not hand-rolled `httpx` calls.**
Reversed from this design's first draft. The SDKs absorb protocol/versioning risk (retries, pagination, error-code semantics, wire-format changes) that a hand-rolled REST client would otherwise leave to this codebase to track — and per Decision 7 below, testability no longer depends on `httpx_mock` seeing the traffic, so the original reason to avoid the SDKs (Dropbox's uses `requests`, Google's uses `httplib2` by default — neither is `httpx`) no longer applies. `google-api-python-client` additionally handles Drive's discovery-document/resumable-upload details that would otherwise need reimplementing by hand.

**2. OAuth2 refresh-token flow for *both* providers, not a Google service account.**
A service account (JSON key, no interactive consent, share the target folder with its email) was considered for Drive since it avoids any one-time user interaction at all — but it requires signing a JWT (RS256), which `google-auth` (a dependency of `google-api-python-client`) already does internally when needed, so this isn't actually extra work either way. Refresh-token flow was still preferred for symmetry with Dropbox (same one-time setup shape for both providers, documented once, one mental model) and because it doesn't require the user to explicitly share the target Drive folder with a separate service-account identity — the refresh token is tied to the user's own account and can see whatever folder they pick. Each SDK is handed this refresh token directly (`dropbox.Dropbox(oauth2_refresh_token=..., app_key=..., app_secret=...)`; `google.oauth2.credentials.Credentials(refresh_token=..., ...)` passed to `googleapiclient.discovery.build()`) and handles minting/renewing the short-lived access token internally — this codebase never talks to either provider's token endpoint directly.

**3. Credential setup is a one-time, documented manual step — no interactive setup script.**
Getting the initial refresh token (registering an app with each provider, doing the one-time authorize-in-browser dance, exchanging the resulting code for a refresh token) is documented in the README as a sequence of steps (mostly `curl` against each provider's OAuth endpoints), not a script this codebase ships and tests. This keeps the addition scoped to the recurring delivery path, which is the part that actually needs test coverage and quality-gate attention; a one-off setup helper would need its own tests for something that runs, at most, a handful of times ever. **Flagged as an assumption, not a firm requirement** — if the manual `curl` sequence proves too fiddly in practice, a small interactive helper script is a reasonable follow-up, not a redesign.

**4. Replace `run_digest`'s growing list of named `DigestDelivery` parameters with a single collection.**
Today: `email_delivery`, `obsidian_delivery`, `epub_copy_delivery` — three named optional parameters. Adding Drive, Dropbox-API, and Dropbox-email as more named parameters would make it six, all doing the same "may or may not be configured" dance. Instead, `run_digest` gains one new parameter, `extra_epub_targets: dict[str, DigestDelivery] | None = None`, for any target beyond the existing three that delivers the EPUB specifically (every new target here does — Drive, Dropbox-API, and Dropbox-email all send the EPUB, never the Markdown note). `cli.main()` builds this dict from whichever of the three are configured, keyed by name (`"google_drive"`, `"dropbox_api"`, `"dropbox_email"`) for `deliver_to_all`'s failure reporting. The three existing named parameters (`email_delivery`, `obsidian_delivery`, `epub_copy_delivery`) are unchanged — this only stops the *next* addition from growing the signature further.

**5. New `Settings` fields, one group per provider**, all optional (`None` = not configured, matching every existing target):
- Google Drive: `gdrive_folder_id`, `gdrive_client_id`, `gdrive_client_secret`, `gdrive_refresh_token`.
- Dropbox (shared by both mechanisms where applicable): `dropbox_folder_path`, `dropbox_app_key`, `dropbox_app_secret`, `dropbox_refresh_token` (API route); `dropbox_email_to` (email route — independent of the API credentials; a user could configure only the email route without ever registering a Dropbox app).

**6. New delivery classes**: `GoogleDriveDelivery` (`infrastructure/delivery/google_drive_delivery.py`) and `DropboxApiDelivery` (`infrastructure/delivery/dropbox_api_delivery.py`). Each takes an injectable client parameter — a narrow `Protocol` capturing only the one or two calls actually used (per Decision 7), defaulting to constructing the real SDK client from the provider's credentials — plus the target folder. `deliver()` uploads `rendered` under a timestamped filename (reusing the existing `timestamped()` helper from `infrastructure/delivery/_filenames.py`) via the injected client, and raises `DeliveryError` on any exception the client raises. The Dropbox-email route needs no new class — `cli.main()` constructs a second `EmailDelivery` pointed at `settings.dropbox_email_to`.

**7. Test each new delivery class at the SDK boundary, not by mocking HTTP.**
Per the `python-testing` skill's new "Mocking a third-party SDK" section (added alongside this change): define a `Protocol` for each SDK client capturing only the method(s) `GoogleDriveDelivery`/`DropboxApiDelivery` actually call (e.g. `files_upload` for Dropbox), inject an instance as a constructor parameter, and test with a hand-written fake implementing that same `Protocol` — the same seam pattern already used for `ProcessRunner`, `ExtractFn`, and `SmtpSender`. This verifies our glue code (does it call the client with the right arguments, does it turn the client's exceptions into `DeliveryError`) without needing to know or care which HTTP library either SDK uses underneath.

## Risks / Trade-offs

- **[Risk]** A revoked or expired refresh token silently breaks one target. → **Mitigation**: handled like any other delivery failure — `DeliveryError` surfaces it by name via existing failure-visibility reporting; no special-casing needed.
- **[Risk]** Two new dependencies (`dropbox`, `google-api-python-client`) with their own transitive dependencies and release cadence, neither maintained by this project. → **Mitigation**: pin to major versions in `pyproject.toml` like every other dependency; the SDK-boundary testing approach (Decision 7) means a minor-version bump inside either SDK can't silently break this codebase's tests the way a wire-format change could have under the hand-rolled approach — a break there would show up as a real interface change, caught by `pyrefly`/tests, not a subtle runtime surprise.
- **[Risk]** This is meaningfully larger in surface area than any single prior addition to this pipeline — two new external services, three new delivery mechanisms, new credential plumbing. → **Mitigation**: none needed beyond normal scoping; noting it so `tasks.md`'s size doesn't come as a surprise relative to past changes.
- **[Trade-off]** Documented manual setup (Decision 3) is more friction for the user than a guided script, in exchange for not shipping and testing a rarely-run helper. Acceptable given this is a one-time step per provider, not a recurring one.

## Open Questions

- Exact OAuth scopes to request when registering each provider's app (Dropbox: `files.content.write` at minimum; Google: `drive.file` at minimum, which only grants access to files/folders the app itself creates or the user explicitly picks — sufficient here since delivery only ever creates new files). Finalized during implementation against each provider's current documentation, not a blocker to the approach above.
