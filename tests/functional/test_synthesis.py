from __future__ import annotations

from datetime import UTC, datetime

import pytest

from news_digest.application.synthesis import (
    apply_synthesis,
    story_key,
    synthesis_enabled,
)
from news_digest.domain.models import Article, Story, Topic
from news_digest.infrastructure.rendering.obsidian_renderer import ObsidianRenderer


def make_article(**overrides) -> Article:
    defaults = {
        "outlet": "BBC",
        "url": "https://example.com/bbc-story",
        "title": "Trade talks collapse",
        "published_at": datetime(2026, 8, 28, 12, 0, 0, tzinfo=UTC),
        "teaser": "A teaser.",
        "topic_candidate": Topic.CANADA,
        "full_text": "BBC's own coverage of the story.",
    }
    defaults.update(overrides)
    return Article(**defaults)


@pytest.fixture
def multi_outlet_story():
    bbc = make_article(outlet="BBC", url="https://example.com/bbc-story")
    cbc = make_article(
        outlet="CBC",
        url="https://example.com/cbc-story",
        full_text="CBC's own coverage of the story.",
    )
    return Story(articles=[bbc, cbc], topic=Topic.CANADA)


def test_synthesis_off_by_default(monkeypatch):
    monkeypatch.delenv("NEWS_DIGEST_SYNTHESIS_ENABLED", raising=False)

    assert synthesis_enabled() is False


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "YES", " yes "])
def test_synthesis_enabled_accepts_truthy_values(monkeypatch, value):
    monkeypatch.setenv("NEWS_DIGEST_SYNTHESIS_ENABLED", value)

    assert synthesis_enabled() is True


@pytest.mark.parametrize("value", ["0", "false", "no", ""])
def test_synthesis_enabled_rejects_falsy_values(monkeypatch, value):
    monkeypatch.setenv("NEWS_DIGEST_SYNTHESIS_ENABLED", value)

    assert synthesis_enabled() is False


def test_synthesis_off_run_contains_no_generated_commentary(
    monkeypatch, multi_outlet_story
):
    monkeypatch.delenv("NEWS_DIGEST_SYNTHESIS_ENABLED", raising=False)
    digest = {Topic.CANADA: [multi_outlet_story]}

    apply_synthesis(
        digest, {story_key(multi_outlet_story): "A synthesis that should be ignored."}
    )

    assert multi_outlet_story.synthesis is None
    markdown = ObsidianRenderer().render(digest).decode()
    assert "synthesis" not in markdown.lower()


def test_synthesized_story_group_still_shows_every_original_article(
    monkeypatch, multi_outlet_story
):
    monkeypatch.setenv("NEWS_DIGEST_SYNTHESIS_ENABLED", "true")
    digest = {Topic.CANADA: [multi_outlet_story]}

    apply_synthesis(
        digest,
        {
            story_key(
                multi_outlet_story
            ): "BBC and CBC both report the talks broke down over tariffs."
        },
    )

    assert multi_outlet_story.synthesis is not None
    markdown = ObsidianRenderer().render(digest).decode()
    assert "BBC and CBC both report the talks broke down over tariffs." in markdown
    assert "BBC's own coverage of the story." in markdown
    assert "CBC's own coverage of the story." in markdown
