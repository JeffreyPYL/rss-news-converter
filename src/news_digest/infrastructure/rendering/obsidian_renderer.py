from __future__ import annotations

from news_digest.domain.models import Story, Topic

from ._topic_titles import TOPIC_TITLES

BACK_TO_INDEX_LINK = "[[#Index|↑ Back to index]]"


class ObsidianRenderer:
    """digest-rendering: the same digest content as an Obsidian-flavored Markdown note."""

    def render(self, digest: dict[Topic, list[Story]]) -> bytes:
        by_topic = {topic: digest[topic] for topic in Topic if digest.get(topic)}

        lines = ["# News Digest", ""]
        lines.extend(_render_index(by_topic))
        for topic, stories in by_topic.items():
            lines.append(f"## {TOPIC_TITLES[topic]}")
            lines.append("")
            for story in stories:
                lines.append(f"### {story.primary.title}")
                lines.append("")
                if story.synthesis:
                    lines.append(f"> {story.synthesis}")
                    lines.append("")
                for article in story.articles:
                    lines.append(f"#### {article.outlet}")
                    lines.append("")
                    lines.append(article.full_text or article.teaser)
                    lines.append("")
                    lines.append(f"[Read on {article.outlet}]({article.url})")
                    lines.append("")
                lines.append(BACK_TO_INDEX_LINK)
                lines.append("")
        return "\n".join(lines).encode("utf-8")


def _render_index(by_topic: dict[Topic, list[Story]]) -> list[str]:
    if not by_topic:
        return []
    lines = ["## Index", ""]
    for topic, stories in by_topic.items():
        lines.append(f"**{TOPIC_TITLES[topic]}**")
        # Obsidian's `[[#Heading]]` links by exact heading text within the
        # same note — no slug to keep in sync with the heading itself.
        lines.extend(f"- [[#{story.primary.title}]]" for story in stories)
        lines.append("")
    return lines
