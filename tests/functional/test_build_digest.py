from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from news_digest.application.build_digest import build_digest
from news_digest.domain.models import Topic
from news_digest.infrastructure.extraction.trafilatura_extractor import (
    TrafilaturaExtractor,
)
from news_digest.infrastructure.feeds.config import DIRECT_FEEDS
from news_digest.infrastructure.feeds.rss_feed import RssFeedSource

NOW = datetime(2026, 8, 28, 12, 0, 0, tzinfo=UTC)
SINCE = NOW - timedelta(hours=24)


def article_page_html(body: str) -> str:
    return f"<html><body><article><p>{body}</p></article></body></html>"


@pytest.fixture
def canada_and_tech_feeds_with_a_cross_outlet_story(httpx_mock, rss_xml_builder):
    bbc_canada, cbc_canada, gnm_canada = DIRECT_FEEDS[Topic.CANADA]
    bbc_tech, cbc_tech, gnm_tech, *other_tech_feeds = DIRECT_FEEDS[Topic.TECH]

    bbc_story_url = "https://example.com/bbc-trade-story"
    cbc_story_url = "https://example.com/cbc-trade-story"
    tech_story_url = "https://example.com/tech-story"

    httpx_mock.add_response(
        url=bbc_canada.url,
        content=rss_xml_builder(
            [
                {
                    "title": "Canada trade talks collapse",
                    "link": bbc_story_url,
                    "published_at": NOW,
                }
            ]
        ),
    )
    httpx_mock.add_response(
        url=cbc_canada.url,
        content=rss_xml_builder(
            [
                {
                    "title": "Canada-trade talks collapse after deadline",
                    "link": cbc_story_url,
                    "published_at": NOW,
                }
            ]
        ),
    )
    httpx_mock.add_response(url=gnm_canada.url, content=rss_xml_builder([]))

    httpx_mock.add_response(
        url=bbc_tech.url,
        content=rss_xml_builder(
            [
                {
                    "title": "New chip architecture announced",
                    "link": tech_story_url,
                    "published_at": NOW,
                }
            ]
        ),
    )
    httpx_mock.add_response(url=cbc_tech.url, content=rss_xml_builder([]))
    httpx_mock.add_response(url=gnm_tech.url, content=rss_xml_builder([]))
    for feed in other_tech_feeds:
        httpx_mock.add_response(url=feed.url, content=rss_xml_builder([]))

    httpx_mock.add_response(
        url=bbc_story_url,
        text=article_page_html("BBC's coverage of the trade talks collapsing."),
    )
    httpx_mock.add_response(
        url=cbc_story_url,
        text=article_page_html("CBC's coverage of the same trade talks collapsing."),
    )
    httpx_mock.add_response(
        url=tech_story_url,
        text=article_page_html("Details of the new chip architecture announcement."),
    )

    return {"bbc_story_url": bbc_story_url, "cbc_story_url": cbc_story_url}


def test_build_digest_happy_path_covers_multiple_topics_and_groups_cross_outlet_story(
    canada_and_tech_feeds_with_a_cross_outlet_story,
):
    digest = build_digest(
        feed_source=RssFeedSource(),
        extractor=TrafilaturaExtractor(),
        since=SINCE,
        topics=(Topic.CANADA, Topic.TECH),
    )

    assert set(digest.keys()) == {Topic.CANADA, Topic.TECH}

    canada_stories = digest[Topic.CANADA]
    assert len(canada_stories) == 1
    grouped_story = canada_stories[0]
    assert {a.outlet for a in grouped_story.articles} == {"BBC", "CBC"}
    assert all(a.full_text is not None for a in grouped_story.articles)
    assert grouped_story.topic is Topic.CANADA

    tech_stories = digest[Topic.TECH]
    assert len(tech_stories) == 1
    assert tech_stories[0].topic is Topic.TECH
