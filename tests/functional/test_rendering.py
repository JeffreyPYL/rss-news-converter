from __future__ import annotations

import hashlib
import uuid
import zipfile
from datetime import UTC, datetime
from io import BytesIO
from xml.etree import ElementTree

import httpx
import pytest

from news_digest.domain.models import Article, Story, Topic
from news_digest.infrastructure._http_client import DEFAULT_USER_AGENT
from news_digest.infrastructure.rendering.epub_renderer import EpubRenderer
from news_digest.infrastructure.rendering.obsidian_renderer import ObsidianRenderer

IMAGE_URL = "https://example.com/photo.jpg"
IMAGE_BYTES = b"\xff\xd8\xff\xe0fake-jpeg-bytes"


def make_article(**overrides) -> Article:
    defaults = {
        "outlet": "BBC",
        "url": "https://example.com/a",
        "title": "Trade talks collapse",
        "published_at": datetime(2026, 8, 28, 12, 0, 0, tzinfo=UTC),
        "teaser": "A teaser.",
        "topic_candidate": Topic.CANADA,
        "full_text": "Negotiators met on Tuesday.\n\n![photo](https://example.com/photo.jpg)\n\nTalks continue.",
        "images": (IMAGE_URL,),
    }
    defaults.update(overrides)
    return Article(**defaults)


@pytest.fixture
def sample_digest():
    canada_story = Story(articles=[make_article()], topic=Topic.CANADA)
    tech_story = Story(
        articles=[
            make_article(
                outlet="CBC", title="New chip announced", topic_candidate=Topic.TECH
            )
        ],
        topic=Topic.TECH,
    )
    return {Topic.CANADA: [canada_story], Topic.TECH: [tech_story]}


@pytest.fixture
def image_response(httpx_mock):
    # Both sample articles reference the same image URL, but the renderer
    # embeds a shared image once per render rather than once per reference.
    httpx_mock.add_response(
        url=IMAGE_URL, content=IMAGE_BYTES, headers={"content-type": "image/jpeg"}
    )


def test_epub_renderer_default_client_config():
    renderer = EpubRenderer()

    assert renderer._client.timeout == httpx.Timeout(15.0)
    assert renderer._client.follow_redirects is True
    assert renderer._client._trust_env is False
    assert renderer._client.headers["user-agent"] == DEFAULT_USER_AGENT


OPF_NS = {
    "opf": "http://www.idpf.org/2007/opf",
    "dc": "http://purl.org/dc/elements/1.1/",
}
XHTML_NS = {"xhtml": "http://www.w3.org/1999/xhtml"}


