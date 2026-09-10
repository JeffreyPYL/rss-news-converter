from __future__ import annotations

import smtplib
from datetime import datetime
from email.message import EmailMessage
from typing import Protocol

from news_digest.application.ports import DeliveryError
from news_digest.infrastructure.delivery._filenames import timestamped
from news_digest.infrastructure.settings import Settings


class SmtpSender(Protocol):
    def send(self, message: EmailMessage) -> None: ...


class SmtplibSender:
    """The real SMTP transport — Send-to-Kindle is just email, no HTTP API exists for it."""

    def __init__(self, host: str, port: int, username: str, password: str) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password

    def send(self, message: EmailMessage) -> None:
        with smtplib.SMTP_SSL(self._host, self._port) as smtp:
            smtp.login(self._username, self._password)
            smtp.send_message(message)


class EmailDelivery:
    """digest-delivery: emails the rendered EPUB, e.g. to a Kindle send-to-Kindle address."""

    def __init__(self, sender: SmtpSender, from_addr: str, to_addr: str) -> None:
        self._sender = sender
        self._from_addr = from_addr
        self._to_addr = to_addr

    def deliver(self, rendered: bytes, generated_at: datetime) -> None:
        message = EmailMessage()
        message["From"] = self._from_addr
        message["To"] = self._to_addr
        message["Subject"] = "News Digest"
        message.set_content("Your news digest is attached.")
        message.add_attachment(
            rendered,
            maintype="application",
            subtype="epub+zip",
            filename=timestamped(generated_at, "digest.epub"),
        )
        try:
            self._sender.send(message)
        except Exception as exc:
            raise DeliveryError(f"email delivery failed: {exc}") from exc


_REQUIRED_SMTP_FIELDS = (
    "smtp_host",
    "smtp_port",
    "smtp_username",
    "smtp_password",
    "email_from",
)


def email_delivery_from_env(
    settings: Settings | None = None, to_addr: str | None = None
) -> EmailDelivery:
    """Config deferred to env vars (or a `.env` file — see `Settings`), per
    the vault-path/credentials decision in proposal.md.

    `to_addr` overrides `settings.email_to` — used to reuse the same SMTP
    credentials for a second recipient (e.g. a Kobo's Dropbox-linked "email
    to Dropbox" address) without requiring `NEWS_DIGEST_EMAIL_TO` to also be
    set for that to work.
    """
    settings = settings or Settings()
    required = (
        _REQUIRED_SMTP_FIELDS
        if to_addr is not None
        else (*_REQUIRED_SMTP_FIELDS, "email_to")
    )
    missing = [
        f"NEWS_DIGEST_{name.upper()}"
        for name in required
        if getattr(settings, name) is None
    ]
    if missing:
        raise ValueError(
            f"missing required environment variable(s): {', '.join(missing)}"
        )

    sender = SmtplibSender(
        host=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password,
    )
    return EmailDelivery(
        sender=sender,
        from_addr=settings.email_from,
        to_addr=to_addr or settings.email_to,
    )
