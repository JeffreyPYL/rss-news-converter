"""Entry point for the on-demand `/news-digest` command."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import UTC, datetime, timedelta

from news_digest.application.build_digest import build_digest
from news_digest.application.deliver_digest import deliver_to_all
from news_digest.application.ports import ArticleExtractor, DigestDelivery, FeedSource
from news_digest.infrastructure.delivery.dropbox_api_delivery import (
    dropbox_api_delivery_from_env,
)
from news_digest.infrastructure.delivery.email_delivery import email_delivery_from_env
from news_digest.infrastructure.delivery.google_drive_delivery import (
    google_drive_delivery_from_env,
)
from news_digest.infrastructure.delivery.obsidian_vault_delivery import (
    ObsidianVaultDelivery,
    obsidian_vault_delivery_from_env,
)
from news_digest.infrastructure.extraction.factory import get_extractor
from news_digest.infrastructure.feeds.rss_feed import RssFeedSource
from news_digest.infrastructure.rendering.epub_renderer import EpubRenderer
from news_digest.infrastructure.rendering.obsidian_renderer import ObsidianRenderer
from news_digest.infrastructure.settings import Settings
from news_digest.infrastructure.state.run_state import RunState

_SINCE_DURATION_RE = re.compile(r"^(\d+)([dh])$")
_SINCE_UNIT_TO_KWARG = {"d": "days", "h": "hours"}


def parse_since_duration(value: str) -> timedelta:
    """Parse a --since value like '3d' or '48h' into a timedelta.

    Raises argparse.ArgumentTypeError rather than ValueError so argparse
    reports it as a normal usage error (exit code 2) before main() builds
    any feed source, extractor, or delivery target.
    """
    match = _SINCE_DURATION_RE.fullmatch(value)
    if match is None:
        raise argparse.ArgumentTypeError(
            f"invalid --since duration {value!r}: expected e.g. '3d' or '48h'"
        )
    amount, unit = match.groups()
    return timedelta(**{_SINCE_UNIT_TO_KWARG[unit]: int(amount)})


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the news digest pipeline.")
    parser.add_argument(
        "--since",
        type=parse_since_duration,
        default=None,
        help=(
            "Override the lookback window with a relative duration, e.g. "
            "'3d' or '48h' (default: since the last successful run)"
        ),
    )
    return parser


def run_digest(
    feed_source: FeedSource,
    extractor: ArticleExtractor,
    state: RunState,
    email_delivery: DigestDelivery | None,
    obsidian_delivery: DigestDelivery | None,
    epub_copy_delivery: DigestDelivery | None = None,
    extra_epub_targets: dict[str, DigestDelivery] | None = None,
    since_override: datetime | None = None,
) -> int:
    """digest-triggers: the shared pipeline both the on-demand command and,
    once designed, the scheduled trigger invoke (see design.md's Open Questions
    for why the scheduled path isn't wired up yet).

    since_override, when given, replaces the state-derived lookback for this
    run only — state.record_success() below still fires unconditionally, so
    the next unoverridden run continues from this run's completion time."""
    since = since_override if since_override is not None else state.lookback_since()
    digest = build_digest(feed_source=feed_source, extractor=extractor, since=since)

    skipped = getattr(feed_source, "skipped", None)
    if skipped:
        print("Sources skipped this run:")
        for source in skipped:
            print(f"  - {source.outlet} ({source.url}): {source.reason}")

    epub_bytes = EpubRenderer().render(digest)
    markdown_bytes = ObsidianRenderer().render(digest)

    targets: dict[str, tuple[DigestDelivery, bytes]] = {}
    if email_delivery is not None:
        targets["email"] = (email_delivery, epub_bytes)
    if obsidian_delivery is not None:
        targets["obsidian"] = (obsidian_delivery, markdown_bytes)
    if epub_copy_delivery is not None:
        targets["epub_copy"] = (epub_copy_delivery, epub_bytes)
    for name, delivery in (extra_epub_targets or {}).items():
        targets[name] = (delivery, epub_bytes)

    if not targets:
        print("No delivery targets configured.")
        return 1

    generated_at = datetime.now(UTC)
    any_succeeded = False
    for result in deliver_to_all(targets, generated_at):
        if result.succeeded:
            print(f"Delivered to {result.target}.")
            any_succeeded = True
        else:
            print(f"Delivery to {result.target} failed: {result.error}")

    if any_succeeded:
        state.record_success()
        return 0
    return 1


def main() -> int:
    args = _build_arg_parser().parse_args()
    since_override = datetime.now(UTC) - args.since if args.since is not None else None

    settings = Settings()
    state = RunState(settings.state_path)

    try:
        email_delivery: DigestDelivery | None = email_delivery_from_env()
    except ValueError as exc:
        print(f"Email delivery not configured: {exc}")
        email_delivery = None

    try:
        obsidian_delivery: DigestDelivery | None = obsidian_vault_delivery_from_env(
            settings
        )
    except ValueError as exc:
        print(f"Obsidian delivery not configured: {exc}")
        obsidian_delivery = None

    epub_copy_delivery: DigestDelivery | None = None
    if settings.obsidian_vault_path is not None:
        # digest-delivery: a local copy of the exact EPUB emailed to Kindle,
        # saved alongside the Obsidian note — lets you check what a run
        # actually generated independent of whether the email itself arrived.
        epub_copy_delivery = ObsidianVaultDelivery(
            vault_path=settings.obsidian_vault_path, note_filename="digest.epub"
        )

    extra_epub_targets: dict[str, DigestDelivery] = {}
    if settings.dropbox_email_to is not None:
        try:
            extra_epub_targets["dropbox_email"] = email_delivery_from_env(
                settings, to_addr=settings.dropbox_email_to
            )
        except ValueError as exc:
            print(f"Dropbox email delivery not configured: {exc}")

    try:
        extra_epub_targets["dropbox_api"] = dropbox_api_delivery_from_env(settings)
    except ValueError as exc:
        print(f"Dropbox delivery not configured: {exc}")

    try:
        extra_epub_targets["google_drive"] = google_drive_delivery_from_env(settings)
    except ValueError as exc:
        print(f"Google Drive delivery not configured: {exc}")

    return run_digest(
        feed_source=RssFeedSource(),
        extractor=get_extractor(),
        state=state,
        email_delivery=email_delivery,
        obsidian_delivery=obsidian_delivery,
        epub_copy_delivery=epub_copy_delivery,
        extra_epub_targets=extra_epub_targets,
        since_override=since_override,
    )


if __name__ == "__main__":
    sys.exit(main())
