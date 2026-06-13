"""Command-line entrypoint for Wisdom Digest."""

from __future__ import annotations

import logging

from wisdom_digest.config import load_settings
from wisdom_digest.logging_utils import configure_logging
from wisdom_digest.workflow import run_digest

LOGGER = logging.getLogger(__name__)


def main() -> int:
    """Run the Wisdom Digest workflow."""
    settings = load_settings(validate_required=False)
    configure_logging(settings.log_level)
    result = run_digest(settings)
    LOGGER.info("Wisdom Digest completed result=%s", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
