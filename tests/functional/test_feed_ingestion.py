from __future__ import annotations

import json
import time
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from news_digest.domain.models import Topic
from news_digest.infrastructure._http_client import DEFAULT_USER_AGENT
from news_digest.infrastructure.feeds.config import (
    DIRECT_FEEDS,
    KEYWORD_FILTERED_FEEDS,
    load_feeds,
)
from news_digest.infrastructure.feeds.rss_feed import (
    DEFAULT_TIMEOUT_SECONDS,
    RssFeedSource,
    _parse_published,
)

NOW = datetime(2026, 8, 28, 12, 0, 0, tzinfo=UTC)
SINCE = NOW - timedelta(hours=24)


def rfc822(dt: datetime) -> str:
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")


@pytest.fixture
def canada_topic_feeds(httpx_mock, rss_xml_builder):
    for feed in DIRECT_FEEDS[Topic.CANADA]:
        httpx_mock.add_response(
            url=feed.url,
            content=rss_xml_builder(
                [
                    {
                        "title": f"{feed.outlet} Canada story",
                        "link": f"{feed.url}#story",
                        "published_at": NOW,
                    }
                ]
            ),
        )


@pytest.fixture
def hong_kong_topic_feeds(httpx_mock, rss_xml_builder):
    for feed in DIRECT_FEEDS[Topic.HONG_KONG]:
        httpx_mock.add_response(
            url=feed.url,
            content=rss_xml_builder(
                [
                    {
                        "title": f"{feed.outlet} HK story",
                        "link": f"{feed.url}#story",
                        "published_at": NOW,
                    }
                ]
            ),
        )
    for feed in KEYWORD_FILTERED_FEEDS[Topic.HONG_KONG]:
        httpx_mock.add_response(
            url=feed.url,
            content=rss_xml_builder(
                [
                    {
                        "title": "Hong Kong protests update",
                        "link": f"{feed.url}#hk",
                        "published_at": NOW,
                    },
                    {
                        "title": "Unrelated story about Japan",
                        "link": f"{feed.url}#other",
                        "published_at": NOW,
                    },
                ]
            ),
        )


@pytest.fixture
def canada_feeds_with_one_broken(httpx_mock, rss_xml_builder):
    feeds = DIRECT_FEEDS[Topic.CANADA]
    httpx_mock.add_exception(httpx.ConnectTimeout("timed out"), url=feeds[0].url)
    for feed in feeds[1:]:
        httpx_mock.add_response(
            url=feed.url,
            content=rss_xml_builder(
                [
                    {
                        "title": f"{feed.outlet} story",
                        "link": f"{feed.url}#story",
                        "published_at": NOW,
                    }
                ]
            ),
        )
    return feeds[0]


def test_fetching_canada_topic_pulls_from_all_its_configured_feeds(canada_topic_feeds):
    source = RssFeedSource()

    articles = source.fetch_topic(Topic.CANADA, since=SINCE)

    assert {a.outlet for a in articles} == {
        f.outlet for f in DIRECT_FEEDS[Topic.CANADA]
    }
    assert all(a.topic_candidate is Topic.CANADA for a in articles)
    assert all(a.published_at == NOW for a in articles)


def test_hong_kong_ingestion_draws_from_all_five_source_types(hong_kong_topic_feeds):
    source = RssFeedSource()

    articles = source.fetch_topic(Topic.HONG_KONG, since=SINCE)

    expected_outlets = {f.outlet for f in DIRECT_FEEDS[Topic.HONG_KONG]} | {
        f.outlet for f in KEYWORD_FILTERED_FEEDS[Topic.HONG_KONG]
    }
    assert {a.outlet for a in articles} == expected_outlets
    assert all("Unrelated" not in a.title for a in articles)


def _rss_with_raw_items(items_xml: str) -> bytes:
    return f"""<?xml version="1.0"?>
    <rss version="2.0"><channel><title>Test Feed</title>{items_xml}</channel></rss>
    """.encode()


