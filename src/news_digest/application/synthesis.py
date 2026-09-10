from __future__ import annotations

from news_digest.domain.models import Story, Topic
from news_digest.infrastructure.settings import Settings


def synthesis_enabled(settings: Settings | None = None) -> bool:
    """digest-synthesis: an explicit on/off setting for a run (env var or
    `.env` — see `Settings`)."""
    raw = (settings or Settings()).synthesis_enabled
    if raw is None:
        return False
    return raw.strip().lower() in ("1", "true", "yes")


def story_key(story: Story) -> str:
    """A stable identifier for a story group, for attaching synthesis text
    written by an agent turn that has no Python object identities to work with."""
    return story.primary.url


def apply_synthesis(
    digest: dict[Topic, list[Story]], synthesis_by_story_key: dict[str, str]
) -> None:
    """Attach synthesis text to story groups, keyed by `story_key`.

    Never generates synthesis itself — the text comes from the calling
    Claude Code agent turn (see the `/news-digest` command for the
    on-demand path; the scheduled path's mechanism is deferred, see
    design.md's Open Questions). A no-op when synthesis is disabled, so the
    off path never carries generated text (digest-synthesis: "Synthesis is
    an explicit toggle").
    """
    if not synthesis_enabled():
        return
    for stories in digest.values():
        for story in stories:
            text = synthesis_by_story_key.get(story_key(story))
            if text is not None:
                story.synthesis = text
