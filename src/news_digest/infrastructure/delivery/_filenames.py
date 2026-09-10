from __future__ import annotations

from datetime import datetime


def timestamped(generated_at: datetime, name: str) -> str:
    """digest-delivery: every delivered file is named with when it was
    generated (date prefix, then time with no seconds), so successive runs
    don't overwrite each other and a reader can tell which digest is which."""
    return f"{generated_at:%Y-%m-%d %H%M} {name}"
