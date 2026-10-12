from __future__ import annotations

import argparse
import re
import zipfile
from datetime import UTC, datetime, timedelta
from io import BytesIO

import pytest

from news_digest.cli import _build_arg_parser, parse_since_duration, run_digest
from news_digest.domain.models import Topic
from news_digest.infrastructure.delivery.email_delivery import EmailDelivery
from news_digest.infrastructure.delivery.obsidian_vault_delivery import (
    ObsidianVaultDelivery,
)
from news_digest.infrastructure.extraction.trafilatura_extractor import (
    TrafilaturaExtractor,
)
from news_digest.infrastructure.feeds.config import DIRECT_FEEDS, KEYWORD_FILTERED_FEEDS
from news_digest.infrastructure.feeds.rss_feed import RssFeedSource
from news_digest.infrastructure.state.run_state import RunState

NOW = datetime(2026, 8, 28, 12, 0, 0, tzinfo=UTC)


class RecordingSmtpSender:
    def __init__(self):
        self.sent = []

    def send(self, message):
        self.sent.append(message)


@pytest.fixture
def all_feeds_empty_except_one_canada_story(httpx_mock, rss_xml_builder):
    story_url = "https://example.com/story"
    bbc_canada_url = DIRECT_FEEDS[Topic.CANADA][
        0
    ].url  # also reused by Ottawa's keyword filter

    # Every configured feed URL, deduplicated (some URLs are reused across
    # topics — e.g. Ottawa's keyword filter reuses Canada's BBC feed) — each
    # registered `is_reusable=True` so it serves however many topics request it.
    all_urls = {
        feed.url
        for feeds in (*DIRECT_FEEDS.values(), *KEYWORD_FILTERED_FEEDS.values())
        for feed in feeds
    }
    for url in all_urls:
        if url == bbc_canada_url:
            continue
        httpx_mock.add_response(url=url, content=rss_xml_builder([]), is_reusable=True)

    httpx_mock.add_response(
        url=bbc_canada_url,
        content=rss_xml_builder(
            [
                {
                    "title": "Ottawa announces new funding",
                    "link": story_url,
                    "published_at": NOW,
                }
            ]
        ),
        is_reusable=True,
    )
    httpx_mock.add_response(
        url=story_url,
        text="<html><body><article><p>Details of the funding announcement.</p></article></body></html>",
        is_reusable=True,
    )
    return story_url


def test_run_digest_delivers_to_email_obsidian_and_the_epub_copy(
    tmp_path, all_feeds_empty_except_one_canada_story
):
    state = RunState(tmp_path / "state.json")
    state.record_success(at=NOW - timedelta(hours=1))
    recording_sender = RecordingSmtpSender()
    email_delivery = EmailDelivery(
        sender=recording_sender, from_addr="me@example.com", to_addr="kindle@kindle.com"
    )
    obsidian_delivery = ObsidianVaultDelivery(vault_path=tmp_path / "vault")
    epub_copy_delivery = ObsidianVaultDelivery(
        vault_path=tmp_path / "vault", note_filename="digest.epub"
    )

    exit_code = run_digest(
        feed_source=RssFeedSource(),
        extractor=TrafilaturaExtractor(),
        state=state,
        email_delivery=email_delivery,
        obsidian_delivery=obsidian_delivery,
        epub_copy_delivery=epub_copy_delivery,
    )

    assert exit_code == 0
    assert len(recording_sender.sent) == 1
    attachment = next(recording_sender.sent[0].iter_attachments())
    with zipfile.ZipFile(BytesIO(attachment.get_content())) as archive:
        chapter_html = "".join(
            archive.read(name).decode()
            for name in archive.namelist()
            if name.endswith(".xhtml") and name != "EPUB/nav.xhtml"
        )
    assert "Ottawa announces new funding" in chapter_html

    vault_files = {f.name: f for f in (tmp_path / "vault").iterdir()}
    assert len(vault_files) == 2
    # cli.run_digest stamps the real generation time (not mocked here), so
    # only the filename shape — date prefix, then time with no seconds — and
    # the fixed suffix can be asserted, not an exact timestamp.
    note_name = next(n for n in vault_files if n.endswith("News Digest.md"))
    epub_name = next(n for n in vault_files if n.endswith("digest.epub"))
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{4} News Digest\.md", note_name)
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{4} digest\.epub", epub_name)
    # Both files come from the same run, so they share the exact same
    # timestamp — not just the same shape.
    assert note_name.removesuffix("News Digest.md") == epub_name.removesuffix(
        "digest.epub"
    )
    assert "Ottawa announces new funding" in vault_files[note_name].read_text()
    assert vault_files[epub_name].read_bytes() == attachment.get_content()
    assert state.last_success() is not None


