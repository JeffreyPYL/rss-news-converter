from __future__ import annotations

from datetime import UTC, datetime

import dropbox
import pytest
from google.oauth2.credentials import Credentials

from news_digest.application.ports import DeliveryError
from news_digest.infrastructure.delivery.dropbox_api_delivery import (
    DropboxApiDelivery,
    dropbox_api_delivery_from_env,
)
from news_digest.infrastructure.delivery.google_drive_delivery import (
    GoogleDriveDelivery,
    google_drive_delivery_from_env,
)

_GDRIVE_VARS = (
    "NEWS_DIGEST_GDRIVE_FOLDER_ID",
    "NEWS_DIGEST_GDRIVE_CLIENT_ID",
    "NEWS_DIGEST_GDRIVE_CLIENT_SECRET",
    "NEWS_DIGEST_GDRIVE_REFRESH_TOKEN",
)

_DROPBOX_API_VARS = (
    "NEWS_DIGEST_DROPBOX_FOLDER_PATH",
    "NEWS_DIGEST_DROPBOX_APP_KEY",
    "NEWS_DIGEST_DROPBOX_APP_SECRET",
    "NEWS_DIGEST_DROPBOX_REFRESH_TOKEN",
)

EPUB_BYTES = b"fake-epub-bytes"
GENERATED_AT = datetime(2026, 8, 28, 14, 5, tzinfo=UTC)


class RecordingDropboxClient:
    """A fake DropboxClient — per the python-testing skill's SDK-mocking
    section, this fakes the SDK's own interface rather than its HTTP calls."""

    def __init__(self) -> None:
        self.uploads: list[tuple[bytes, str]] = []

    def files_upload(self, f: bytes, path: str) -> object:
        self.uploads.append((f, path))
        return object()


class FailingDropboxClient:
    def files_upload(self, f: bytes, path: str) -> object:
        raise RuntimeError("Dropbox API error: expired_access_token")


@pytest.fixture
def recording_dropbox_client():
    return RecordingDropboxClient()


@pytest.fixture
def failing_dropbox_client():
    return FailingDropboxClient()


def test_successful_run_uploads_the_epub_to_the_configured_dropbox_folder(
    recording_dropbox_client,
):
    delivery = DropboxApiDelivery(client=recording_dropbox_client, folder_path="/kobo")

    delivery.deliver(EPUB_BYTES, GENERATED_AT)

    assert len(recording_dropbox_client.uploads) == 1
    content, path = recording_dropbox_client.uploads[0]
    assert content == EPUB_BYTES
    assert path == "/kobo/2026-08-28 1405 digest.epub"


def test_folder_path_trailing_slash_does_not_produce_a_double_slash(
    recording_dropbox_client,
):
    delivery = DropboxApiDelivery(client=recording_dropbox_client, folder_path="/kobo/")

    delivery.deliver(EPUB_BYTES, GENERATED_AT)

    _, path = recording_dropbox_client.uploads[0]
    assert path == "/kobo/2026-08-28 1405 digest.epub"


def test_folder_path_rstrip_only_strips_the_trailing_slash_not_other_characters(
    recording_dropbox_client,
):
    # A folder path ending in "X" right before the slash: rstrip('/') should
    # strip only the slash, leaving the "X" — distinguishes it from a charset
    # that (by accident) also strips trailing "X" characters.
    delivery = DropboxApiDelivery(
        client=recording_dropbox_client, folder_path="/koboX/"
    )

    delivery.deliver(EPUB_BYTES, GENERATED_AT)

    _, path = recording_dropbox_client.uploads[0]
    assert path == "/koboX/2026-08-28 1405 digest.epub"


def test_dropbox_upload_failure_raises_delivery_error(failing_dropbox_client):
    delivery = DropboxApiDelivery(client=failing_dropbox_client, folder_path="/kobo")

    with pytest.raises(DeliveryError) as exc_info:
        delivery.deliver(EPUB_BYTES, GENERATED_AT)

    assert "Dropbox upload failed" in str(exc_info.value)
    assert "expired_access_token" in str(exc_info.value)


def test_dropbox_api_delivery_from_env_lists_every_missing_field(monkeypatch):
    for var in _DROPBOX_API_VARS:
        monkeypatch.delenv(var, raising=False)

    with pytest.raises(ValueError) as exc_info:
        dropbox_api_delivery_from_env()

    assert (
        str(exc_info.value)
        == f"missing required environment variable(s): {', '.join(_DROPBOX_API_VARS)}"
    )


