from datetime import UTC, datetime, timedelta

from wisdom_digest.models import DeliveryLog, Recipient, WisdomItem
from wisdom_digest.selector import select_items_for_recipients

NOW = datetime(2026, 6, 12, 9, 0, tzinfo=UTC)


def recipient(
    *,
    id: str = "recipient-1",
    status: str = "active",
    frequency: set[str] | None = None,
    preference_tags: set[str] | None = None,
    excluded_tags: set[str] | None = None,
    email: str = "person@example.com",
) -> Recipient:
    return Recipient(
        id=id,
        name="Synthetic Recipient",
        email=email,
        status=status,
        frequency=frequency or {"morning"},
        preference_tags=preference_tags or set(),
        excluded_tags=excluded_tags or set(),
    )


def item(
    *,
    id: str,
    status: str = "active",
    importance: int = 3,
    tags: set[str] | None = None,
    audience: set[str] | None = None,
    text: str = "Synthetic wisdom text.",
    min_repeat_days: int = 90,
) -> WisdomItem:
    return WisdomItem(
        id=id,
        title=f"Synthetic {id}",
        text=text,
        status=status,
        importance=importance,
        tags=tags or set(),
        audience=audience or set(),
        min_repeat_days=min_repeat_days,
    )


def log(
    *,
    recipient_id: str = "recipient-1",
    wisdom_item_id: str,
    days_ago: int,
    status: str = "sent",
) -> DeliveryLog:
    return DeliveryLog(
        recipient_id=recipient_id,
        wisdom_item_id=wisdom_item_id,
        sent_at=NOW - timedelta(days=days_ago),
        slot="morning",
        status=status,
    )


def select(
    recipients: list[Recipient],
    items: list[WisdomItem],
    logs: list[DeliveryLog] | None = None,
) -> list[str]:
    return [
        result.wisdom_item_id
        for result in select_items_for_recipients(
            recipients,
            items,
            logs or [],
            "morning",
            now=NOW,
        )
    ]


def test_inactive_recipients_are_skipped():
    assert select([recipient(status="paused")], [item(id="item-1")]) == []


def test_recipients_not_subscribed_to_current_slot_are_skipped():
    assert select([recipient(frequency={"evening"})], [item(id="item-1")]) == []


def test_invalid_recipient_email_is_skipped():
    assert select([recipient(email="not-an-email")], [item(id="item-1")]) == []


def test_inactive_and_pending_review_items_are_excluded():
    results = select(
        [recipient()],
        [
            item(id="archived", status="archived", importance=5),
            item(id="pending", status="pending_review", importance=5),
            item(id="active", importance=1),
        ],
    )

    assert results == ["active"]


def test_empty_text_items_are_excluded():
    assert select([recipient()], [item(id="blank", text="  ")]) == []


def test_excluded_tags_block_items():
    results = select(
        [recipient(excluded_tags={"investing"})],
        [
            item(id="blocked", tags={"investing"}, importance=5),
            item(id="allowed", tags={"career"}, importance=1),
        ],
    )

    assert results == ["allowed"]


def test_preference_tags_increase_score():
    results = select(
        [recipient(preference_tags={"discipline"})],
        [
            item(id="plain", importance=3),
            item(id="matched", importance=3, tags={"discipline"}),
        ],
    )

    assert results == ["matched"]


def test_audience_tags_increase_score():
    results = select(
        [recipient(preference_tags={"career"})],
        [
            item(id="plain", importance=3),
            item(id="audience", importance=3, audience={"career"}),
        ],
    )

    assert results == ["audience"]


def test_items_inside_min_repeat_days_are_excluded():
    results = select(
        [recipient()],
        [
            item(id="recent", importance=5, min_repeat_days=90),
            item(id="fresh", importance=1),
        ],
        [log(wisdom_item_id="recent", days_ago=30)],
    )

    assert results == ["fresh"]


def test_never_sent_items_are_preferred_over_frequently_sent_items():
    results = select(
        [recipient()],
        [
            item(id="frequent", importance=3, min_repeat_days=0),
            item(id="never", importance=3),
        ],
        [
            log(wisdom_item_id="frequent", days_ago=100),
            log(wisdom_item_id="frequent", days_ago=120),
        ],
    )

    assert results == ["never"]


def test_higher_importance_wins_when_other_factors_are_equal():
    results = select(
        [recipient()],
        [
            item(id="low", importance=2),
            item(id="high", importance=5),
        ],
    )

    assert results == ["high"]


def test_tie_breaking_is_deterministic_by_item_id():
    results = select(
        [recipient()],
        [
            item(id="item-b", importance=3),
            item(id="item-a", importance=3),
        ],
    )

    assert results == ["item-a"]


def test_tie_breaking_prefers_older_last_sent_after_repeat_window():
    results = select(
        [recipient()],
        [
            item(id="newer", importance=3, min_repeat_days=0),
            item(id="older", importance=3, min_repeat_days=0),
        ],
        [
            log(wisdom_item_id="newer", days_ago=100),
            log(wisdom_item_id="older", days_ago=200),
        ],
    )

    assert results == ["older"]


def test_failed_and_dry_run_logs_do_not_count_as_successful_sends():
    results = select(
        [recipient()],
        [
            item(id="logged", importance=3),
            item(id="other", importance=3),
        ],
        [
            log(wisdom_item_id="logged", days_ago=1, status="failed"),
            log(wisdom_item_id="logged", days_ago=1, status="dry_run"),
        ],
    )

    assert results == ["logged"]


def test_selection_returns_one_result_per_eligible_recipient():
    results = select_items_for_recipients(
        [
            recipient(id="recipient-1"),
            recipient(id="recipient-2", preference_tags={"career"}),
        ],
        [
            item(id="general", importance=3),
            item(id="career", importance=3, tags={"career"}),
        ],
        [],
        "morning",
        now=NOW,
    )

    assert [(result.recipient_id, result.wisdom_item_id) for result in results] == [
        ("recipient-1", "career"),
        ("recipient-2", "career"),
    ]
    assert all("importance=3" in result.reason for result in results)


def test_naive_delivery_log_datetimes_are_treated_as_utc():
    naive_sent_at = (NOW - timedelta(days=1)).replace(tzinfo=None)

    results = select_items_for_recipients(
        [recipient()],
        [item(id="recent", importance=5), item(id="fresh", importance=1)],
        [
            DeliveryLog(
                recipient_id="recipient-1",
                wisdom_item_id="recent",
                sent_at=naive_sent_at,
                slot="morning",
                status="sent",
            )
        ],
        "morning",
        now=NOW,
    )

    assert [result.wisdom_item_id for result in results] == ["fresh"]
