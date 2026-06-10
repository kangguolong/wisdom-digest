"""Application data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class Slot(StrEnum):
    MORNING = "morning"
    NOON = "noon"
    EVENING = "evening"


class DeliveryStatus(StrEnum):
    SENT = "sent"
    FAILED = "failed"
    DRY_RUN = "dry_run"


@dataclass(frozen=True)
class Recipient:
    id: str
    name: str
    email: str
    status: str
    frequency: set[str] = field(default_factory=set)
    preference_tags: set[str] = field(default_factory=set)
    excluded_tags: set[str] = field(default_factory=set)
    timezone: str | None = None


@dataclass(frozen=True)
class WisdomItem:
    id: str
    title: str
    text: str
    status: str
    importance: int
    tags: set[str] = field(default_factory=set)
    audience: set[str] = field(default_factory=set)
    category: str | None = None
    author: str | None = None
    source: str | None = None
    min_repeat_days: int = 90
    reflection_prompt: str | None = None


@dataclass(frozen=True)
class DeliveryLog:
    recipient_id: str
    wisdom_item_id: str
    sent_at: datetime
    slot: str
    status: str


@dataclass(frozen=True)
class SelectionResult:
    recipient_id: str
    wisdom_item_id: str
    score: float
    reason: str