def test_dropbox_api_delivery_from_env_succeeds_when_fully_configured(monkeypatch):
    monkeypatch.setenv("NEWS_DIGEST_DROPBOX_FOLDER_PATH", "/kobo")
    monkeypatch.setenv("NEWS_DIGEST_DROPBOX_APP_KEY", "app-key")
    monkeypatch.setenv("NEWS_DIGEST_DROPBOX_APP_SECRET", "app-secret")
    monkeypatch.setenv("NEWS_DIGEST_DROPBOX_REFRESH_TOKEN", "refresh-token")

    delivery = dropbox_api_delivery_from_env()

    assert delivery._folder_path == "/kobo"
    assert isinstance(delivery._client, dropbox.Dropbox)
    assert delivery._client._oauth2_refresh_token == "refresh-token"
    assert delivery._client._app_key == "app-key"
    assert delivery._client._app_secret == "app-secret"


class RecordingDriveExecutable:
    def __init__(self, result: dict) -> None:
        self._result = result

    def execute(self) -> dict:
        return self._result


class RecordingDriveFilesResource:
    """A fake matching the exact `.create(...).execute()` chain
    `GoogleDriveDelivery` calls on the real `service.files()` resource —
    per the python-testing skill's SDK-mocking section, this fakes the
    SDK's own interface rather than its HTTP calls."""

    def __init__(self) -> None:
        self.creates: list[dict] = []

    def create(self, *, body, media_body, fields):
        self.creates.append({"body": body, "media_body": media_body, "fields": fields})
        return RecordingDriveExecutable({"id": "fake-file-id"})


class FailingDriveExecutable:
    def execute(self) -> dict:
        raise RuntimeError("Drive API error: invalid_grant")


class FailingDriveFilesResource:
    def create(self, *, body, media_body, fields):
        return FailingDriveExecutable()


@pytest.fixture
def recording_drive_files():
    return RecordingDriveFilesResource()


@pytest.fixture
def failing_drive_files():
    return FailingDriveFilesResource()


def test_successful_run_uploads_the_epub_to_the_configured_drive_folder(
    recording_drive_files,
):
    delivery = GoogleDriveDelivery(
        files=recording_drive_files, folder_id="drive-folder"
    )

    delivery.deliver(EPUB_BYTES, GENERATED_AT)

    assert len(recording_drive_files.creates) == 1
    call = recording_drive_files.creates[0]
    assert call["body"] == {
        "name": "2026-08-28 1405 digest.epub",
        "parents": ["drive-folder"],
    }
    assert call["fields"] == "id"
    media = call["media_body"]
    assert media.mimetype() == "application/epub+zip"
    assert media.getbytes(0, len(EPUB_BYTES)) == EPUB_BYTES


def test_drive_upload_failure_raises_delivery_error(failing_drive_files):
    delivery = GoogleDriveDelivery(files=failing_drive_files, folder_id="drive-folder")

    with pytest.raises(DeliveryError) as exc_info:
        delivery.deliver(EPUB_BYTES, GENERATED_AT)

    assert "Google Drive upload failed" in str(exc_info.value)
    assert "invalid_grant" in str(exc_info.value)


def test_google_drive_delivery_from_env_lists_every_missing_field(monkeypatch):
    for var in _GDRIVE_VARS:
        monkeypatch.delenv(var, raising=False)

    with pytest.raises(ValueError) as exc_info:
        google_drive_delivery_from_env()

    assert (
        str(exc_info.value)
        == f"missing required environment variable(s): {', '.join(_GDRIVE_VARS)}"
    )


def test_google_drive_delivery_from_env_succeeds_when_fully_configured(monkeypatch):
    monkeypatch.setenv("NEWS_DIGEST_GDRIVE_FOLDER_ID", "drive-folder")
    monkeypatch.setenv("NEWS_DIGEST_GDRIVE_CLIENT_ID", "client-id")
    monkeypatch.setenv("NEWS_DIGEST_GDRIVE_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("NEWS_DIGEST_GDRIVE_REFRESH_TOKEN", "refresh-token")

    delivery = google_drive_delivery_from_env()

    assert delivery._folder_id == "drive-folder"
    credentials = delivery._files._http.credentials
    assert isinstance(credentials, Credentials)
    assert credentials.refresh_token == "refresh-token"
    assert credentials.client_id == "client-id"
    assert credentials.client_secret == "client-secret"
    assert credentials.token_uri == "https://oauth2.googleapis.com/token"
    assert delivery._files._rootDesc.get("name") == "drive"
    assert delivery._files._rootDesc.get("version") == "v3"
