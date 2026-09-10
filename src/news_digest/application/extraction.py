from __future__ import annotations

from news_digest.application.ports import ArticleExtractor, ExtractionError
from news_digest.domain.models import Article


def enrich_with_full_text(article: Article, extractor: ArticleExtractor) -> Article:
    """article-extraction: on failure, fall back to the article's existing
    headline/teaser/link rather than failing the run."""
    try:
        extracted = extractor.extract(article.url)
    except ExtractionError:
        return article.model_copy(update={"extraction_failed": True})
    return article.model_copy(
        update={"full_text": extracted.text, "images": extracted.images}
    )
