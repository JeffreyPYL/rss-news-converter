from __future__ import annotations

from datetime import datetime
from pathlib import Path

from news_digest.application.ports import DeliveryError
from news_digest.infrastructure.delivery._filenames import timestamped
from news_digest.infrastructure.settings import Settings

DEFAULT_NOTE_FILENAME = "News Digest.md"


class ObsidianVaultDelivery:
    """digest-delivery: writes the rendered note into a configured Obsidian
    vault path, one file per run (see `timestamped`) rather than overwriting."""

    def __init__(
        self, vault_path: Path, note_filename: str = DEFAULT_NOTE_FILENAME
    ) -> None:
        self._vault_path = vault_path
        self._note_filename = note_filename

    def deliver(self, rendered: bytes, generated_at: datetime) -> None:
        try:
            self._vault_path.mkdir(parents=True, exist_ok=True)
            filename = timestamped(generated_at, self._note_filename)
            (self._vault_path / filename).write_bytes(rendered)
        except OSError as exc:
            raise DeliveryError(
                f"failed to write to vault at {self._vault_path}: {exc}"
            ) from exc


def obsidian_vault_delivery_from_env(
    settings: Settings | None = None,
) -> ObsidianVaultDelivery:
    """Vault path deferred to an env var (or a `.env` file — see `Settings`),
    per the earlier "do it later" decision."""
    settings = settings or Settings()
    if settings.obsidian_vault_path is None:
        raise ValueError(
            "missing required environment variable: NEWS_DIGEST_OBSIDIAN_VAULT_PATH"
        )
    return ObsidianVaultDelivery(vault_path=settings.obsidian_vault_path)
