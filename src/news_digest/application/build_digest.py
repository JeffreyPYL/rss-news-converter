from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from functools import partial

from news_digest.application.extraction import enrich_with_full_text
from news_digest.application.ports import ArticleExtractor, FeedSource
from news_digest.domain.grouping import group_articles
from news_digest.domain.models import Article, Story, Topic
from news_digest.domain.topics import (
    cap_stories_per_topic,
    dedupe_by_url,
    group_stories_by_topic,
)

ALL_TOPICS: tuple[Topic, ...] = tuple(Topic)

# article-extraction: every candidate's full-text fetch is independent
# network I/O, extracted concurrently once every topic's candidates are in.
DEFAULT_MAX_WORKERS = 8


def build_digest(
    feed_source: FeedSource,
    extractor: ArticleExtractor,
    since: datetime,
    topics: tuple[Topic, ...] = ALL_TOPICS,
    max_workers: int = DEFAULT_MAX_WORKERS,
) -> dict[Topic, list[Story]]:
    """story-digest: fetch, extract, group cross-outlet coverage, assign each
    story its most specific topic, and cap each topic at its story limit.

    Grouping runs across every topic's candidates combined (not per-topic)
    before topic assignment — see design.md's "Story grouping happens
    before topic assignment" decision.
    """
    candidates: list[Article] = []
    for topic in topics:
        candidates.extend(feed_source.fetch_topic(topic, since))

    if candidates:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # map preserves candidates' order in its output regardless of
            # completion order — dedupe_by_url's first-seen tie-break and
            # grouping both depend on that order staying intact.
            all_articles = list(
                executor.map(
                    partial(enrich_with_full_text, extractor=extractor), candidates
                )
            )
    else:
        all_articles = []

    stories = group_articles(dedupe_by_url(all_articles))
    by_topic = group_stories_by_topic(stories)
    return cap_stories_per_topic(by_topic)
