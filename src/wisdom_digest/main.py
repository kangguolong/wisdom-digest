"""Command-line entrypoint for Wisdom Digest."""

from __future__ import annotations

import logging

from wisdom_digest.config import load_settings
from wisdom_digest.logging_utils import configure_logging

LOGGER = logging.getLogger(__name__)


def main() -> int:
    """Load configuration and exit without external side effects in Phase 1."""
    settings = load_settings(validate_required=False)
    configure_logging(settings.log_level)
    LOGGER.info(
        "Wisdom Digest skeleton loaded timezone=%s dry_run=%s write_dry_run_logs=%s",
        settings.default_timezone,
        settings.dry_run,
        settings.write_dry_run_logs,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
