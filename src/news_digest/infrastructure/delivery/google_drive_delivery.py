from __future__ import annotations

from datetime import datetime
from typing import Protocol

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload

from news_digest.application.ports import DeliveryError
from news_digest.infrastructure.delivery._filenames import timestamped
from news_digest.infrastructure.settings import Settings


class DriveExecutable(Protocol):
    def execute(self) -> dict: ...


class DriveFilesResource(Protocol):
    def create(
        self, *, body: dict, media_body: MediaInMemoryUpload, fields: str
    ) -> DriveExecutable: ...


class GoogleDriveDelivery:
    """digest-delivery: uploads the rendered EPUB directly to a Google Drive
    folder — the SDK handles refreshing the access token internally from
    the given long-lived refresh token."""

    def __init__(self, files: DriveFilesResource, folder_id: str) -> None:
        self._files = files
        self._folder_id = folder_id

    def deliver(self, rendered: bytes, generated_at: datetime) -> None:
        filename = timestamped(generated_at, "digest.epub")
        media = MediaInMemoryUpload(rendered, mimetype="application/epub+zip")
        try:
            self._files.create(
                body={"name": filename, "parents": [self._folder_id]},
                media_body=media,
                fields="id",
            ).execute()
        except Exception as exc:
            raise DeliveryError(f"Google Drive upload failed: {exc}") from exc


_REQUIRED_FIELDS = (
    "gdrive_folder_id",
    "gdrive_client_id",
    "gdrive_client_secret",
    "gdrive_refresh_token",
)


def google_drive_delivery_from_env(
    settings: Settings | None = None,
) -> GoogleDriveDelivery:
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

    credentials = Credentials(
        token=None,
        refresh_token=settings.gdrive_refresh_token,
        client_id=settings.gdrive_client_id,
        client_secret=settings.gdrive_client_secret,
        token_uri="https://oauth2.googleapis.com/token",
    )
    service = build("drive", "v3", credentials=credentials)
    return GoogleDriveDelivery(
        files=service.files(), folder_id=settings.gdrive_folder_id
    )
