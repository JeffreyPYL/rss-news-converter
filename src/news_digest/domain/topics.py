from __future__ import annotations

from .models import TOPIC_SPECIFICITY, Article, Story, Topic

# story-digest: "Per-topic story cap" — at most this many stories per topic
# per run, most-recent-first when more qualify.
STORIES_PER_TOPIC_CAP = 10


def dedupe_by_url(articles: list[Article]) -> list[Article]:
    """Collapse the same URL fetched under more than one topic lens (e.g. a
    keyword-filtered feed reusing another topic's direct feed URL) to a
    single Article, keeping its most specific topic_candidate.

    Runs before grouping so a story never carries two "articles" that are
    really the same physical piece.
    """
    best_by_url: dict[str, Article] = {}
    for article in articles:
        existing = best_by_url.get(article.url)
        if existing is None or (
            TOPIC_SPECIFICITY[article.topic_candidate]
            < TOPIC_SPECIFICITY[existing.topic_candidate]
        ):
            best_by_url[article.url] = article
    return list(best_by_url.values())


def assign_topic(story: Story) -> Topic:
    """Pick the single most-specific topic a story's articles were fetched under.

    story-digest: "Topic assignment is single and most-specific" — narrow to
    broad: Ottawa, Canada, Hong Kong, China, Tech, Global.
    """
    candidates = {article.topic_candidate for article in story.articles}
    return min(candidates, key=lambda topic: TOPIC_SPECIFICITY[topic])


def group_stories_by_topic(stories: list[Story]) -> dict[Topic, list[Story]]:
    """Assign each story its topic and bucket stories by that topic."""
    by_topic: dict[Topic, list[Story]] = {}
    for story in stories:
        story.topic = assign_topic(story)
        by_topic.setdefault(story.topic, []).append(story)
    return by_topic


def _outlet_cap_override(story: Story) -> tuple[str, int] | None:
    """A story whose articles include one from an outlet with its own
    configured cap (Article.outlet_cap, set from that feed's `cap` in
    feeds.json) is exempt from the shared per-topic cap — it gets this
    outlet's own limit instead."""
    for article in story.articles:
        if article.outlet_cap is not None:
            return article.outlet, article.outlet_cap
    return None


def _most_recent(stories: list[Story], cap: int) -> list[Story]:
    return sorted(stories, key=lambda s: s.primary.published_at, reverse=True)[:cap]


def cap_stories_per_topic(
    stories_by_topic: dict[Topic, list[Story]], cap: int = STORIES_PER_TOPIC_CAP
) -> dict[Topic, list[Story]]:
    """Trim each topic's stories to the `cap` most recently published, except
    stories from an outlet with its own cap override — those are capped
    independently at their own limit instead of competing for the shared one."""
    result: dict[Topic, list[Story]] = {}
    for topic, stories in stories_by_topic.items():
        default_stories: list[Story] = []
        overridden: dict[str, list[Story]] = {}
        outlet_caps: dict[str, int] = {}
        for story in stories:
            override = _outlet_cap_override(story)
            if override is None:
                default_stories.append(story)
            else:
                outlet, outlet_cap = override
                overridden.setdefault(outlet, []).append(story)
                outlet_caps[outlet] = outlet_cap

        capped = _most_recent(default_stories, cap)
        for outlet, outlet_stories in overridden.items():
            capped.extend(_most_recent(outlet_stories, outlet_caps[outlet]))

        result[topic] = sorted(
            capped, key=lambda s: s.primary.published_at, reverse=True
        )
    return result
