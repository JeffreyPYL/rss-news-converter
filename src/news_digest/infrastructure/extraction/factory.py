from __future__ import annotations

from news_digest.application.ports import ArticleExtractor
from news_digest.infrastructure.settings import Settings

from .defuddle_extractor import DefuddleExtractor
from .trafilatura_extractor import TrafilaturaExtractor

_EXTRACTORS: dict[str, type[ArticleExtractor]] = {
    "trafilatura": TrafilaturaExtractor,
    "defuddle": DefuddleExtractor,
}


def get_extractor(
    name: str | None = None, settings: Settings | None = None
) -> ArticleExtractor:
    """article-extraction: the extraction engine is configurable (env var or
    `.env` — see `Settings`), defaulting to Trafilatura."""
    name = name or (settings or Settings()).extractor or "trafilatura"
    try:
        extractor_cls = _EXTRACTORS[name]
    except KeyError:
        raise ValueError(
            f"unknown extractor: {name!r} (choices: {sorted(_EXTRACTORS)})"
        ) from None
    return extractor_cls()
