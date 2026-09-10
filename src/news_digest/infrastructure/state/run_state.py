from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from pydantic import BaseModel, ValidationError

# feed-ingestion: first-ever run has no prior success to look back from.
DEFAULT_LOOKBACK = timedelta(hours=48)


class RunStateData(BaseModel):
    last_success: datetime


class RunState:
    """Persists the last-successful-run timestamp for the ingestion lookback window.

    feed-ingestion: a missed scheduled run self-heals because the next run's
    lookback is always "since the last recorded success," however long ago
    that was — never a fixed rolling window.
    """

    def __init__(self, path: Path) -> None:
        self._path = path

    def last_success(self) -> datetime | None:
        if not self._path.exists():
            return None
        # feed-ingestion: a state file left empty or truncated (e.g. a crash
        # mid-write) is treated the same as no prior run — self-heal with the
        # 48-hour default lookback rather than crash the whole pipeline.
        try:
            return RunStateData.model_validate_json(self._path.read_text()).last_success
        except ValidationError:
            return None

    def lookback_since(self, now: datetime | None = None) -> datetime:
        now = now or datetime.now(UTC)
        last = self.last_success()
        return last if last is not None else now - DEFAULT_LOOKBACK

    def record_success(self, at: datetime | None = None) -> None:
        at = at or datetime.now(UTC)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(RunStateData(last_success=at).model_dump_json())
