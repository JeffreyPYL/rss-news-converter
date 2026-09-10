from datetime import UTC, datetime

from news_digest.domain.models import Article, Story, Topic


def make_article(**overrides):
    defaults = {
        "outlet": "BBC",
        "url": "https://example.com/a",
        "title": "Some headline",
        "published_at": datetime(2026, 8, 28, 12, 0, 0, tzinfo=UTC),
        "teaser": "A teaser.",
        "topic_candidate": Topic.CANADA,
    }
    defaults.update(overrides)
    return Article(**defaults)


def test_article_construction_holds_fields():
    article = make_article()

    assert article.outlet == "BBC"
    assert article.topic_candidate is Topic.CANADA
    assert article.full_text is None
    assert article.images == ()
    assert article.extraction_failed is False


def test_article_equality_by_value():
    a = make_article()
    b = make_article()

    assert a == b


def test_story_primary_is_first_article():
    first = make_article(outlet="BBC")
    second = make_article(outlet="CBC")
    story = Story(articles=[first, second])

    assert story.primary is first
    assert story.topic is None
