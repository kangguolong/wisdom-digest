"""Notion gateway interface."""

from __future__ import annotations

from wisdom_digest.config import Settings
from wisdom_digest.models import DeliveryLog, Recipient, WisdomItem


class NotionGateway:
    """Thin gateway for future Notion database operations."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def fetch_wisdom_items(self) -> list[WisdomItem]:
        raise NotImplementedError("Notion reads are implemented in Phase 3.")

    def fetch_recipients(self) -> list[Recipient]:
        raise NotImplementedError("Notion reads are implemented in Phase 3.")

    def fetch_recent_delivery_logs(self) -> list[DeliveryLog]:
        raise NotImplementedError("Notion reads are implemented in Phase 3.")

    def write_delivery_log(self, delivery_log: DeliveryLog) -> None:
        _ = delivery_log
        raise NotImplementedError("Notion writes are implemented in Phase 3.")
