from __future__ import annotations

from typing import Protocol

import httpx
import trafilatura

from news_digest.application.ports import ExtractedContent, ExtractionError
from news_digest.infrastructure._http_client import DEFAULT_USER_AGENT

from ._markdown_images import extract_image_urls


class ExtractFn(Protocol):
    def __call__(
        self,
        html: str,
        *,
        output_format: str,
        include_images: bool,
        include_links: bool,
        favor_precision: bool,
    ) -> str | None: ...


class TrafilaturaExtractor:
    """article-extraction default: a plain unauthenticated fetch + Trafilatura.

    Confirmed during design exploration to reach full text on BBC, CBC, and
    Globe and Mail (including paywalled Globe and Mail pieces) without login.
    """

    def __init__(
        self,
        client: httpx.Client | None = None,
        extract_fn: ExtractFn = trafilatura.extract,
    ) -> None:
        self._client = client or httpx.Client(
            timeout=15.0,
            follow_redirects=True,
            trust_env=False,
            headers={"User-Agent": DEFAULT_USER_AGENT},
        )
        self._extract_fn = extract_fn

    def extract(self, url: str) -> ExtractedContent:
        try:
            response = self._client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ExtractionError(f"failed to fetch {url}: {exc}") from exc

        text = self._extract_fn(
            response.text,
            output_format="markdown",
            include_images=True,
            include_links=False,
            favor_precision=True,
        )
        if not text:
            raise ExtractionError(f"no extractable content at {url}")

        return ExtractedContent(text=text, images=extract_image_urls(text))
