import re

_MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\((https?://[^)]+)\)")


def extract_image_urls(markdown_text: str) -> tuple[str, ...]:
    return tuple(_MARKDOWN_IMAGE_RE.findall(markdown_text))
