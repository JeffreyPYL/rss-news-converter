from __future__ import annotations

from news_digest.domain.models import Story, Topic


def story_key(story: Story) -> str:
    """A stable identifier for a story group, for attaching synthesis text
    written by an agent turn that has no Python object identities to work with."""
    return story.primary.url


def apply_synthesis(
    digest: dict[Topic, list[Story]],
    synthesis_by_story_key: dict[str, str],
    enabled: bool = True,
) -> None:
    """Attach synthesis text to story groups, keyed by `story_key`.

    Never generates synthesis itself — the text comes from the calling
    AI agent turn (e.g. Claude Code or Antigravity / `agy` via `/news-digest`)
    or an automated runner. A no-op when synthesis is disabled, so the
    off path never carries generated text (digest-synthesis: "Synthesis is
    an explicit toggle").
    """
    if not enabled:
        return
    for stories in digest.values():
        for story in stories:
            text = synthesis_by_story_key.get(story_key(story))
            if text is not None:
                story.synthesis = text
