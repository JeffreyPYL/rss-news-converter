from __future__ import annotations

from datetime import UTC, datetime
from email.message import EmailMessage

import pytest

from news_digest.application.deliver_digest import deliver_to_all
from news_digest.application.ports import DeliveryError
from news_digest.infrastructure.delivery.email_delivery import EmailDelivery
from news_digest.infrastructure.delivery.obsidian_vault_delivery import (
    ObsidianVaultDelivery,
)

EPUB_BYTES = b"fake-epub-bytes"
MARKDOWN_BYTES = b"# News Digest"
GENERATED_AT = datetime(2026, 8, 28, 14, 5, tzinfo=UTC)


class RecordingSmtpSender:
    """A fake SmtpSender that records what would have been sent, per
    python-testing's fixture-not-patch rule for test doubles."""

    def __init__(self) -> None:
        self.sent: list[EmailMessage] = []

    def send(self, message: EmailMessage) -> None:
        self.sent.append(message)


class FailingSmtpSender:
    def send(self, message: EmailMessage) -> None:
        raise ConnectionError("smtp server refused connection")


class FailingDelivery:
    def deliver(self, rendered: bytes, generated_at: datetime) -> None:
        raise DeliveryError("simulated delivery failure")


class RecordingDelivery:
    def __init__(self) -> None:
        self.delivered: list[bytes] = []

    def deliver(self, rendered: bytes, generated_at: datetime) -> None:
        self.delivered.append(rendered)


@pytest.fixture
def recording_smtp_sender():
    return RecordingSmtpSender()


@pytest.fixture
def failing_smtp_sender():
    return FailingSmtpSender()


def test_successful_run_emails_the_epub_to_the_configured_address(
    recording_smtp_sender,
):
    delivery = EmailDelivery(
        sender=recording_smtp_sender,
        from_addr="me@example.com",
        to_addr="kindle@kindle.com",
    )

    delivery.deliver(EPUB_BYTES, GENERATED_AT)

    assert len(recording_smtp_sender.sent) == 1
    message = recording_smtp_sender.sent[0]
    # Header lookup on EmailMessage is case-insensitive, so exact-case
    # correctness needs `.items()`, which preserves what was actually set.
    header_names = [name for name, _ in message.items()]
    assert "From" in header_names
    assert "To" in header_names
    assert "Subject" in header_names
    assert message["From"] == "me@example.com"
    assert message["To"] == "kindle@kindle.com"
    assert message["Subject"] == "News Digest"
    body = message.get_body(preferencelist=("plain",))
    assert body.get_content().strip() == "Your news digest is attached."
    attachment = next(message.iter_attachments())
    assert attachment.get_content() == EPUB_BYTES
    assert attachment.get_content_type() == "application/epub+zip"
    # get_content_type() lowercases its result, so it can't catch a case
    # regression in maintype/subtype — the raw header preserves exact case.
    assert attachment["Content-Type"].startswith("application/epub+zip")
    # Date prefix, then time with no seconds — so successive runs' emails
    # don't collide, and the filename alone tells you which run it was.
    assert attachment.get_filename() == "2026-08-28 1405 digest.epub"


def test_email_delivery_failure_raises_delivery_error(failing_smtp_sender):
    delivery = EmailDelivery(
        sender=failing_smtp_sender,
        from_addr="me@example.com",
        to_addr="kindle@kindle.com",
    )

    with pytest.raises(DeliveryError) as exc_info:
        delivery.deliver(EPUB_BYTES, GENERATED_AT)

    assert (
        str(exc_info.value) == "email delivery failed: smtp server refused connection"
    )


def test_successful_run_writes_a_note_into_the_configured_vault_path(tmp_path):
    delivery = ObsidianVaultDelivery(vault_path=tmp_path / "vault")

    delivery.deliver(MARKDOWN_BYTES, GENERATED_AT)

    written = tmp_path / "vault" / "2026-08-28 1405 News Digest.md"
    assert written.read_bytes() == MARKDOWN_BYTES


def test_delivery_creates_nested_vault_directories_that_dont_exist_yet(tmp_path):
    nested = tmp_path / "obsidian" / "vaults" / "news"
    delivery = ObsidianVaultDelivery(vault_path=nested)

    delivery.deliver(MARKDOWN_BYTES, GENERATED_AT)

    assert (nested / "2026-08-28 1405 News Digest.md").read_bytes() == MARKDOWN_BYTES


def test_delivery_twice_in_the_same_run_does_not_raise(tmp_path):
    delivery = ObsidianVaultDelivery(vault_path=tmp_path / "vault")

    delivery.deliver(MARKDOWN_BYTES, GENERATED_AT)
    # Same generated_at as a real run would pass to every target in one
    # run — the directory (and file) already exists on the 2nd call.
    delivery.deliver(MARKDOWN_BYTES, GENERATED_AT)

    assert (tmp_path / "vault" / "2026-08-28 1405 News Digest.md").read_bytes() == (
        MARKDOWN_BYTES
    )


def test_delivery_failure_when_vault_path_is_blocked_by_a_file(tmp_path):
    blocking_file = tmp_path / "blocked"
    blocking_file.write_text("not a directory")
    delivery = ObsidianVaultDelivery(vault_path=blocking_file / "vault")

    with pytest.raises(DeliveryError) as exc_info:
        delivery.deliver(MARKDOWN_BYTES, GENERATED_AT)

    vault_path = blocking_file / "vault"
    assert str(exc_info.value) == (
        f"failed to write to vault at {vault_path}: [Errno 20] Not a directory: '{vault_path}'"
    )


def test_email_delivery_fails_but_obsidian_delivery_still_succeeds(
    tmp_path, failing_smtp_sender
):
    email = EmailDelivery(
        sender=failing_smtp_sender,
        from_addr="me@example.com",
        to_addr="kindle@kindle.com",
    )
    obsidian = ObsidianVaultDelivery(vault_path=tmp_path / "vault")

    results = deliver_to_all(
        {
            "email": (email, EPUB_BYTES),
            "obsidian": (obsidian, MARKDOWN_BYTES),
        },
        GENERATED_AT,
    )

    by_target = {r.target: r for r in results}
    assert by_target["email"].succeeded is False
    assert by_target["email"].error is not None
    assert by_target["obsidian"].succeeded is True
    assert (tmp_path / "vault" / "2026-08-28 1405 News Digest.md").exists()
