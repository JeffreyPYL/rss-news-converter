from __future__ import annotations

from datetime import datetime

import pytest

from news_digest.application.ports import ExtractionError


def _rfc822(dt: datetime) -> str:
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")


def _make_rss_xml(items: list[dict]) -> bytes:
    entries = "".join(
        f"""
        <item>
            <title>{item["title"]}</title>
            <link>{item["link"]}</link>
            <description>{item.get("summary", "")}</description>
            <pubDate>{_rfc822(item["published_at"])}</pubDate>
        </item>
        """
        for item in items
    )
    return f"""<?xml version="1.0"?>
    <rss version="2.0"><channel><title>Test Feed</title>{entries}</channel></rss>
    """.encode()


@pytest.fixture
def rss_xml_builder():
    """A minimal valid RSS 2.0 document builder for httpx_mock responses.

    Each item dict needs `title`, `link`, `published_at` (datetime); `summary` is optional.
    """
    return _make_rss_xml


class _AlwaysFailingExtractor:
    """A fake ArticleExtractor that always raises, for graceful-fallback tests."""

    def extract(self, url: str):
        raise ExtractionError(f"simulated extraction failure for {url}")


@pytest.fixture
def always_failing_extractor():
    return _AlwaysFailingExtractor()
