from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from news_digest.application.ports import DeliveryError, DigestDelivery


class DeliveryResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    target: str
    succeeded: bool
    error: str | None = None


def deliver_to_all(
    targets: dict[str, tuple[DigestDelivery, bytes]],
    generated_at: datetime,
) -> list[DeliveryResult]:
    """digest-delivery: each target is attempted independently, with its own
    pre-rendered content (email gets the EPUB, Obsidian gets the Markdown
    note) — one failing is reported, not allowed to block the others."""
    results = []
    for name, (delivery, rendered) in targets.items():
        try:
            delivery.deliver(rendered, generated_at)
        except DeliveryError as exc:
            results.append(DeliveryResult(target=name, succeeded=False, error=str(exc)))
        else:
            results.append(DeliveryResult(target=name, succeeded=True))
    return results