@pytest.fixture
def canada_bbc_feed_with_edge_case_items(httpx_mock):
    bbc_url = DIRECT_FEEDS[Topic.CANADA][0].url
    old = rfc822(NOW - timedelta(hours=100))
    boundary = rfc822(SINCE)
    recent = rfc822(NOW)
    items_xml = f"""
        <item><title>Old story, before the window</title><link>https://example.com/old</link><pubDate>{old}</pubDate></item>
        <item><title>No date story</title><link>https://example.com/nodate</link></item>
        <item><title>Boundary story</title><link>https://example.com/boundary</link><pubDate>{boundary}</pubDate></item>
        <item><title>Valid recent story</title><link>https://example.com/recent</link><pubDate>{recent}</pubDate></item>
    """
    httpx_mock.add_response(url=bbc_url, content=_rss_with_raw_items(items_xml))
    for feed in DIRECT_FEEDS[Topic.CANADA][1:]:
        httpx_mock.add_response(url=feed.url, content=_rss_with_raw_items(""))


def test_date_filtering_handles_boundary_missing_date_and_keeps_scanning(
    canada_bbc_feed_with_edge_case_items,
):
    source = RssFeedSource()

    articles = source.fetch_topic(Topic.CANADA, since=SINCE)

    titles = {a.title for a in articles}
    # "No date story" (would crash under an and-mutation instead of filtering
    # out) and "Old story" are excluded; "Boundary story" at exactly `since`
    # is included (proves `<` not `<=`); "Valid recent story" after it proves
    # the loop kept scanning rather than stopping (continue, not break).
    assert titles == {"Boundary story", "Valid recent story"}


@pytest.fixture
def canada_bbc_feed_missing_optional_fields(httpx_mock):
    bbc_url = DIRECT_FEEDS[Topic.CANADA][0].url
    items_xml = f"<item><pubDate>{rfc822(NOW)}</pubDate></item>"
    httpx_mock.add_response(url=bbc_url, content=_rss_with_raw_items(items_xml))
    for feed in DIRECT_FEEDS[Topic.CANADA][1:]:
        httpx_mock.add_response(url=feed.url, content=_rss_with_raw_items(""))


def test_missing_title_link_and_summary_default_to_empty_strings(
    canada_bbc_feed_missing_optional_fields,
):
    source = RssFeedSource()

    articles = source.fetch_topic(Topic.CANADA, since=SINCE)

    assert len(articles) == 1
    assert articles[0].title == ""
    assert articles[0].url == ""
    assert articles[0].teaser == ""


@pytest.fixture
def ottawa_bbc_feed_with_keyword_only_in_summary(httpx_mock):
    bbc_url = KEYWORD_FILTERED_FEEDS[Topic.OTTAWA][0].url
    items_xml = (
        f"<item><title>City council votes on transit</title>"
        f"<description>The vote took place in Ottawa on Tuesday.</description>"
        f"<link>https://example.com/ottawa-story</link><pubDate>{rfc822(NOW)}</pubDate></item>"
    )
    httpx_mock.add_response(url=bbc_url, content=_rss_with_raw_items(items_xml))
    httpx_mock.add_response(
        url=DIRECT_FEEDS[Topic.OTTAWA][0].url, content=_rss_with_raw_items("")
    )
    httpx_mock.add_response(
        url=KEYWORD_FILTERED_FEEDS[Topic.OTTAWA][1].url, content=_rss_with_raw_items("")
    )


def test_keyword_matching_checks_summary_as_well_as_title(
    ottawa_bbc_feed_with_keyword_only_in_summary,
):
    source = RssFeedSource()

    articles = source.fetch_topic(Topic.OTTAWA, since=SINCE)

    assert any(a.title == "City council votes on transit" for a in articles)