def test_multi_topic_digest_produces_one_epub_with_all_topics_and_an_image(
    sample_digest, image_response
):
    renderer = EpubRenderer()

    epub_bytes = renderer.render(sample_digest)

    with zipfile.ZipFile(BytesIO(epub_bytes)) as archive:
        names = archive.namelist()
        assert any(name.endswith("canada.xhtml") for name in names)
        assert any(name.endswith("tech.xhtml") for name in names)

        image_hash = hashlib.sha256(IMAGE_URL.encode()).hexdigest()
        expected_image_path = f"images/{image_hash}.jpeg"
        assert any(name.endswith(expected_image_path) for name in names)
        image_entry = next(n for n in names if n.endswith(expected_image_path))
        assert archive.read(image_entry) == IMAGE_BYTES

        canada_entry = next(n for n in names if n.endswith("canada.xhtml"))
        root = ElementTree.fromstring(archive.read(canada_entry))
        assert root.get("lang") == "en"
        assert root.get("{http://www.w3.org/XML/1998/namespace}lang") == "en"
        assert (
            root.findtext(".//xhtml:head/xhtml:title", namespaces=XHTML_NS) == "Canada"
        )

        canada_bytes = archive.read(canada_entry)
        # A join-separator regression (e.g. joining with "XXXX" instead of "")
        # wouldn't break XML well-formedness, so element lookups by tag alone
        # can't catch it — check the raw serialized bytes directly.
        assert b"XX" not in canada_bytes

        body = root.find("xhtml:body", XHTML_NS)
        assert body.findtext("xhtml:h1", namespaces=XHTML_NS) == "Canada"
        h2 = body.find("xhtml:h2", XHTML_NS)
        assert h2.text == "Trade talks collapse"
        assert h2.get("id") == "story-canada-0"
        assert body.findtext("xhtml:h3", namespaces=XHTML_NS) == "BBC"
        assert body.find("xhtml:img", XHTML_NS).get("src") == expected_image_path

        paragraphs = body.findall("xhtml:p", XHTML_NS)
        assert paragraphs[0].text == "Negotiators met on Tuesday."
        assert paragraphs[1].text == "Talks continue."
        link = paragraphs[2].find("xhtml:a", XHTML_NS)
        assert link.get("href") == "https://example.com/a"
        assert link.text == "Read on BBC"

        # Last paragraph in the chapter is the back-to-index link.
        back_link = paragraphs[-1].find("xhtml:a", XHTML_NS)
        assert back_link.get("href") == "index.xhtml"
        assert back_link.text == "↑ Back to index"

        index_entry = next(n for n in names if n.endswith("index.xhtml"))
        index_bytes = archive.read(index_entry)
        assert b"XX" not in index_bytes
        index_root = ElementTree.fromstring(index_bytes)
        assert index_root.get("lang") == "en"
        assert index_root.get("{http://www.w3.org/XML/1998/namespace}lang") == "en"
        assert (
            index_root.findtext(".//xhtml:head/xhtml:title", namespaces=XHTML_NS)
            == "Index"
        )
        index_body = index_root.find("xhtml:body", XHTML_NS)
        assert index_body.findtext("xhtml:h1", namespaces=XHTML_NS) == "Index"
        topic_headings = [h2.text for h2 in index_body.findall("xhtml:h2", XHTML_NS)]
        assert topic_headings == ["Canada", "Tech"]

        index_links = index_body.findall(".//xhtml:a", XHTML_NS)
        links_by_href = {a.get("href"): a.text for a in index_links}
        assert links_by_href["canada.xhtml#story-canada-0"] == "Trade talks collapse"
        assert links_by_href["tech.xhtml#story-tech-0"] == "New chip announced"

        # The Tech chapter shares the same image URL as Canada's — this
        # verifies the per-render embed cache stores the successfully
        # embedded item (not None) after the first embed, so later
        # references to the same URL still render an <img>, not a blank.
        tech_entry = next(n for n in names if n.endswith("tech.xhtml"))
        tech_root = ElementTree.fromstring(archive.read(tech_entry))
        tech_body = tech_root.find("xhtml:body", XHTML_NS)
        assert tech_body.find("xhtml:img", XHTML_NS).get("src") == expected_image_path

        opf_path = next(n for n in names if n.endswith(".opf"))
        opf = ElementTree.fromstring(archive.read(opf_path))
        assert opf.findtext("opf:metadata/dc:title", namespaces=OPF_NS) == "News Digest"
        assert opf.findtext("opf:metadata/dc:language", namespaces=OPF_NS) == "en"
        identifier = opf.findtext("opf:metadata/dc:identifier", namespaces=OPF_NS)
        uuid.UUID(identifier)  # raises ValueError if not a real UUID

        itemrefs = [
            el.get("idref") for el in opf.findall(".//opf:spine/opf:itemref", OPF_NS)
        ]
        assert itemrefs[0] == "nav"
        assert len(itemrefs) == 4  # nav + index + canada + tech chapters

        image_manifest_item = next(
            el
            for el in opf.findall(".//opf:manifest/opf:item", OPF_NS)
            if el.get("href", "").endswith(expected_image_path)
        )
        assert image_manifest_item.get("id") == expected_image_path
        assert image_manifest_item.get("media-type") == "image/jpeg"


def test_embed_image_uses_the_actual_content_type_header_not_a_hardcoded_default(
    httpx_mock,
):
    # Distinguishes a real header lookup from an accidental fallback: if the
    # code always used its "image/jpeg" default, this would come out wrong.
    httpx_mock.add_response(
        url=IMAGE_URL, content=IMAGE_BYTES, headers={"content-type": "image/png"}
    )
    story = Story(articles=[make_article()], topic=Topic.CANADA)

    epub_bytes = EpubRenderer().render({Topic.CANADA: [story]})

    image_hash = hashlib.sha256(IMAGE_URL.encode()).hexdigest()
    with zipfile.ZipFile(BytesIO(epub_bytes)) as archive:
        assert any(
            name.endswith(f"images/{image_hash}.png") for name in archive.namelist()
        )


def test_embed_image_strips_charset_param_from_content_type_header(httpx_mock):
    # Distinguishes splitting on ";" from a whitespace-split: only a real
    # semicolon-bearing header ("image/jpeg; charset=binary") tells them apart.
    httpx_mock.add_response(
        url=IMAGE_URL,
        content=IMAGE_BYTES,
        headers={"content-type": "image/jpeg; charset=binary"},
    )
    story = Story(articles=[make_article()], topic=Topic.CANADA)

    epub_bytes = EpubRenderer().render({Topic.CANADA: [story]})

    image_hash = hashlib.sha256(IMAGE_URL.encode()).hexdigest()
    with zipfile.ZipFile(BytesIO(epub_bytes)) as archive:
        assert any(
            name.endswith(f"images/{image_hash}.jpeg") for name in archive.namelist()
        )


