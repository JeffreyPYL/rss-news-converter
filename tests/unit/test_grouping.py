from datetime import UTC, datetime

from news_digest.domain.grouping import (
    _title_similarity,
    group_articles,
    normalize_title,
)
from news_digest.domain.models import Article, Topic


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


def test_normalize_title_strips_punctuation_and_case():
    assert (
        normalize_title("Canada, U.S. Trade Talks Collapse!")
        == "canada u s trade talks collapse"
    )


def test_normalize_title_splits_hyphenated_words():
    assert (
        normalize_title("Canada-U.S. trade talks collapse")
        == "canada u s trade talks collapse"
    )


def test_same_story_from_two_outlets_groups_into_one_entry():
    bbc = make_article(outlet="BBC", title="Canada, U.S. trade talks collapse")
    cbc = make_article(
        outlet="CBC", title="Canada-U.S. trade talks collapse after deadline"
    )

    stories = group_articles([bbc, cbc])

    assert len(stories) == 1
    assert stories[0].articles == [bbc, cbc]


def test_title_similarity_is_exact_overlap_ratio():
    assert _title_similarity("a b c d", "a b x y") == 0.5


def test_title_similarity_zero_when_only_one_side_is_empty():
    # regression: `and` instead of `or` here divides by zero rather than
    # short-circuiting to 0.0
    assert _title_similarity("", "some words here") == 0.0
    assert _title_similarity("some words here", "") == 0.0


def test_title_similarity_zero_when_both_sides_empty():
    assert _title_similarity("", "") == 0.0


def test_similarity_exactly_at_threshold_groups_together():
    bbc = make_article(outlet="BBC", title="a b c d e")
    cbc = make_article(outlet="CBC", title="a b c x y")  # token overlap ratio == 0.6

    stories = group_articles([bbc, cbc])

    assert len(stories) == 1


def test_unrelated_story_from_one_outlet_stays_its_own_entry():
    bbc = make_article(outlet="BBC", title="Canada-U.S. trade talks collapse")
    unrelated = make_article(outlet="CBC", title="Ottawa announces new transit funding")

    stories = group_articles([bbc, unrelated])

    assert len(stories) == 2
    assert {story.articles[0] for story in stories} == {bbc, unrelated}
