"""Delivery slot definitions."""

from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

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


def infer_current_slot(
    timezone_name: str = DEFAULT_TIMEZONE,
    now: datetime | None = None,
) -> Slot | None:
    """Infer the slot from the current local time in the configured timezone."""
    reference_time = now or datetime.now(tz=ZoneInfo(timezone_name))
    local_time = reference_time.astimezone(ZoneInfo(timezone_name))

    for slot, slot_time in SLOT_TIMES.items():
        if local_time.hour == slot_time.hour and local_time.minute == slot_time.minute:
            return slot

    return None