def test_embed_image_defaults_to_jpeg_when_no_content_type_header(httpx_mock):
    httpx_mock.add_response(
        url=IMAGE_URL, content=IMAGE_BYTES
    )  # no content-type header
    story = Story(articles=[make_article()], topic=Topic.CANADA)

    epub_bytes = EpubRenderer().render({Topic.CANADA: [story]})

    image_hash = hashlib.sha256(IMAGE_URL.encode()).hexdigest()
    with zipfile.ZipFile(BytesIO(epub_bytes)) as archive:
        assert any(
            name.endswith(f"images/{image_hash}.jpeg") for name in archive.namelist()
        )


def test_embed_image_failure_is_cached_and_omits_the_image_everywhere(httpx_mock):
    httpx_mock.add_exception(httpx.ConnectTimeout("timed out"), url=IMAGE_URL)
    canada_story = Story(articles=[make_article()], topic=Topic.CANADA)
    tech_story = Story(
        articles=[
            make_article(
                outlet="CBC", title="New chip announced", topic_candidate=Topic.TECH
            )
        ],
        topic=Topic.TECH,
    )

    epub_bytes = EpubRenderer().render(
        {Topic.CANADA: [canada_story], Topic.TECH: [tech_story]}
    )

    with zipfile.ZipFile(BytesIO(epub_bytes)) as archive:
        names = archive.namelist()
        assert not any("images/" in name for name in names)
        for entry in (
            n for n in names if n.endswith(".xhtml") and n != "EPUB/nav.xhtml"
        ):
            root = ElementTree.fromstring(archive.read(entry))
            assert root.find(".//xhtml:img", XHTML_NS) is None


def test_epub_synthesis_renders_without_crashing_and_shows_originals(image_response):
    story = Story(
        articles=[make_article()],
        topic=Topic.CANADA,
        synthesis="A brief cross-outlet synthesis.",
    )

    epub_bytes = EpubRenderer().render({Topic.CANADA: [story]})

    with zipfile.ZipFile(BytesIO(epub_bytes)) as archive:
        canada_entry = next(n for n in archive.namelist() if n.endswith("canada.xhtml"))
        root = ElementTree.fromstring(archive.read(canada_entry))
        body = root.find("xhtml:body", XHTML_NS)
        em = body.find("xhtml:p/xhtml:em", XHTML_NS)
        assert em.text == "A brief cross-outlet synthesis."
        assert body.findtext("xhtml:h3", namespaces=XHTML_NS) == "BBC"


def test_obsidian_note_has_equivalent_content_to_the_epub(sample_digest):
    renderer = ObsidianRenderer()

    markdown_bytes = renderer.render(sample_digest)

    full_text = "Negotiators met on Tuesday.\n\n![photo](https://example.com/photo.jpg)\n\nTalks continue."
    expected_lines = [
        "# News Digest",
        "",
        "## Index",
        "",
        "**Canada**",
        "- [[#Trade talks collapse]]",
        "",
        "**Tech**",
        "- [[#New chip announced]]",
        "",
        "## Canada",
        "",
        "### Trade talks collapse",
        "",
        "#### BBC",
        "",
        full_text,
        "",
        "[Read on BBC](https://example.com/a)",
        "",
        "[[#Index|↑ Back to index]]",
        "",
        "## Tech",
        "",
        "### New chip announced",
        "",
        "#### CBC",
        "",
        full_text,
        "",
        "[Read on CBC](https://example.com/a)",
        "",
        "[[#Index|↑ Back to index]]",
        "",
    ]
    assert markdown_bytes == "\n".join(expected_lines).encode("utf-8")


def test_obsidian_note_with_synthesis_has_exact_expected_layout():
    story = Story(
        articles=[make_article(outlet="BBC", url="https://example.com/a")],
        topic=Topic.CANADA,
        synthesis="A brief cross-outlet synthesis.",
    )
    digest = {Topic.CANADA: [story]}

    markdown_bytes = ObsidianRenderer().render(digest)

    full_text = "Negotiators met on Tuesday.\n\n![photo](https://example.com/photo.jpg)\n\nTalks continue."
    expected_lines = [
        "# News Digest",
        "",
        "## Index",
        "",
        "**Canada**",
        "- [[#Trade talks collapse]]",
        "",
        "## Canada",
        "",
        "### Trade talks collapse",
        "",
        "> A brief cross-outlet synthesis.",
        "",
        "#### BBC",
        "",
        full_text,
        "",
        "[Read on BBC](https://example.com/a)",
        "",
        "[[#Index|↑ Back to index]]",
        "",
    ]
    assert markdown_bytes == "\n".join(expected_lines).encode("utf-8")


def test_epub_and_obsidian_render_empty_digest():
    digest = {}
    epub_bytes = EpubRenderer().render(digest)
    assert len(epub_bytes) > 0
    obsidian_bytes = ObsidianRenderer().render(digest)
    assert len(obsidian_bytes) > 0
