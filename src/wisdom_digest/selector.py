"""Deterministic wisdom item selection."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime

from wisdom_digest.models import (
    DeliveryLog,
    DeliveryStatus,
    Recipient,
    SelectionResult,
    WisdomItem,
)


@dataclass(frozen=True)
class _CandidateScore:
    item: WisdomItem
    score: float
    preference_tag_match_count: int
    audience_tag_match_count: int
    sent_count: int
    last_sent_at: datetime | None

    @property
    def matched_tags(self) -> int:
        return self.preference_tag_match_count + self.audience_tag_match_count


def select_items_for_recipients(
    recipients: Iterable[Recipient],
    wisdom_items: Iterable[WisdomItem],
    delivery_logs: Iterable[DeliveryLog],
    current_slot: str,
    now: datetime | None = None,
) -> list[SelectionResult]:
    """Select one wisdom item per eligible recipient."""
    reference_time = _as_aware_utc(now or datetime.now(UTC))
    items = list(wisdom_items)
    sent_logs = _sent_logs(delivery_logs)
    results: list[SelectionResult] = []

    for recipient in recipients:
        if not _is_recipient_eligible(recipient, current_slot):
            continue

        candidates = [
            _score_candidate(recipient, item, sent_logs, reference_time)
            for item in items
            if _is_item_eligible(recipient, item, sent_logs, reference_time)
        ]
        if not candidates:
            continue

        best = min(candidates, key=_candidate_sort_key)
        results.append(
            SelectionResult(
                recipient_id=recipient.id,
                wisdom_item_id=best.item.id,
                score=best.score,
                reason=(
                    f"matched_tags={best.matched_tags} "
                    f"importance={best.item.importance} "
                    f"sent_count={best.sent_count}"
                ),
            )
        )

    return results


def _is_recipient_eligible(recipient: Recipient, current_slot: str) -> bool:
    return (
        recipient.status == "active"
        and current_slot in recipient.frequency
        and _has_usable_email(recipient.email)
    )


def _has_usable_email(email: str) -> bool:
    local, separator, domain = email.partition("@")
    return bool(local and separator and domain and "@" not in domain)


def _is_item_eligible(
    recipient: Recipient,
    item: WisdomItem,
    sent_logs: list[DeliveryLog],
    now: datetime,
) -> bool:
    if item.status != "active" or not item.text.strip():
        return False

    if item.tags & recipient.excluded_tags:
        return False

    last_sent_at = _last_sent_at(recipient.id, item.id, sent_logs)
    if last_sent_at is None:
        return True

    repeat_days = item.min_repeat_days if item.min_repeat_days is not None else 90
    days_since_last_sent = (now - last_sent_at).total_seconds() / 86_400
    return days_since_last_sent >= repeat_days


def _score_candidate(
    recipient: Recipient,
    item: WisdomItem,
    sent_logs: list[DeliveryLog],
    now: datetime,
) -> _CandidateScore:
    preference_tag_match_count = len(item.tags & recipient.preference_tags)
    audience_tag_match_count = len(item.audience & recipient.preference_tags)
    sent_count = _sent_count(recipient.id, item.id, sent_logs)
    last_sent_at = _last_sent_at(recipient.id, item.id, sent_logs)
    recent_soft_penalty = _recent_soft_penalty(last_sent_at, now)
    score = (
        item.importance * 10
        + preference_tag_match_count * 5
        + audience_tag_match_count * 3
        - sent_count * 8
        - recent_soft_penalty
    )
    return _CandidateScore(
        item=item,
        score=score,
        preference_tag_match_count=preference_tag_match_count,
        audience_tag_match_count=audience_tag_match_count,
        sent_count=sent_count,
        last_sent_at=last_sent_at,
    )


def _candidate_sort_key(candidate: _CandidateScore) -> tuple[object, ...]:
    return (
        -candidate.score,
        -candidate.item.importance,
        candidate.sent_count,
        candidate.last_sent_at is not None,
        candidate.last_sent_at or datetime.min.replace(tzinfo=UTC),
        candidate.item.id,
    )


def _recent_soft_penalty(last_sent_at: datetime | None, now: datetime) -> int:
    if last_sent_at is None:
        return 0

    days_since_last_sent = (now - last_sent_at).total_seconds() / 86_400
    if days_since_last_sent < 30:
        return 30
    if days_since_last_sent < 90:
        return 10
    return 0


def _sent_logs(delivery_logs: Iterable[DeliveryLog]) -> list[DeliveryLog]:
    return [
        DeliveryLog(
            recipient_id=log.recipient_id,
            wisdom_item_id=log.wisdom_item_id,
            sent_at=_as_aware_utc(log.sent_at),
            slot=log.slot,
            status=log.status,
        )
        for log in delivery_logs
        if log.status == DeliveryStatus.SENT
    ]


def _sent_count(
    recipient_id: str,
    wisdom_item_id: str,
    sent_logs: Iterable[DeliveryLog],
) -> int:
    return sum(
        1
        for log in sent_logs
        if log.recipient_id == recipient_id and log.wisdom_item_id == wisdom_item_id
    )


def _last_sent_at(
    recipient_id: str,
    wisdom_item_id: str,
    sent_logs: Iterable[DeliveryLog],
) -> datetime | None:
    matching_times = [
        log.sent_at
        for log in sent_logs
        if log.recipient_id == recipient_id and log.wisdom_item_id == wisdom_item_id
    ]
    return max(matching_times, default=None)


def _as_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
