from __future__ import annotations

import subprocess
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from news_digest.application.extraction import enrich_with_full_text
from news_digest.application.ports import ExtractionError
from news_digest.domain.models import Article, Topic
from news_digest.infrastructure._http_client import DEFAULT_USER_AGENT
from news_digest.infrastructure.extraction.defuddle_extractor import DefuddleExtractor
from news_digest.infrastructure.extraction.factory import get_extractor
from news_digest.infrastructure.extraction.trafilatura_extractor import (
    TrafilaturaExtractor,
)

ARTICLE_URL = "https://www.theglobeandmail.com/business/article-example/"

SAMPLE_ARTICLE_HTML = """
<html><head><title>Example story</title></head>
<body>
<article>
<h1>Trade talks resume between Canada and the U.S.</h1>
<img src="https://example.com/photo.jpg" alt="Negotiators at a table">
<p>Negotiators for Canada and the United States resumed trade talks on Tuesday,
according to officials briefed on the meeting who spoke on condition of anonymity
because the discussions are private.</p>
<p>The talks come after weeks of stalled progress on tariff exemptions for
Canadian steel and aluminum exporters.</p>
</article>
</body></html>
"""


def make_article(**overrides) -> Article:
    defaults = {
        "outlet": "Globe and Mail",
        "url": ARTICLE_URL,
        "title": "Trade talks resume",
        "published_at": datetime(2026, 8, 28, 12, 0, 0, tzinfo=UTC),
        "teaser": "A teaser.",
        "topic_candidate": Topic.CANADA,
    }
    defaults.update(overrides)
    return Article(**defaults)


@pytest.fixture
def globe_and_mail_article_page(httpx_mock):
    httpx_mock.add_response(url=ARTICLE_URL, text=SAMPLE_ARTICLE_HTML)


def test_extracting_paywalled_globe_and_mail_article_without_login_succeeds(
    globe_and_mail_article_page,
):
    extractor = TrafilaturaExtractor()

    content = extractor.extract(ARTICLE_URL)

    assert "Negotiators for Canada and the United States" in content.text
    assert "https://example.com/photo.jpg" in content.images


class RecordingExtractFn:
    def __init__(self, result: str | None = "extracted text"):
        self.calls: list[dict] = []
        self._result = result

    def __call__(self, html, **kwargs):
        self.calls.append({"html": html, "kwargs": kwargs})
        return self._result


def test_trafilatura_calls_extract_with_expected_kwargs(globe_and_mail_article_page):
    recording = RecordingExtractFn()
    extractor = TrafilaturaExtractor(extract_fn=recording)

    extractor.extract(ARTICLE_URL)

    assert len(recording.calls) == 1
    assert recording.calls[0]["kwargs"] == {
        "output_format": "markdown",
        "include_images": True,
        "include_links": False,
        "favor_precision": True,
    }
    assert "Trade talks resume between Canada" in recording.calls[0]["html"]


def test_trafilatura_extraction_failure_message_includes_url(httpx_mock):
    httpx_mock.add_exception(httpx.ConnectTimeout("timed out"), url=ARTICLE_URL)
    extractor = TrafilaturaExtractor()

    with pytest.raises(ExtractionError) as exc_info:
        extractor.extract(ARTICLE_URL)

    assert str(exc_info.value).startswith(f"failed to fetch {ARTICLE_URL}:")


def test_trafilatura_no_content_extracted_raises_with_url(globe_and_mail_article_page):
    extractor = TrafilaturaExtractor(extract_fn=RecordingExtractFn(result=None))

    with pytest.raises(ExtractionError) as exc_info:
        extractor.extract(ARTICLE_URL)

    assert str(exc_info.value) == f"no extractable content at {ARTICLE_URL}"


def test_trafilatura_default_client_config():
    extractor = TrafilaturaExtractor()

    assert extractor._client.timeout == httpx.Timeout(15.0)
    assert extractor._client.follow_redirects is True
    assert extractor._client._trust_env is False
    assert extractor._client.headers["user-agent"] == DEFAULT_USER_AGENT


class RecordingRunner:
    """A fake ProcessRunner that records its call and returns canned stdout,
    reading the temp file's actual on-disk content before it's cleaned up."""

    def __init__(self, stdout: str = "# Extracted\n\nBody text."):
        self.calls: list[dict] = []
        self._stdout = stdout

    def __call__(self, args, **kwargs):
        tmp_path = Path(args[4])
        self.calls.append(
            {
                "args": args,
                "kwargs": kwargs,
                "tmp_path_exists": tmp_path.exists(),
                "tmp_path_suffix": tmp_path.suffix,
                "tmp_content": tmp_path.read_text(encoding="utf-8"),
            }
        )
        return subprocess.CompletedProcess(args, returncode=0, stdout=self._stdout)


class FailingRunner:
    def __call__(self, args, **kwargs):
        raise subprocess.CalledProcessError(returncode=1, cmd=args, stderr="boom")


