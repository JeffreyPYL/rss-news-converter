## 1. Settings and configuration plumbing

- [x] 1.1 Add the new optional `Settings` fields from design.md's Decision 5 (`gdrive_folder_id`, `gdrive_client_id`, `gdrive_client_secret`, `gdrive_refresh_token`, `dropbox_folder_path`, `dropbox_app_key`, `dropbox_app_secret`, `dropbox_refresh_token`, `dropbox_email_to`), all `str | None = None`; verify with a functional test that each reads from a real env var and from `.env`, per the existing `Settings` test pattern.
- [x] 1.2 Document the one-time manual OAuth setup for each provider in the README (per design.md's Decision 3): registering an app, the authorize-in-browser step, and the `curl` exchange for a refresh token; verify by following the documented steps once against a real (or sandbox) provider account and confirming a working refresh token comes out the other end.
- [x] 1.3 Add `dropbox` and `google-api-python-client`/`google-auth` as dependencies via `uv add` (design.md Decision 1); verify `uv sync` succeeds and both import cleanly (`uv run python -c "import dropbox, googleapiclient.discovery, google.oauth2.credentials"`).

## 2. `run_digest`'s generalized extra-targets parameter

- [x] 2.1 Add `extra_epub_targets: dict[str, DigestDelivery] | None = None` to `run_digest` (design.md Decision 4); when set, merge its entries into the `targets` dict already built for `deliver_to_all`, keyed by their given names; verify with a functional test that an extra target configured this way is delivered and reported by name, and that omitting the parameter behaves exactly as before (regression-covering the three existing named parameters).

## 3. Dropbox email delivery (reuses `EmailDelivery` unchanged)

- [x] 3.1 Wire `cli.main()` to construct a second `EmailDelivery` targeting `settings.dropbox_email_to` when configured, added to `extra_epub_targets` under `"dropbox_email"`; verify with a functional test (mirroring the existing Kindle email test) that the EPUB is emailed to the Dropbox-linked address with the same timestamped filename convention, independently of whether Kindle email delivery is also configured.

## 4. Dropbox API delivery

- [x] 4.1 Implement `DropboxApiDelivery` (`infrastructure/delivery/dropbox_api_delivery.py`): a `DropboxClient` `Protocol` capturing only `files_upload(f, path, mode)` (the one call needed), an injectable client constructor parameter defaulting to a real `dropbox.Dropbox(oauth2_refresh_token=..., app_key=..., app_secret=...)`, and a `deliver()` that calls `files_upload` with `rendered` under a `timestamped()` filename in `dropbox_folder_path`, raising `DeliveryError` on any exception from the client; verify with functional tests injecting a hand-written fake `DropboxClient` (per the `python-testing` skill's SDK-mocking section) covering a successful upload and a client that raises, each producing the right outcome.
- [x] 4.2 Add `dropbox_api_delivery_from_env(settings)` factory (mirroring `email_delivery_from_env`), raising `ValueError` listing which of `dropbox_folder_path`/`dropbox_app_key`/`dropbox_app_secret`/`dropbox_refresh_token` are missing; verify with a functional test for both the fully-configured and missing-fields cases.
- [x] 4.3 Wire `cli.main()` to add `dropbox_api_delivery_from_env`'s result to `extra_epub_targets` under `"dropbox_api"` when configured, printing "Dropbox delivery not configured: {error}" on `ValueError` (matching the existing email/Obsidian not-configured pattern); verify by reading the printed output in a functional test with the required env vars unset.

## 5. Google Drive delivery

- [x] 5.1 Implement `GoogleDriveDelivery` (`infrastructure/delivery/google_drive_delivery.py`): a `DriveFilesClient` `Protocol` capturing only the `files().create(...).execute()` call actually used, an injectable client constructor parameter defaulting to a real client built from `googleapiclient.discovery.build("drive", "v3", credentials=...)` using `google.oauth2.credentials.Credentials(refresh_token=..., client_id=..., client_secret=..., token_uri="https://oauth2.googleapis.com/token")`, and a `deliver()` that uploads `rendered` under a `timestamped()` filename into `gdrive_folder_id`, raising `DeliveryError` on any exception from the client; verify with functional tests injecting a hand-written fake `DriveFilesClient` covering a successful upload and a client that raises, each producing the right outcome.
- [x] 5.2 Add `google_drive_delivery_from_env(settings)` factory, raising `ValueError` listing which of `gdrive_folder_id`/`gdrive_client_id`/`gdrive_client_secret`/`gdrive_refresh_token` are missing; verify with a functional test for both the fully-configured and missing-fields cases.
- [x] 5.3 Wire `cli.main()` to add `google_drive_delivery_from_env`'s result to `extra_epub_targets` under `"google_drive"` when configured, printing "Google Drive delivery not configured: {error}" on `ValueError`; verify by reading the printed output in a functional test with the required env vars unset.

## 6. Quality gate

- [x] 6.1 Run `just mutate` and `just crap` across the finished pipeline and fix any surviving mutant that isn't a verified-equivalent case (following this project's established equivalent-mutant baseline) or any function scoring over CRAP 30, before the change is considered done.
- [x] 6.2 Update `ARCHITECTURE.md`'s delivery section and `README.md`'s configuration section (new "Kobo (Google Drive / Dropbox)" heading) to reflect the new delivery targets, per the `architecture-doc-check` and `readme-doc-check` skills.
