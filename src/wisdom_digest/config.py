"""Runtime configuration for Wisdom Digest."""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_TIMEZONE = "Pacific/Auckland"
DEFAULT_DRY_RUN = True
DEFAULT_WRITE_DRY_RUN_LOGS = False

REQUIRED_SECRET_NAMES = (
    "NOTION_API_KEY",
    "NOTION_WISDOM_DATABASE_ID",
    "NOTION_RECIPIENTS_DATABASE_ID",
    "NOTION_DELIVERY_LOGS_DATABASE_ID",
    "GMAIL_USER",
    "GMAIL_APP_PASSWORD",
)


def parse_bool(value: str | None, default: bool = False) -> bool:
    """Parse an environment-style boolean value."""
    if value is None or value == "":
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False

    raise ValueError(f"Invalid boolean value: {value!r}")


@dataclass(frozen=True)
class Settings:
    notion_api_key: str | None
    notion_wisdom_database_id: str | None
    notion_recipients_database_id: str | None
    notion_delivery_logs_database_id: str | None
    gmail_user: str | None
    gmail_app_password: str | None
    default_timezone: str = DEFAULT_TIMEZONE
    dry_run: bool = DEFAULT_DRY_RUN
    write_dry_run_logs: bool = DEFAULT_WRITE_DRY_RUN_LOGS
    digest_slot: str | None = None
    log_level: str = "INFO"

    def missing_required_secrets(self) -> tuple[str, ...]:
        values = {
            "NOTION_API_KEY": self.notion_api_key,
            "NOTION_WISDOM_DATABASE_ID": self.notion_wisdom_database_id,
            "NOTION_RECIPIENTS_DATABASE_ID": self.notion_recipients_database_id,
            "NOTION_DELIVERY_LOGS_DATABASE_ID": self.notion_delivery_logs_database_id,
            "GMAIL_USER": self.gmail_user,
            "GMAIL_APP_PASSWORD": self.gmail_app_password,
        }
        return tuple(name for name in REQUIRED_SECRET_NAMES if not values[name])


def load_settings(validate_required: bool = False) -> Settings:
    """Load settings from environment variables."""
    settings = Settings(
        notion_api_key=os.getenv("NOTION_API_KEY"),
        notion_wisdom_database_id=os.getenv("NOTION_WISDOM_DATABASE_ID"),
        notion_recipients_database_id=os.getenv("NOTION_RECIPIENTS_DATABASE_ID"),
        notion_delivery_logs_database_id=os.getenv("NOTION_DELIVERY_LOGS_DATABASE_ID"),
        gmail_user=os.getenv("GMAIL_USER"),
        gmail_app_password=os.getenv("GMAIL_APP_PASSWORD"),
        default_timezone=os.getenv("DEFAULT_TIMEZONE") or DEFAULT_TIMEZONE,
        dry_run=parse_bool(os.getenv("DRY_RUN"), DEFAULT_DRY_RUN),
        write_dry_run_logs=parse_bool(
            os.getenv("WRITE_DRY_RUN_LOGS"),
            DEFAULT_WRITE_DRY_RUN_LOGS,
        ),
        digest_slot=os.getenv("DIGEST_SLOT") or None,
        log_level=os.getenv("LOG_LEVEL") or "INFO",
    )

    if validate_required:
        missing = settings.missing_required_secrets()
        if missing:
            names = ", ".join(missing)
            raise RuntimeError(f"Missing required environment variables: {names}")

    return settings
