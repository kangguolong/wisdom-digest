"""Deterministic wisdom item selection interface."""

from __future__ import annotations

from collections.abc import Iterable

from wisdom_digest.models import DeliveryLog, Recipient, SelectionResult, WisdomItem


def select_items_for_recipients(
    recipients: Iterable[Recipient],
    wisdom_items: Iterable[WisdomItem],
    delivery_logs: Iterable[DeliveryLog],
    current_slot: str,
) -> list[SelectionResult]:
    """Select one wisdom item per eligible recipient.

    The deterministic scoring engine is implemented in Phase 2.
    """
    _ = (recipients, wisdom_items, delivery_logs, current_slot)
    raise NotImplementedError("Selection engine is implemented in Phase 2.")
