from __future__ import annotations

from datetime import datetime
from typing import Protocol

from pydantic import BaseModel, ConfigDict

from news_digest.domain.models import Article, Story, Topic


class FeedSource(Protocol):
    def fetch_topic(self, topic: Topic, since: datetime) -> list[Article]:
        """Fetch and normalize candidate articles for a topic from all its configured sources."""
        ...


class ExtractedContent(BaseModel):
    model_config = ConfigDict(frozen=True)

    text: str
    images: tuple[str, ...]


class ExtractionError(Exception):
    """Raised when a page can't be fetched or no meaningful content could be extracted."""


class ArticleExtractor(Protocol):
    def extract(self, url: str) -> ExtractedContent:
        """Fetch `url` and return its full article text and image URLs.

        Raises ExtractionError on failure — callers fall back to the
        article's existing headline/teaser/link rather than treating this
        as fatal (article-extraction: graceful extraction failure).
        """
        ...


class DigestRenderer(Protocol):
    def render(self, digest: dict[Topic, list[Story]]) -> bytes:
        """Render a full run's digest (every topic) into this renderer's output format."""
        ...


class DeliveryError(Exception):
    """Raised when a delivery target fails — callers report it, not raise the whole run."""


class DigestDelivery(Protocol):
    def deliver(self, rendered: bytes, generated_at: datetime) -> None:
        """Deliver a rendered digest to this target, timestamped with when the
        run generated it. Raises DeliveryError on failure."""
        ...
