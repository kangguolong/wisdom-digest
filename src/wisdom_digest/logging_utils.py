"""Logging helpers."""

from __future__ import annotations

import logging


def mask_email(email: str) -> str:
    """Mask an email address for logs and delivery records."""
    local, separator, domain = email.partition("@")
    if not separator or not domain:
        return "***"

    if len(local) <= 2:
        return f"***@{domain}"

    return f"{local[0]}***{local[-1]}@{domain}"


def configure_logging(level: str = "INFO") -> None:
    """Configure process logging with a simple safe default format."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
