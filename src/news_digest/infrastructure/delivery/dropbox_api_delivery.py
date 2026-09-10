from __future__ import annotations

from datetime import datetime
from typing import Protocol

import dropbox

from news_digest.application.ports import DeliveryError
from news_digest.infrastructure.delivery._filenames import timestamped
from news_digest.infrastructure.settings import Settings


class DropboxClient(Protocol):
    def files_upload(self, f: bytes, path: str) -> object: ...


class DropboxApiDelivery:
    """digest-delivery: uploads the rendered EPUB directly to a Dropbox
    folder — the SDK handles refreshing the access token internally from
    the given long-lived refresh token."""

    def __init__(self, client: DropboxClient, folder_path: str) -> None:
        self._client = client
        self._folder_path = folder_path

    def deliver(self, rendered: bytes, generated_at: datetime) -> None:
        filename = timestamped(generated_at, "digest.epub")
        path = f"{self._folder_path.rstrip('/')}/{filename}"
        try:
            self._client.files_upload(rendered, path)
        except Exception as exc:
            raise DeliveryError(f"Dropbox upload failed: {exc}") from exc


_REQUIRED_FIELDS = (
    "dropbox_folder_path",
    "dropbox_app_key",
    "dropbox_app_secret",
    "dropbox_refresh_token",
)


def dropbox_api_delivery_from_env(
    settings: Settings | None = None,
) -> DropboxApiDelivery:
    """Config deferred to env vars (or a `.env` file — see `Settings`)."""
    settings = settings or Settings()
    missing = [
        f"NEWS_DIGEST_{name.upper()}"
        for name in _REQUIRED_FIELDS
        if getattr(settings, name) is None
    ]
    if missing:
        raise ValueError(
            f"missing required environment variable(s): {', '.join(missing)}"
        )

    client = dropbox.Dropbox(
        oauth2_refresh_token=settings.dropbox_refresh_token,
        app_key=settings.dropbox_app_key,
        app_secret=settings.dropbox_app_secret,
    )
    return DropboxApiDelivery(client=client, folder_path=settings.dropbox_folder_path)
