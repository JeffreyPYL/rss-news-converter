from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_STATE_PATH = Path.home() / ".local" / "state" / "news-digest" / "run_state.json"


class Settings(BaseSettings):
    """All NEWS_DIGEST_* configuration in one place, read from the environment
    or a `.env` file in the current working directory (real env vars win over
    `.env` — pydantic-settings' default precedence).

    Fields stay loosely typed (`str | None`) where the existing parsing
    functions already tolerate messy input (`synthesis_enabled`'s
    strip+lowercase check) — a strict type here would change what counts as
    valid input, which isn't what adding `.env` support is for.
    """

    model_config = SettingsConfigDict(
        env_prefix="NEWS_DIGEST_", env_file=".env", extra="ignore"
    )

    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_username: str | None = None
    smtp_password: str | None = None
    email_from: str | None = None
    email_to: str | None = None

    obsidian_vault_path: Path | None = None

    extractor: str | None = None
    synthesis_enabled: str | None = None
    state_path: Path = DEFAULT_STATE_PATH
    # None means "use the packaged default feeds.json" (see
    # infrastructure/feeds/config.py::DEFAULT_FEEDS_PATH) — set this only to
    # point at a different feed list entirely.
    feeds_config_path: Path | None = None

    # Kobo delivery (see add-kobo-delivery's design.md) — each provider's
    # fields are independent of the others; any subset left unset means that
    # target isn't configured, same as every other delivery target.
    gdrive_folder_id: str | None = None
    gdrive_client_id: str | None = None
    gdrive_client_secret: str | None = None
    gdrive_refresh_token: str | None = None

    dropbox_folder_path: str | None = None
    dropbox_app_key: str | None = None
    dropbox_app_secret: str | None = None
    dropbox_refresh_token: str | None = None
    dropbox_email_to: str | None = None