class EmptyFeedSource:
    def __init__(self):
        self.skipped = []

    def fetch_topic(self, topic, since):
        return []


class FakeExtractor:
    def extract(self, url):
        from news_digest.application.ports import ExtractedContent

        return ExtractedContent(text="Full text.", images=())


class FailingDelivery:
    def deliver(self, rendered, generated_at):
        from news_digest.application.ports import DeliveryError

        raise DeliveryError("simulated failure")


class RecordingDelivery:
    def __init__(self):
        self.delivered = []
        self.generated_at_calls = []

    def deliver(self, rendered, generated_at):
        self.delivered.append(rendered)
        self.generated_at_calls.append(generated_at)


def test_run_digest_with_no_targets_configured_reports_failure(tmp_path, capsys):
    state = RunState(tmp_path / "state.json")
    state.record_success(at=NOW - timedelta(hours=1))

    exit_code = run_digest(
        feed_source=EmptyFeedSource(),
        extractor=TrafilaturaExtractor(),
        state=state,
        email_delivery=None,
        obsidian_delivery=None,
    )

    assert exit_code == 1
    assert capsys.readouterr().out == "No delivery targets configured.\n"


def test_run_digest_with_a_feed_source_lacking_a_skipped_attribute_does_not_crash(
    tmp_path,
):
    class BareFeedSource:
        def fetch_topic(self, topic, since):
            return []

    state = RunState(tmp_path / "state.json")

    exit_code = run_digest(
        feed_source=BareFeedSource(),
        extractor=TrafilaturaExtractor(),
        state=state,
        email_delivery=RecordingDelivery(),
        obsidian_delivery=None,
    )

    assert exit_code == 0


def test_run_digest_stamps_delivery_with_a_timezone_aware_utc_generated_at(tmp_path):
    obsidian = RecordingDelivery()
    state = RunState(tmp_path / "state.json")

    run_digest(
        feed_source=EmptyFeedSource(),
        extractor=FakeExtractor(),
        state=state,
        email_delivery=None,
        obsidian_delivery=obsidian,
    )

    assert len(obsidian.generated_at_calls) == 1
    assert obsidian.generated_at_calls[0].tzinfo is UTC


def test_run_digest_delivers_to_extra_epub_targets_by_name(tmp_path, capsys):
    state = RunState(tmp_path / "state.json")
    extra = RecordingDelivery()

    exit_code = run_digest(
        feed_source=EmptyFeedSource(),
        extractor=FakeExtractor(),
        state=state,
        email_delivery=None,
        obsidian_delivery=None,
        extra_epub_targets={"google_drive": extra},
    )

    assert exit_code == 0
    assert "Delivered to google_drive.\n" in capsys.readouterr().out
    assert len(extra.delivered) == 1


def test_run_digest_without_extra_epub_targets_behaves_as_before(tmp_path):
    state = RunState(tmp_path / "state.json")
    obsidian = RecordingDelivery()

    exit_code = run_digest(
        feed_source=EmptyFeedSource(),
        extractor=FakeExtractor(),
        state=state,
        email_delivery=None,
        obsidian_delivery=obsidian,
    )

    assert exit_code == 0
    assert len(obsidian.delivered) == 1


def test_run_digest_reports_skipped_sources_exactly(tmp_path, capsys):
    from news_digest.infrastructure.feeds.rss_feed import SkippedSource

    feed_source = EmptyFeedSource()
    feed_source.skipped = [
        SkippedSource(
            outlet="BBC", url="https://example.com/feed.xml", reason="timed out"
        )
    ]
    state = RunState(tmp_path / "state.json")

    run_digest(
        feed_source=feed_source,
        extractor=FakeExtractor(),
        state=state,
        email_delivery=RecordingDelivery(),
        obsidian_delivery=None,
    )

    out = capsys.readouterr().out
    assert "Sources skipped this run:\n" in out
    assert "  - BBC (https://example.com/feed.xml): timed out\n" in out


def test_run_digest_all_targets_failing_returns_1_and_does_not_record_success(tmp_path):
    state = RunState(tmp_path / "state.json")

    exit_code = run_digest(
        feed_source=EmptyFeedSource(),
        extractor=FakeExtractor(),
        state=state,
        email_delivery=FailingDelivery(),
        obsidian_delivery=FailingDelivery(),
    )

    assert exit_code == 1
    assert state.last_success() is None


