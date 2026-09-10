from __future__ import annotations

import pytest

from news_digest.infrastructure.delivery.email_delivery import email_delivery_from_env
from news_digest.infrastructure.delivery.obsidian_vault_delivery import (
    obsidian_vault_delivery_from_env,
)
from news_digest.infrastructure.settings import Settings

_SMTP_VARS = (
    "NEWS_DIGEST_SMTP_HOST",
    "NEWS_DIGEST_SMTP_PORT",
    "NEWS_DIGEST_SMTP_USERNAME",
    "NEWS_DIGEST_SMTP_PASSWORD",
    "NEWS_DIGEST_EMAIL_FROM",
    "NEWS_DIGEST_EMAIL_TO",
)


def test_settings_reads_from_dotenv_file(tmp_path):
    # tests/conftest.py's autouse fixture already chdir's into tmp_path.
    (tmp_path / ".env").write_text("NEWS_DIGEST_SMTP_HOST=smtp.example.com\n")

    assert Settings().smtp_host == "smtp.example.com"


def test_real_env_var_overrides_dotenv_file(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("NEWS_DIGEST_SMTP_HOST=from-dotenv\n")
    monkeypatch.setenv("NEWS_DIGEST_SMTP_HOST", "from-real-env")

    assert Settings().smtp_host == "from-real-env"


def test_kobo_delivery_settings_read_from_dotenv_file(tmp_path):
    (tmp_path / ".env").write_text(
        "NEWS_DIGEST_GDRIVE_FOLDER_ID=gdrive-folder\n"
        "NEWS_DIGEST_GDRIVE_CLIENT_ID=gdrive-client-id\n"
        "NEWS_DIGEST_GDRIVE_CLIENT_SECRET=gdrive-client-secret\n"
        "NEWS_DIGEST_GDRIVE_REFRESH_TOKEN=gdrive-refresh-token\n"
        "NEWS_DIGEST_DROPBOX_FOLDER_PATH=/kobo\n"
        "NEWS_DIGEST_DROPBOX_APP_KEY=dropbox-app-key\n"
        "NEWS_DIGEST_DROPBOX_APP_SECRET=dropbox-app-secret\n"
        "NEWS_DIGEST_DROPBOX_REFRESH_TOKEN=dropbox-refresh-token\n"
        "NEWS_DIGEST_DROPBOX_EMAIL_TO=kobo@dropbox.example.com\n"
    )

    settings = Settings()

    assert settings.gdrive_folder_id == "gdrive-folder"
    assert settings.gdrive_client_id == "gdrive-client-id"
    assert settings.gdrive_client_secret == "gdrive-client-secret"
    assert settings.gdrive_refresh_token == "gdrive-refresh-token"
    assert settings.dropbox_folder_path == "/kobo"
    assert settings.dropbox_app_key == "dropbox-app-key"
    assert settings.dropbox_app_secret == "dropbox-app-secret"
    assert settings.dropbox_refresh_token == "dropbox-refresh-token"
    assert settings.dropbox_email_to == "kobo@dropbox.example.com"


def test_kobo_delivery_settings_default_to_none(tmp_path):
    assert Settings().gdrive_folder_id is None
    assert Settings().dropbox_email_to is None


def test_email_delivery_from_env_lists_every_missing_field(monkeypatch):
    for var in _SMTP_VARS:
        monkeypatch.delenv(var, raising=False)

    with pytest.raises(ValueError) as exc_info:
        email_delivery_from_env()

    assert (
        str(exc_info.value)
        == f"missing required environment variable(s): {', '.join(_SMTP_VARS)}"
    )


def test_email_delivery_from_env_succeeds_when_fully_configured(monkeypatch):
    monkeypatch.setenv("NEWS_DIGEST_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("NEWS_DIGEST_SMTP_PORT", "465")
    monkeypatch.setenv("NEWS_DIGEST_SMTP_USERNAME", "me@example.com")
    monkeypatch.setenv("NEWS_DIGEST_SMTP_PASSWORD", "secret")
    monkeypatch.setenv("NEWS_DIGEST_EMAIL_FROM", "me@example.com")
    monkeypatch.setenv("NEWS_DIGEST_EMAIL_TO", "kindle@kindle.com")

    delivery = email_delivery_from_env()

    assert delivery._from_addr == "me@example.com"
    assert delivery._to_addr == "kindle@kindle.com"
    assert delivery._sender._host == "smtp.example.com"
    assert delivery._sender._port == 465
    assert delivery._sender._username == "me@example.com"
    assert delivery._sender._password == "secret"


def test_email_delivery_from_env_with_to_addr_override_does_not_require_email_to(
    monkeypatch,
):
    monkeypatch.delenv("NEWS_DIGEST_EMAIL_TO", raising=False)
    monkeypatch.setenv("NEWS_DIGEST_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("NEWS_DIGEST_SMTP_PORT", "465")
    monkeypatch.setenv("NEWS_DIGEST_SMTP_USERNAME", "me@example.com")
    monkeypatch.setenv("NEWS_DIGEST_SMTP_PASSWORD", "secret")
    monkeypatch.setenv("NEWS_DIGEST_EMAIL_FROM", "me@example.com")

    delivery = email_delivery_from_env(to_addr="kobo@dropbox.example.com")

    assert delivery._to_addr == "kobo@dropbox.example.com"
    assert delivery._from_addr == "me@example.com"


def test_email_delivery_from_env_to_addr_override_still_requires_smtp_fields(
    monkeypatch,
):
    for var in _SMTP_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.delenv("NEWS_DIGEST_EMAIL_TO", raising=False)

    with pytest.raises(ValueError) as exc_info:
        email_delivery_from_env(to_addr="kobo@dropbox.example.com")

    # EMAIL_TO isn't required when to_addr overrides it — only the SMTP
    # transport fields and EMAIL_FROM are.
    assert "NEWS_DIGEST_EMAIL_TO" not in str(exc_info.value)
    assert (
        str(exc_info.value)
        == f"missing required environment variable(s): {', '.join(_SMTP_VARS[:-1])}"
    )


def test_obsidian_vault_delivery_from_env_missing_raises(monkeypatch):
    monkeypatch.delenv("NEWS_DIGEST_OBSIDIAN_VAULT_PATH", raising=False)

    with pytest.raises(ValueError) as exc_info:
        obsidian_vault_delivery_from_env()

    assert (
        str(exc_info.value)
        == "missing required environment variable: NEWS_DIGEST_OBSIDIAN_VAULT_PATH"
    )


def test_obsidian_vault_delivery_from_env_succeeds_when_configured(
    monkeypatch, tmp_path
):
    vault = tmp_path / "vault"
    monkeypatch.setenv("NEWS_DIGEST_OBSIDIAN_VAULT_PATH", str(vault))

    delivery = obsidian_vault_delivery_from_env()

    assert delivery._vault_path == vault