def test_run_defuddle_invokes_expected_command_and_cleans_up_temp_file(
    globe_and_mail_article_page,
):
    recording_runner = RecordingRunner()
    extractor = DefuddleExtractor(runner=recording_runner)

    extractor.extract(ARTICLE_URL)

    assert len(recording_runner.calls) == 1
    call = recording_runner.calls[0]
    args = call["args"]
    assert args[0] == "npx"
    assert args[1] == "--yes"
    assert args[2] == "defuddle"
    assert args[3] == "parse"
    assert args[5] == "--markdown"
    assert call["tmp_path_suffix"] == ".html"
    assert "Trade talks resume between Canada" in call["tmp_content"]
    assert call["kwargs"] == {
        "capture_output": True,
        "text": True,
        "timeout": 30,
        "check": True,
    }
    # cleaned up (`finally: tmp_path.unlink(missing_ok=True)`) after the call returns
    assert not Path(args[4]).exists()


def test_defuddle_extract_uses_runners_returned_stdout_and_extracts_images(
    globe_and_mail_article_page,
):
    stdout = "# A Title\n\n![alt](https://example.com/photo.jpg)\n\nSome body."
    extractor = DefuddleExtractor(runner=RecordingRunner(stdout=stdout))

    content = extractor.extract(ARTICLE_URL)

    assert content.text == stdout
    assert content.images == ("https://example.com/photo.jpg",)


def test_defuddle_fetch_failure_message_includes_url(httpx_mock):
    httpx_mock.add_exception(httpx.ConnectTimeout("timed out"), url=ARTICLE_URL)
    extractor = DefuddleExtractor(runner=RecordingRunner())

    with pytest.raises(ExtractionError) as exc_info:
        extractor.extract(ARTICLE_URL)

    assert str(exc_info.value).startswith(f"failed to fetch {ARTICLE_URL}:")


class SelfDeletingRunner:
    """Simulates defuddle itself having consumed/removed the temp file —
    proves cleanup uses `missing_ok=True` rather than assuming it's still there."""

    def __call__(self, args, **kwargs):
        tmp_path = Path(args[4])
        tmp_path.unlink()
        return subprocess.CompletedProcess(args, returncode=0, stdout="# Text")


def test_run_defuddle_cleanup_does_not_raise_if_the_temp_file_is_already_gone(
    globe_and_mail_article_page,
):
    extractor = DefuddleExtractor(runner=SelfDeletingRunner())

    content = extractor.extract(ARTICLE_URL)

    assert content.text == "# Text"


def test_defuddle_empty_stdout_raises_with_url(globe_and_mail_article_page):
    extractor = DefuddleExtractor(runner=RecordingRunner(stdout="   "))

    with pytest.raises(ExtractionError) as exc_info:
        extractor.extract(ARTICLE_URL)

    assert str(exc_info.value) == f"no extractable content at {ARTICLE_URL}"


def test_defuddle_subprocess_failure_wraps_in_extraction_error_with_url(
    globe_and_mail_article_page,
):
    extractor = DefuddleExtractor(runner=FailingRunner())

    with pytest.raises(ExtractionError) as exc_info:
        extractor.extract(ARTICLE_URL)

    assert str(exc_info.value).startswith(f"defuddle failed for {ARTICLE_URL}:")


def test_defuddle_default_client_config():
    extractor = DefuddleExtractor()

    assert extractor._client.timeout == httpx.Timeout(15.0)
    assert extractor._client.follow_redirects is True
    assert extractor._client._trust_env is False
    assert extractor._client.headers["user-agent"] == DEFAULT_USER_AGENT


def test_switching_extractor_config_selects_defuddle_without_touching_other_stages(
    monkeypatch,
):
    monkeypatch.setenv("NEWS_DIGEST_EXTRACTOR", "defuddle")

    extractor = get_extractor()

    assert isinstance(extractor, DefuddleExtractor)


def test_get_extractor_defaults_to_trafilatura_when_unset(monkeypatch):
    monkeypatch.delenv("NEWS_DIGEST_EXTRACTOR", raising=False)

    extractor = get_extractor()

    assert isinstance(extractor, TrafilaturaExtractor)


def test_get_extractor_unknown_name_raises_with_choices(monkeypatch):
    monkeypatch.delenv("NEWS_DIGEST_EXTRACTOR", raising=False)

    with pytest.raises(ValueError) as exc_info:
        get_extractor("not-a-real-extractor")

    assert str(exc_info.value) == (
        "unknown extractor: 'not-a-real-extractor' (choices: ['defuddle', 'trafilatura'])"
    )


@pytest.mark.integration
def test_defuddle_extracts_the_same_article(globe_and_mail_article_page):
    extractor = DefuddleExtractor()

    content = extractor.extract(ARTICLE_URL)

    assert "Negotiators for Canada and the United States" in content.text


def test_enrich_with_full_text_sets_both_text_and_images(globe_and_mail_article_page):
    article = make_article()

    enriched = enrich_with_full_text(article, TrafilaturaExtractor())

    assert enriched.extraction_failed is False
    assert "Negotiators for Canada and the United States" in enriched.full_text
    assert enriched.images == ("https://example.com/photo.jpg",)


def test_hard_gated_article_falls_back_to_teaser_and_link(always_failing_extractor):
    article = make_article()

    enriched = enrich_with_full_text(article, always_failing_extractor)

    assert enriched.extraction_failed is True
    assert enriched.full_text is None
    assert enriched.title == article.title
    assert enriched.teaser == article.teaser
    assert enriched.url == article.url
