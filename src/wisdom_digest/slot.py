"""Delivery slot definitions."""

from __future__ import annotations

from datetime import time

from wisdom_digest.config import DEFAULT_TIMEZONE
from wisdom_digest.models import Slot


SLOT_TIMES = {
    Slot.MORNING: time(hour=9),
    Slot.NOON: time(hour=13),
    Slot.EVENING: time(hour=18),
}

CANDIDATE_UTC_CRONS = {
    Slot.MORNING: "0 20,21 * * *",
    Slot.NOON: "0 0,1 * * *",
    Slot.EVENING: "0 5,6 * * *",
}


def normalize_slot(value: str) -> Slot:
    """Convert a user-provided slot string to a Slot enum."""
    return Slot(value.strip().lower())


def infer_current_slot(timezone_name: str = DEFAULT_TIMEZONE) -> Slot | None:
    """Infer the current slot.

    Full Auckland-aware slot inference is implemented in Phase 5.
    """
    _ = timezone_name
    raise NotImplementedError("Slot inference is implemented in Phase 5.")
