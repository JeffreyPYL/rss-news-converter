from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Protocol

import httpx

from news_digest.application.ports import ExtractedContent, ExtractionError
from news_digest.infrastructure._http_client import DEFAULT_USER_AGENT

from ._markdown_images import extract_image_urls


class ProcessRunner(Protocol):
    def __call__(
        self,
        args: list[str],
        *,
        capture_output: bool,
        text: bool,
        timeout: int,
        check: bool,
    ) -> subprocess.CompletedProcess: ...


class DefuddleExtractor:
    """article-extraction alternative: same unauthenticated fetch, Defuddle CLI for cleanup.

    Kept swappable with TrafilaturaExtractor via configuration rather than
    replacing it — see design.md's extraction decision.
    """

    def __init__(
        self,
        client: httpx.Client | None = None,
        runner: ProcessRunner = subprocess.run,
    ) -> None:
        self._client = client or httpx.Client(
            timeout=15.0,
            follow_redirects=True,
            trust_env=False,
            headers={"User-Agent": DEFAULT_USER_AGENT},
        )
        self._runner = runner

    def extract(self, url: str) -> ExtractedContent:
        try:
            response = self._client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ExtractionError(f"failed to fetch {url}: {exc}") from exc

        text = self._run_defuddle(response.text, url)
        if not text.strip():
            raise ExtractionError(f"no extractable content at {url}")

        return ExtractedContent(text=text, images=extract_image_urls(text))

    def _run_defuddle(self, html: str, url: str) -> str:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", encoding="utf-8", delete=False
        ) as tmp:
            tmp.write(html)
            tmp_path = Path(tmp.name)

        try:
            result = self._runner(
                ["npx", "--yes", "defuddle", "parse", str(tmp_path), "--markdown"],
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            raise ExtractionError(f"defuddle failed for {url}: {exc}") from exc
        finally:
            tmp_path.unlink(missing_ok=True)

        return result.stdout
