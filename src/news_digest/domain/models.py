from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class Topic(Enum):
    OTTAWA = "ottawa"
    CANADA = "canada"
    HONG_KONG = "hong-kong"
    CHINA = "china"
    TECH = "tech"
    GLOBAL = "global"


# Narrow-to-broad ranking used when a story matches more than one topic
# (story-digest: "Topic assignment is single and most-specific").
TOPIC_SPECIFICITY: dict[Topic, int] = {
    Topic.OTTAWA: 0,
    Topic.CANADA: 1,
    Topic.HONG_KONG: 2,
    Topic.CHINA: 3,
    Topic.TECH: 4,
    Topic.GLOBAL: 5,
}


class Article(BaseModel):
    model_config = ConfigDict(frozen=True)

    outlet: str
    url: str
    title: str
    published_at: datetime
    teaser: str
    topic_candidate: Topic
    # story-digest: "Per-feed cap override" — set when this article's feed
    # configures its own cap (feeds.json), exempting it from the shared
    # per-topic cap in favor of this limit instead. None means no override.
    outlet_cap: int | None = None
    full_text: str | None = None
    images: tuple[str, ...] = ()
    extraction_failed: bool = False


class Story(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    articles: list[Article] = Field(default_factory=list)
    topic: Topic | None = None
    # digest-synthesis: a cross-outlet synthesis, present only when synthesis
    # is enabled for the run — never replaces the original articles above.
    synthesis: str | None = None

    @property
    def primary(self) -> Article:
        return self.articles[0]
