from __future__ import annotations

import hashlib
import html
import tempfile
import uuid
from pathlib import Path

import httpx
from ebooklib import epub

from news_digest.domain.models import Story, Topic
from news_digest.infrastructure._http_client import DEFAULT_USER_AGENT

from ._topic_titles import TOPIC_TITLES

INDEX_FILE_NAME = "index.xhtml"


class EpubRenderer:
    """digest-rendering: one combined EPUB per run, all topics, images embedded.

    Images are downloaded and embedded rather than linked — e-readers
    (Kindle included) generally don't fetch remote images at read time.
    """

    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(
            timeout=15.0,
            follow_redirects=True,
            trust_env=False,
            headers={"User-Agent": DEFAULT_USER_AGENT},
        )
        self._embedded_images: dict[str, epub.EpubItem | None] = {}

    def render(self, digest: dict[Topic, list[Story]]) -> bytes:
        book = epub.EpubBook()
        book.set_identifier(str(uuid.uuid4()))
        book.set_title("News Digest")
        book.set_language("en")
        self._embedded_images = {}

        by_topic = {
            topic: digest.get(topic, []) for topic in Topic if digest.get(topic)
        }

        chapters = []
        for topic, stories in by_topic.items():
            chapter = self._render_topic_chapter(book, topic, stories)
            book.add_item(chapter)
            chapters.append(chapter)

        index_chapter = self._render_index_chapter(by_topic)
        book.add_item(index_chapter)

        book.toc = [index_chapter, *chapters]
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = ["nav", index_chapter, *chapters]

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = Path(tmp_dir) / "digest.epub"
            epub.write_epub(str(out_path), book)
            return out_path.read_bytes()

    def _render_index_chapter(
        self, by_topic: dict[Topic, list[Story]]
    ) -> epub.EpubHtml:
        html_parts = ["<h1>Index</h1>"]
        for topic, stories in by_topic.items():
            html_parts.append(f"<h2>{html.escape(TOPIC_TITLES[topic])}</h2><ul>")
            for i, story in enumerate(stories):
                anchor = _story_anchor(topic, i)
                html_parts.append(
                    f'<li><a href="{topic.value}.xhtml#{anchor}">{html.escape(story.primary.title)}</a></li>'
                )
            html_parts.append("</ul>")

        chapter = epub.EpubHtml(title="Index", file_name=INDEX_FILE_NAME, lang="en")
        chapter.content = "".join(html_parts)
        return chapter

    def _render_topic_chapter(
        self, book: epub.EpubBook, topic: Topic, stories: list[Story]
    ) -> epub.EpubHtml:
        title = TOPIC_TITLES[topic]
        html_parts = [f"<h1>{html.escape(title)}</h1>"]

        for i, story in enumerate(stories):
            html_parts.append(
                f'<h2 id="{_story_anchor(topic, i)}">{html.escape(story.primary.title)}</h2>'
            )
            if story.synthesis:
                html_parts.append(f"<p><em>{html.escape(story.synthesis)}</em></p>")
            for article in story.articles:
                html_parts.append(f"<h3>{html.escape(article.outlet)}</h3>")
                for image_url in article.images:
                    image_item = self._embed_image(book, image_url)
                    if image_item is not None:
                        html_parts.append(f'<img src="{image_item.file_name}" />')
                body = article.full_text or article.teaser
                html_parts.append(_body_to_html(body))
                html_parts.append(
                    f'<p><a href="{html.escape(article.url)}">Read on {html.escape(article.outlet)}</a></p>'
                )
            html_parts.append(f'<p><a href="{INDEX_FILE_NAME}">↑ Back to index</a></p>')

        chapter = epub.EpubHtml(
            title=title, file_name=f"{topic.value}.xhtml", lang="en"
        )
        chapter.content = "".join(html_parts)
        return chapter

    def _embed_image(self, book: epub.EpubBook, url: str) -> epub.EpubItem | None:
        # Multiple articles (or outlets covering the same story) can share an
        # image URL — embed it once per render, not once per reference.
        if url in self._embedded_images:
            return self._embedded_images[url]

        try:
            response = self._client.get(url)
            response.raise_for_status()
        except httpx.HTTPError:
            self._embedded_images[url] = None
            return None

        content_type = response.headers.get("content-type", "image/jpeg").split(";")[0]
        ext = content_type.split("/")[-1]
        file_name = f"images/{hashlib.sha256(url.encode()).hexdigest()}.{ext}"
        image_item = epub.EpubItem(
            uid=file_name,
            file_name=file_name,
            media_type=content_type,
            content=response.content,
        )
        book.add_item(image_item)
        self._embedded_images[url] = image_item
        return image_item


def _story_anchor(topic: Topic, index: int) -> str:
    return f"story-{topic.value}-{index}"


def _body_to_html(markdown_text: str) -> str:
    """Paragraph-split markdown into HTML, dropping standalone image lines
    (images are embedded separately, above the body) and escaping the rest."""
    paragraphs = [p.strip() for p in markdown_text.split("\n\n") if p.strip()]
    kept = [p for p in paragraphs if not p.startswith("![")]
    return "".join(f"<p>{html.escape(p)}</p>" for p in kept)