@pytest.fixture
def ottawa_bbc_feed_with_a_non_matching_item_before_a_matching_one(httpx_mock):
    bbc_url = KEYWORD_FILTERED_FEEDS[Topic.OTTAWA][0].url
    items_xml = (
        f"<item><title>Unrelated story about weather</title>"
        f"<description>Nothing relevant here.</description>"
        f"<link>https://example.com/unrelated</link><pubDate>{rfc822(NOW)}</pubDate></item>"
        f"<item><title>Ottawa transit vote</title>"
        f"<description>City council update.</description>"
        f"<link>https://example.com/ottawa</link><pubDate>{rfc822(NOW)}</pubDate></item>"
    )
    httpx_mock.add_response(url=bbc_url, content=_rss_with_raw_items(items_xml))
    httpx_mock.add_response(
        url=DIRECT_FEEDS[Topic.OTTAWA][0].url, content=_rss_with_raw_items("")
    )
    httpx_mock.add_response(
        url=KEYWORD_FILTERED_FEEDS[Topic.OTTAWA][1].url, content=_rss_with_raw_items("")
    )


def test_keyword_mismatch_skips_that_item_but_keeps_scanning_later_ones(
    ottawa_bbc_feed_with_a_non_matching_item_before_a_matching_one,
):
    source = RssFeedSource()

    articles = source.fetch_topic(Topic.OTTAWA, since=SINCE)

    titles = {a.title for a in articles}
    assert "Unrelated story about weather" not in titles
    assert "Ottawa transit vote" in titles


def test_parse_published_uses_published_parsed_when_present():
    st = time.struct_time((2026, 8, 28, 12, 0, 0, 4, 240, 0))

    assert _parse_published({"published_parsed": st}) == datetime(
        2026, 8, 28, 12, 0, 0, tzinfo=UTC
    )


def test_parse_published_falls_back_to_updated_parsed():
    st = time.struct_time((2020, 1, 1, 0, 0, 0, 2, 1, 0))

    assert _parse_published({"updated_parsed": st}) == datetime(
        2020, 1, 1, 0, 0, 0, tzinfo=UTC
    )


def test_parse_published_returns_none_when_neither_field_present():
    assert _parse_published({}) is None


def test_parse_published_does_not_leak_weekday_into_microseconds():
    st = time.struct_time((2026, 8, 28, 12, 0, 0, 5, 240, 0))  # weekday=5

    result = _parse_published({"published_parsed": st})

    assert result.microsecond == 0


def test_default_client_has_expected_timeout_follows_redirects_and_does_not_trust_env():
    source = RssFeedSource()

    assert source._client.timeout == httpx.Timeout(DEFAULT_TIMEOUT_SECONDS)
    assert source._client.follow_redirects is True
    assert source._client._trust_env is False
    assert source._client.headers["user-agent"] == DEFAULT_USER_AGENT


def test_a_feed_without_its_own_timeout_uses_the_client_default(
    canada_topic_feeds, httpx_mock
):
    source = RssFeedSource()

    source.fetch_topic(Topic.CANADA, since=SINCE)

    request = httpx_mock.get_requests(url=DIRECT_FEEDS[Topic.CANADA][0].url)[0]
    assert request.extensions["timeout"] == {
        "connect": DEFAULT_TIMEOUT_SECONDS,
        "read": DEFAULT_TIMEOUT_SECONDS,
        "write": DEFAULT_TIMEOUT_SECONDS,
        "pool": DEFAULT_TIMEOUT_SECONDS,
    }


def test_a_feeds_own_timeout_overrides_the_client_default(
    monkeypatch, tmp_path, httpx_mock, rss_xml_builder
):
    feeds_file = tmp_path / "custom_feeds.json"
    slow_url = "https://example.com/slow-feed.xml"
    feeds_file.write_text(
        json.dumps(
            {"tech": {"direct": [{"outlet": "Slow", "url": slow_url, "timeout": 30}]}}
        )
    )
    monkeypatch.setenv("NEWS_DIGEST_FEEDS_CONFIG_PATH", str(feeds_file))
    httpx_mock.add_response(url=slow_url, content=rss_xml_builder([]))

    source = RssFeedSource()
    source.fetch_topic(Topic.TECH, since=SINCE)

    request = httpx_mock.get_requests(url=slow_url)[0]
    assert request.extensions["timeout"] == {
        "connect": 30.0,
        "read": 30.0,
        "write": 30.0,
        "pool": 30.0,
    }


