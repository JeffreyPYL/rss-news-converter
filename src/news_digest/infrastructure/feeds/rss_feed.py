from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

import feedparser
import httpx
from pydantic import BaseModel, ConfigDict

from news_digest.domain.models import Article, Topic
from news_digest.infrastructure._http_client import DEFAULT_USER_AGENT
from news_digest.infrastructure.settings import Settings

from .config import (
    DIRECT_FEEDS,
    KEYWORD_FILTERED_FEEDS,
    DirectFeed,
    KeywordFilteredFeed,
    load_feeds,
)

Feed = DirectFeed | KeywordFilteredFeed

# feed-ingestion: sensible default request timeout — a feed can override this
# via its own `timeout` in feeds.json (DirectFeed.timeout/KeywordFilteredFeed.timeout).
DEFAULT_TIMEOUT_SECONDS = 15.0

# feed-ingestion: a topic's feeds are fetched concurrently (each is an
# independent network call) — httpx.Client is safe to share across threads.
DEFAULT_MAX_WORKERS = 8


class SkippedSource(BaseModel):
    model_config = ConfigDict(frozen=True)

    outlet: str
    url: str
    reason: str


class RssFeedSource:
    """Fetches and normalizes candidate articles for a topic from all its configured feeds.

    feed-ingestion: a source that errors or times out is skipped rather than
    failing the whole run; skipped sources are collected on `.skipped`.
    """

    def __init__(
        self,
        client: httpx.Client | None = None,
        max_workers: int = DEFAULT_MAX_WORKERS,
    ) -> None:
        self._client = client or httpx.Client(
            timeout=DEFAULT_TIMEOUT_SECONDS,
            follow_redirects=True,
            trust_env=False,
            headers={"User-Agent": DEFAULT_USER_AGENT},
        )
        self._max_workers = max_workers
        feeds_config_path = Settings().feeds_config_path
        if feeds_config_path is not None:
            self._direct_feeds, self._keyword_filtered_feeds = load_feeds(
                feeds_config_path
            )
        else:
            self._direct_feeds, self._keyword_filtered_feeds = (
                DIRECT_FEEDS,
                KEYWORD_FILTERED_FEEDS,
            )
        self.skipped: list[SkippedSource] = []

    def fetch_topic(self, topic: Topic, since: datetime) -> list[Article]:
        feeds: list[Feed] = [
            *self._direct_feeds[topic],
            *self._keyword_filtered_feeds[topic],
        ]
        if not feeds:
            return []

        articles: list[Article] = []
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            futures = [
                executor.submit(self._fetch_one, feed, topic, since) for feed in feeds
            ]
            for feed, future in zip(feeds, futures, strict=True):
                try:
                    articles.extend(future.result())
                except httpx.HTTPError as exc:
                    self.skipped.append(
                        SkippedSource(outlet=feed.outlet, url=feed.url, reason=str(exc))
                    )
        return articles

    def _fetch_one(self, feed: Feed, topic: Topic, since: datetime) -> list[Article]:
        # Omit the kwarg entirely rather than pass timeout=None — httpx treats
        # an explicit None as "no timeout at all", not "use the client default".
        request_kwargs = {} if feed.timeout is None else {"timeout": feed.timeout}
        response = self._client.get(feed.url, **request_kwargs)
        response.raise_for_status()
        parsed = feedparser.parse(response.content)

        keywords: tuple[str, ...] = getattr(feed, "keywords", ())
        articles: list[Article] = []
        for entry in parsed.entries:
            published = _parse_published(entry)
            if published is None or published < since:
                continue

            title = entry.get("title", "")
            summary = entry.get("summary", "")
            if keywords and not _matches_keywords(title, summary, keywords):
                continue

            articles.append(
                Article(
                    outlet=feed.outlet,
                    url=entry.get("link", ""),
                    title=title,
                    published_at=published,
                    teaser=summary,
                    topic_candidate=topic,
                    outlet_cap=feed.cap,
                )
            )
        return articles


def _matches_keywords(title: str, summary: str, keywords: tuple[str, ...]) -> bool:
    haystack = f"{title} {summary}".lower()
    return any(keyword in haystack for keyword in keywords)


def _parse_published(entry: dict) -> datetime | None:
    parsed_time = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed_time is None:
        return None
    return datetime(*parsed_time[:6], tzinfo=UTC)
