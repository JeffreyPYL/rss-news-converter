from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from news_digest.domain.models import Topic


class DirectFeed(BaseModel):
    """A feed genuinely dedicated to one topic — every item counts."""

    model_config = ConfigDict(frozen=True)

    outlet: str
    url: str
    # None means this feed's stories compete for the shared per-topic cap
    # (story-digest's STORIES_PER_TOPIC_CAP) like everyone else. Set this to
    # exempt them and give this outlet its own limit instead.
    cap: int | None = None
    # None means this feed uses RssFeedSource's default request timeout. Set
    # this to give a slow or occasionally-flaky outlet more (or less) time.
    timeout: float | None = None


class KeywordFilteredFeed(BaseModel):
    """A broader feed (e.g. World/Asia) filtered down to items matching a topic's keywords.

    Used where no outlet publishes a feed dedicated to the topic (Hong Kong, China).
    """

    model_config = ConfigDict(frozen=True)

    outlet: str
    url: str
    keywords: tuple[str, ...]
    cap: int | None = None
    timeout: float | None = None


class _TopicFeeds(BaseModel):
    direct: list[DirectFeed] = []
    keyword_filtered: list[KeywordFilteredFeed] = []


# The user-editable feed list — add or remove a feed here, no code change
# needed. Override which file gets read via NEWS_DIGEST_FEEDS_CONFIG_PATH
# (see Settings.feeds_config_path); this is only the default.
DEFAULT_FEEDS_PATH = Path(__file__).parent / "feeds.json"


def load_feeds(
    path: Path,
) -> tuple[dict[Topic, list[DirectFeed]], dict[Topic, list[KeywordFilteredFeed]]]:
    """Parse a feeds config file into per-topic direct and keyword-filtered feed
    dicts, exhaustive over every Topic (a topic absent from the file gets []
    for both, rather than requiring every topic to be listed explicitly)."""
    raw = json.loads(path.read_text())
    direct_feeds: dict[Topic, list[DirectFeed]] = {}
    keyword_filtered_feeds: dict[Topic, list[KeywordFilteredFeed]] = {}
    for topic in Topic:
        topic_feeds = _TopicFeeds.model_validate(raw.get(topic.value, {}))
        direct_feeds[topic] = topic_feeds.direct
        keyword_filtered_feeds[topic] = topic_feeds.keyword_filtered
    return direct_feeds, keyword_filtered_feeds


DIRECT_FEEDS, KEYWORD_FILTERED_FEEDS = load_feeds(DEFAULT_FEEDS_PATH)
