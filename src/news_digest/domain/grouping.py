from __future__ import annotations

import re

from .models import Article, Story

_PUNCTUATION_RE = re.compile(r"[^\w\s]")
_WHITESPACE_RE = re.compile(r"\s+")

# Token-overlap ratio above which two differently-worded headlines are
# considered the same underlying story (story-digest: cross-outlet grouping).
SIMILARITY_THRESHOLD = 0.6


def normalize_title(title: str) -> str:
    # Punctuation becomes a space, not nothing — "Canada-trade" must split
    # into "canada trade", not merge into "canadatrade".
    lowered = title.lower()
    spaced = _PUNCTUATION_RE.sub(" ", lowered)
    return _WHITESPACE_RE.sub(" ", spaced).strip()


def _title_similarity(a: str, b: str) -> float:
    tokens_a = set(a.split())
    tokens_b = set(b.split())
    if not tokens_a or not tokens_b:
        return 0.0
    overlap = tokens_a & tokens_b
    return len(overlap) / min(len(tokens_a), len(tokens_b))


def group_articles(articles: list[Article]) -> list[Story]:
    """Group articles covering the same story across outlets.

    A new article joins the first existing story whose lead article's
    normalized title is identical or similar enough (SIMILARITY_THRESHOLD);
    otherwise it starts its own story.
    """
    stories: list[Story] = []
    normalized_titles: dict[int, str] = {}

    for article in articles:
        normalized = normalize_title(article.title)

        matched_story = next(
            (
                story
                for story in stories
                if normalized == normalized_titles[id(story.primary)]
                or _title_similarity(normalized, normalized_titles[id(story.primary)])
                >= SIMILARITY_THRESHOLD
            ),
            None,
        )

        if matched_story is not None:
            matched_story.articles.append(article)
        else:
            stories.append(Story(articles=[article]))
            normalized_titles[id(article)] = normalized

    return stories