def test_load_feeds_is_exhaustive_over_topic_and_parses_both_feed_kinds(tmp_path):
    feeds_file = tmp_path / "feeds.json"
    feeds_file.write_text(
        json.dumps(
            {
                "canada": {
                    "direct": [{"outlet": "BBC", "url": "https://example.com/bbc.xml"}],
                    "keyword_filtered": [
                        {
                            "outlet": "CBC",
                            "url": "https://example.com/cbc.xml",
                            "keywords": ["ottawa"],
                        }
                    ],
                }
            }
        )
    )

    direct_feeds, keyword_filtered_feeds = load_feeds(feeds_file)

    assert set(direct_feeds) == set(Topic)
    assert set(keyword_filtered_feeds) == set(Topic)
    assert direct_feeds[Topic.CANADA][0].outlet == "BBC"
    assert keyword_filtered_feeds[Topic.CANADA][0].keywords == ("ottawa",)
    assert direct_feeds[Topic.TECH] == []
    assert keyword_filtered_feeds[Topic.TECH] == []


def test_feeds_config_path_setting_overrides_the_default_feed_list(
    monkeypatch, tmp_path, httpx_mock, rss_xml_builder
):
    feeds_file = tmp_path / "custom_feeds.json"
    custom_url = "https://example.com/custom-feed.xml"
    feeds_file.write_text(
        json.dumps({"canada": {"direct": [{"outlet": "Custom", "url": custom_url}]}})
    )
    monkeypatch.setenv("NEWS_DIGEST_FEEDS_CONFIG_PATH", str(feeds_file))
    httpx_mock.add_response(
        url=custom_url,
        content=rss_xml_builder(
            [
                {
                    "title": "Custom outlet story",
                    "link": "https://example.com/story",
                    "published_at": NOW,
                }
            ]
        ),
    )

    source = RssFeedSource()
    articles = source.fetch_topic(Topic.CANADA, since=SINCE)

    assert {a.outlet for a in articles} == {"Custom"}


def test_a_feeds_own_cap_is_carried_onto_its_fetched_articles(
    monkeypatch, tmp_path, httpx_mock, rss_xml_builder
):
    feeds_file = tmp_path / "custom_feeds.json"
    capped_url = "https://example.com/capped-feed.xml"
    uncapped_url = "https://example.com/uncapped-feed.xml"
    feeds_file.write_text(
        json.dumps(
            {
                "tech": {
                    "direct": [
                        {"outlet": "The Verge", "url": capped_url, "cap": 20},
                        {"outlet": "BBC", "url": uncapped_url},
                    ]
                }
            }
        )
    )
    monkeypatch.setenv("NEWS_DIGEST_FEEDS_CONFIG_PATH", str(feeds_file))
    httpx_mock.add_response(
        url=capped_url,
        content=rss_xml_builder(
            [
                {
                    "title": "Verge story",
                    "link": "https://example.com/verge",
                    "published_at": NOW,
                }
            ]
        ),
    )
    httpx_mock.add_response(
        url=uncapped_url,
        content=rss_xml_builder(
            [
                {
                    "title": "BBC story",
                    "link": "https://example.com/bbc",
                    "published_at": NOW,
                }
            ]
        ),
    )

    source = RssFeedSource()
    articles = source.fetch_topic(Topic.TECH, since=SINCE)

    by_outlet = {a.outlet: a for a in articles}
    assert by_outlet["The Verge"].outlet_cap == 20
    assert by_outlet["BBC"].outlet_cap is None


def test_one_broken_feed_doesnt_block_the_rest(canada_feeds_with_one_broken):
    broken_feed = canada_feeds_with_one_broken
    source = RssFeedSource()

    articles = source.fetch_topic(Topic.CANADA, since=SINCE)

    remaining_outlets = {
        f.outlet for f in DIRECT_FEEDS[Topic.CANADA] if f.outlet != broken_feed.outlet
    }
    assert {a.outlet for a in articles} == remaining_outlets
    assert len(source.skipped) == 1
    assert source.skipped[0].outlet == broken_feed.outlet
    assert source.skipped[0].url == broken_feed.url
    assert "timed out" in source.skipped[0].reason
