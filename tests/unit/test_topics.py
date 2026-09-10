from datetime import UTC, datetime, timedelta

from news_digest.domain.models import Article, Story, Topic
from news_digest.domain.topics import (
    STORIES_PER_TOPIC_CAP,
    assign_topic,
    cap_stories_per_topic,
    dedupe_by_url,
    group_stories_by_topic,
)


def make_article(topic_candidate, published_at=None, **overrides):
    defaults = {
        "outlet": "BBC",
        "url": "https://example.com/a",
        "title": "Some headline",
        "published_at": published_at or datetime(2026, 8, 28, 12, 0, 0, tzinfo=UTC),
        "teaser": "A teaser.",
        "topic_candidate": topic_candidate,
    }
    defaults.update(overrides)
    return Article(**defaults)


def test_dedupe_by_url_keeps_the_most_specific_topic_candidate():
    shared_url = "https://example.com/shared-story"
    seen_under_canada = make_article(Topic.CANADA, url=shared_url)
    seen_under_ottawa = make_article(Topic.OTTAWA, url=shared_url)

    deduped = dedupe_by_url([seen_under_canada, seen_under_ottawa])

    assert len(deduped) == 1
    assert deduped[0].topic_candidate is Topic.OTTAWA


def test_dedupe_by_url_keeps_the_first_seen_most_specific_regardless_of_order():
    # Same scenario as above with the order reversed: an "always overwrite
    # with whatever's seen last" bug would give the wrong answer here even
    # though it happened to match the correct answer in the other order.
    shared_url = "https://example.com/shared-story"
    seen_under_ottawa = make_article(Topic.OTTAWA, url=shared_url)
    seen_under_canada = make_article(Topic.CANADA, url=shared_url)

    deduped = dedupe_by_url([seen_under_ottawa, seen_under_canada])

    assert len(deduped) == 1
    assert deduped[0].topic_candidate is Topic.OTTAWA


def test_dedupe_by_url_keeps_first_seen_on_a_specificity_tie():
    shared_url = "https://example.com/shared-story"
    first = make_article(Topic.CANADA, url=shared_url, outlet="BBC")
    second = make_article(Topic.CANADA, url=shared_url, outlet="CBC")

    deduped = dedupe_by_url([first, second])

    assert len(deduped) == 1
    assert deduped[0].outlet == "BBC"


def test_dedupe_by_url_keeps_unrelated_urls_separate():
    a = make_article(Topic.CANADA, url="https://example.com/a")
    b = make_article(Topic.TECH, url="https://example.com/b")

    deduped = dedupe_by_url([a, b])

    assert len(deduped) == 2


def test_story_matching_hong_kong_china_and_global_assigns_hong_kong():
    story = Story(
        articles=[
            make_article(Topic.GLOBAL, url="https://example.com/global"),
            make_article(Topic.CHINA, url="https://example.com/china"),
            make_article(Topic.HONG_KONG, url="https://example.com/hk"),
        ]
    )

    assert assign_topic(story) is Topic.HONG_KONG


def test_group_stories_by_topic_assigns_and_buckets():
    hk_story = Story(articles=[make_article(Topic.HONG_KONG)])
    canada_story = Story(articles=[make_article(Topic.CANADA)])

    by_topic = group_stories_by_topic([hk_story, canada_story])

    assert by_topic[Topic.HONG_KONG] == [hk_story]
    assert by_topic[Topic.CANADA] == [canada_story]
    assert hk_story.topic is Topic.HONG_KONG


def test_overflow_topic_trimmed_to_most_recent_stories():
    base_time = datetime(2026, 8, 28, 12, 0, 0, tzinfo=UTC)
    stories = [
        Story(
            articles=[
                make_article(
                    Topic.TECH,
                    published_at=base_time - timedelta(hours=i),
                    url=f"https://example.com/{i}",
                )
            ]
        )
        for i in range(15)
    ]

    by_topic = group_stories_by_topic(stories)
    capped = cap_stories_per_topic(by_topic)

    assert len(capped[Topic.TECH]) == STORIES_PER_TOPIC_CAP
    assert capped[Topic.TECH][0].primary.published_at == base_time
    assert capped[Topic.TECH][-1].primary.published_at == base_time - timedelta(hours=9)


def test_outlet_with_its_own_cap_is_exempt_from_the_shared_topic_cap():
    base_time = datetime(2026, 8, 28, 12, 0, 0, tzinfo=UTC)
    # 15 BBC stories (over the shared cap of 10) plus 15 Verge stories, Verge
    # configured with its own cap of 20 — Verge should keep all 15 (under its
    # own cap) while BBC is still trimmed to the shared cap of 10.
    bbc_stories = [
        Story(
            articles=[
                make_article(
                    Topic.TECH,
                    outlet="BBC",
                    published_at=base_time - timedelta(hours=i),
                    url=f"https://example.com/bbc-{i}",
                )
            ]
        )
        for i in range(15)
    ]
    verge_stories = [
        Story(
            articles=[
                make_article(
                    Topic.TECH,
                    outlet="The Verge",
                    outlet_cap=20,
                    published_at=base_time - timedelta(hours=i),
                    url=f"https://example.com/verge-{i}",
                )
            ]
        )
        for i in range(15)
    ]

    by_topic = group_stories_by_topic(bbc_stories + verge_stories)
    capped = cap_stories_per_topic(by_topic)

    tech_stories = capped[Topic.TECH]
    assert (
        sum(1 for s in tech_stories if s.primary.outlet == "BBC")
        == STORIES_PER_TOPIC_CAP
    )
    assert sum(1 for s in tech_stories if s.primary.outlet == "The Verge") == 15
    assert len(tech_stories) == STORIES_PER_TOPIC_CAP + 15


def test_outlet_with_its_own_cap_is_still_trimmed_once_it_exceeds_that_cap():
    base_time = datetime(2026, 8, 28, 12, 0, 0, tzinfo=UTC)
    verge_stories = [
        Story(
            articles=[
                make_article(
                    Topic.TECH,
                    outlet="The Verge",
                    outlet_cap=20,
                    published_at=base_time - timedelta(hours=i),
                    url=f"https://example.com/verge-{i}",
                )
            ]
        )
        for i in range(25)
    ]

    by_topic = group_stories_by_topic(verge_stories)
    capped = cap_stories_per_topic(by_topic)

    assert len(capped[Topic.TECH]) == 20
    assert capped[Topic.TECH][0].primary.published_at == base_time
    assert capped[Topic.TECH][-1].primary.published_at == base_time - timedelta(
        hours=19
    )


def test_combined_default_and_overridden_stories_are_returned_most_recent_first():
    base_time = datetime(2026, 8, 28, 12, 0, 0, tzinfo=UTC)
    # A single Verge story newer than everything else must sort to the front
    # even though it was appended after the (older) default-capped stories.
    newest_verge = Story(
        articles=[
            make_article(
                Topic.TECH,
                outlet="The Verge",
                outlet_cap=20,
                published_at=base_time,
                url="https://example.com/verge-newest",
            )
        ]
    )
    older_bbc = Story(
        articles=[
            make_article(
                Topic.TECH,
                outlet="BBC",
                published_at=base_time - timedelta(hours=1),
                url="https://example.com/bbc-older",
            )
        ]
    )

    by_topic = group_stories_by_topic([older_bbc, newest_verge])
    capped = cap_stories_per_topic(by_topic)

    assert [s.primary.outlet for s in capped[Topic.TECH]] == ["The Verge", "BBC"]