def test_run_digest_reports_the_epub_copy_target_by_name(tmp_path, capsys):
    state = RunState(tmp_path / "state.json")

    exit_code = run_digest(
        feed_source=EmptyFeedSource(),
        extractor=FakeExtractor(),
        state=state,
        email_delivery=None,
        obsidian_delivery=None,
        epub_copy_delivery=RecordingDelivery(),
    )

    assert exit_code == 0
    assert "Delivered to epub_copy.\n" in capsys.readouterr().out


def test_run_digest_one_of_two_targets_failing_still_succeeds_overall(tmp_path, capsys):
    state = RunState(tmp_path / "state.json")
    obsidian = RecordingDelivery()

    exit_code = run_digest(
        feed_source=EmptyFeedSource(),
        extractor=FakeExtractor(),
        state=state,
        email_delivery=FailingDelivery(),
        obsidian_delivery=obsidian,
    )

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "Delivery to email failed: simulated failure\n" in out
    assert "Delivered to obsidian.\n" in out
    assert len(obsidian.delivered) == 1
    assert state.last_success() is not None


def test_parse_since_duration_supports_days_and_hours():
    assert parse_since_duration("3d") == timedelta(days=3)
    assert parse_since_duration("48h") == timedelta(hours=48)


def test_parse_since_duration_rejects_malformed_value():
    with pytest.raises(argparse.ArgumentTypeError):
        parse_since_duration("3x")


def test_parse_since_duration_error_message_names_the_bad_value():
    with pytest.raises(
        argparse.ArgumentTypeError, match=r"invalid --since duration 'abc'"
    ):
        parse_since_duration("abc")


def test_since_argument_rejects_invalid_duration_before_pipeline_setup():
    parser = _build_arg_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--since", "3x"])

    assert exc_info.value.code != 0


def test_since_argument_parses_a_valid_duration():
    parser = _build_arg_parser()

    args = parser.parse_args(["--since", "3d"])

    assert args.since == timedelta(days=3)


def test_arg_parser_describes_itself_and_the_since_flag():
    parser = _build_arg_parser()

    assert parser.description == "Run the news digest pipeline."
    since_action = next(a for a in parser._actions if "--since" in a.option_strings)
    assert since_action.option_strings == ["--since"]
    assert since_action.help == (
        "Override the lookback window with a relative duration, e.g. "
        "'3d' or '48h' (default: since the last successful run)"
    )


class RecordingFeedSource:
    def __init__(self):
        self.skipped = []
        self.since_calls = []

    def fetch_topic(self, topic, since):
        self.since_calls.append(since)
        return []


def test_run_digest_since_override_bypasses_state_lookback(tmp_path):
    state = RunState(tmp_path / "state.json")
    state.record_success(at=NOW - timedelta(hours=1))
    override = NOW - timedelta(days=3)
    feed_source = RecordingFeedSource()

    exit_code = run_digest(
        feed_source=feed_source,
        extractor=FakeExtractor(),
        state=state,
        email_delivery=None,
        obsidian_delivery=RecordingDelivery(),
        since_override=override,
    )

    assert exit_code == 0
    assert feed_source.since_calls
    assert all(call == override for call in feed_source.since_calls)


def test_run_digest_without_since_override_uses_state_lookback(tmp_path):
    state = RunState(tmp_path / "state.json")
    recorded_at = NOW - timedelta(hours=5)
    state.record_success(at=recorded_at)
    feed_source = RecordingFeedSource()

    run_digest(
        feed_source=feed_source,
        extractor=FakeExtractor(),
        state=state,
        email_delivery=None,
        obsidian_delivery=RecordingDelivery(),
    )

    assert feed_source.since_calls
    assert all(call == recorded_at for call in feed_source.since_calls)


def test_run_digest_since_override_still_records_success(tmp_path):
    state = RunState(tmp_path / "state.json")
    override = NOW - timedelta(days=3)

    exit_code = run_digest(
        feed_source=EmptyFeedSource(),
        extractor=FakeExtractor(),
        state=state,
        email_delivery=None,
        obsidian_delivery=RecordingDelivery(),
        since_override=override,
    )

    assert exit_code == 0
    recorded = state.last_success()
    assert recorded is not None
    assert recorded != override
