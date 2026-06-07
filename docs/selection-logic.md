# Selection Logic

This document defines the deterministic V1 selection engine.

V1 must not use AI ranking, embeddings, external scraping, or opaque recommendation logic.

## 1. Goal

For each active recipient subscribed to the current slot, select exactly one eligible wisdom item when available.

The selector should optimize for:

1. Relevance to recipient preferences.
2. Avoiding recent repetition.
3. Under-sent items.
4. Higher importance.
5. Simple, inspectable behavior.

## 2. Inputs

The selector receives plain application objects, not raw Notion responses.

### Recipient

Required fields:

```python
Recipient(
    id: str,
    name: str,
    email: str,
    status: str,
    frequency: set[str],
    preference_tags: set[str],
    excluded_tags: set[str],
    timezone: str | None,
)
```

### Wisdom Item

Required fields:

```python
WisdomItem(
    id: str,
    title: str,
    text: str,
    status: str,
    importance: int,
    tags: set[str],
    audience: set[str],
    category: str | None,
    author: str | None,
    source: str | None,
    min_repeat_days: int,
    reflection_prompt: str | None,
)
```

### Delivery Log

Required fields:

```python
DeliveryLog(
    recipient_id: str,
    wisdom_item_id: str,
    sent_at: datetime,
    slot: str,
    status: str,
)
```

Only `sent` logs count as production delivery history for repetition control by default. Failed attempts must not count as successful delivery. Dry-run logs may exist when explicitly configured, but they must remain distinguishable from `sent` logs and must not affect production selection unless a future configuration explicitly opts into that behavior.

## 3. Recipient Eligibility

A recipient is eligible when:

- `status == "active"`
- current slot is included in `frequency`
- email is present and syntactically usable

If a recipient is inactive or not subscribed to the current slot, skip them.

## 4. Wisdom Item Eligibility

A wisdom item is eligible when:

- `status == "active"`
- `text` is not empty
- item tags do not intersect recipient excluded tags
- item is not within its recipient-specific minimum repeat window

`pending_review` and `archived` items must not be sent.

## 5. Repeat Control

Repeat control is recipient-specific and derived from Delivery Logs.

For a candidate item and recipient:

1. Find the most recent successful `sent` log for the same recipient and item.
2. If no log exists, item is not repeated.
3. If last sent date is within `min_repeat_days`, item is ineligible.
4. If `min_repeat_days` is missing, default to 90.

## 6. Scoring

After hard filters, calculate score:

```text
score =
  importance * 10
  + preference_tag_match_count * 5
  + audience_tag_match_count * 3
  - sent_count_to_recipient * 8
  - recent_soft_penalty
```

Where:

```text
recent_soft_penalty =
  30 if sent to recipient within last 30 days
  10 if sent to recipient within last 90 days
  0 otherwise
```

The hard repeat filter should normally prevent same-item repetition within `min_repeat_days`. The soft penalty is still useful when `min_repeat_days` is low or when future rules use category-level repetition. `sent_count_to_recipient` and `recent_soft_penalty` should be calculated from successful production delivery history by default.

## 7. Tag Matching

- `preference_tag_match_count` is the count of item tags that intersect recipient preference tags.
- `audience_tag_match_count` is the count of item audience tags that intersect recipient preference tags.
- If recipient has no preference tags, do not penalize general items.
- Items tagged `general` should be eligible for all recipients unless excluded.

## 8. Tie-breaking

If multiple candidates have the same score, tie-break deterministically:

1. Higher importance.
2. Lower sent count for recipient.
3. Older last sent date for recipient, with never-sent first.
4. Lexicographically smaller item ID.

No random selection in V1 unless explicitly seeded and tested. Determinism makes behavior easier to audit.

## 9. Output

For each eligible recipient, return either:

```python
SelectionResult(
    recipient_id: str,
    wisdom_item_id: str,
    score: float,
    reason: str,
)
```

or no result when no eligible item exists.

The reason should be concise and non-sensitive, e.g.:

```text
matched_tags=2 importance=4 sent_count=0
```

## 10. Required Test Cases

Implement tests for:

1. Inactive recipients are skipped.
2. Recipients not subscribed to current slot are skipped.
3. Inactive wisdom items are excluded.
4. Pending review items are excluded.
5. Excluded tags block items.
6. Preference tags increase score.
7. Audience tags increase score.
8. Items inside `min_repeat_days` are excluded.
9. Never-sent items are preferred over frequently sent items.
10. Higher importance wins when other factors are equal.
11. Tie-breaking is deterministic.
12. Failed delivery logs do not count as successful sends.

## 11. Explicit Non-Goals

Do not add:

- AI-based recommendation.
- Embedding similarity.
- External profile inference.
- Per-recipient learning model.
- Randomized exploration logic.
- Complex category balancing in V1.

These may be considered after V1 is stable.
