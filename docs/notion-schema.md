# Notion Schema

This document defines the V1 Notion databases required by Wisdom Digest.

Use synthetic examples in public documentation. Do not commit real database IDs, real emails, real private notes, or real Notion links.

## 1. Wisdom Items Database

Purpose: stores curated wisdom content.

### Required Properties

| Property | Type | Required | Description |
|---|---|---:|---|
| `Title` | Title | Yes | Short internal title. |
| `Text` | Rich text | Yes | Main wisdom text shown in email. |
| `Status` | Select | Yes | `active`, `archived`, or `pending_review`. |
| `Importance` | Number | Yes | Integer from 1 to 5. Higher means more valuable. |

### Recommended Properties

| Property | Type | Required | Description |
|---|---|---:|---|
| `Author` | Rich text | No | Author or originator. |
| `Source` | Rich text | No | Book, article, personal note, or source context. |
| `Category` | Select | No | Broad category such as `career`, `health`, `relationships`, `investing`, `decision_making`, `philosophy`. |
| `Tags` | Multi-select | No | Content tags used for matching and filtering. |
| `Audience` | Multi-select | No | Intended audience tags such as `general`, `personal`, `family`, `career`, `investing`. |
| `Min Repeat Days` | Number | No | Minimum days before the same recipient can receive the same item again. Default: 90. |
| `Reflection Prompt` | Rich text | No | Optional custom prompt. If absent, use default prompt. |
| `Notes` | Rich text | No | Private context, not necessarily shown in email. |
| `Created At` | Created time | No | Notion-created timestamp. |

### Status Values

- `active`: eligible for delivery.
- `archived`: not eligible.
- `pending_review`: not eligible in V1 delivery.

### Notes

- `Text` is the canonical deliverable content.
- `Title` is for internal management and should not be treated as the digest text.
- `Audience` should use broad tags, not hardcoded recipient names.
- Private content can be tagged with `personal` or another maintainer-defined private tag.

## 2. Recipients Database

Purpose: stores people who can receive digest emails.

### Required Properties

| Property | Type | Required | Description |
|---|---|---:|---|
| `Name` | Title | Yes | Recipient display name. |
| `Email` | Email | Yes | Destination email address. Must not be committed to repo. |
| `Status` | Select | Yes | `active` or `paused`. |
| `Frequency` | Multi-select | Yes | Subscribed slots: `morning`, `noon`, `evening`. |

### Recommended Properties

| Property | Type | Required | Description |
|---|---|---:|---|
| `Preference Tags` | Multi-select | No | Tags the recipient prefers. |
| `Excluded Tags` | Multi-select | No | Tags the recipient should not receive. |
| `Timezone` | Rich text | No | Defaults to `Pacific/Auckland` in V1. |
| `Personal Note` | Rich text | No | Internal note. Not used in V1 selection unless explicitly implemented later. |
| `Created At` | Created time | No | Notion-created timestamp. |

### Status Values

- `active`: eligible for delivery.
- `paused`: not eligible for delivery.

### Frequency Values

- `morning`
- `noon`
- `evening`

### Notes

- Do not assume all recipients want three emails per day.
- Default for friends should usually be `morning` only unless explicitly requested.
- Recipient emails are operational private data and must never appear in repository fixtures or logs unmasked.

## 3. Delivery Logs Database

Purpose: stores one event per attempted digest delivery.

### Required Properties

| Property | Type | Required | Description |
|---|---|---:|---|
| `Title` | Title | Yes | Synthetic title, e.g. `2026-06-06 morning abc123`. |
| `Recipient` | Relation | Yes | Relation to Recipients database. |
| `Wisdom Item` | Relation | Yes | Relation to Wisdom Items database. |
| `Sent At` | Date | Yes | Attempt timestamp. |
| `Slot` | Select | Yes | `morning`, `noon`, or `evening`. |
| `Status` | Select | Yes | `sent`, `failed`, or `dry_run`. |

### Recommended Properties

| Property | Type | Required | Description |
|---|---|---:|---|
| `Email Masked` | Rich text | No | Masked email, e.g. `p***r@example.com`. |
| `Error` | Rich text | No | Sanitized failure reason. Must not contain secrets or full payloads. |
| `Message ID` | Rich text | No | Provider message ID if available. |
| `Created At` | Created time | No | Notion-created timestamp. |

### Status Values

- `sent`: email send completed.
- `failed`: email send failed.
- `dry_run`: selection/rendering completed, but no email was sent.

### Notes

- Delivery history must be event-based.
- Do not store recipient-specific sent counts on Wisdom Items.
- The selector should derive recipient-specific send history from Delivery Logs.
- Delivery Logs may grow over time; V1 should query only the recent history window needed for repeat control and scoring.
- Dry-run logs should be optional and disabled by default. If written, they must use status `dry_run` and must not affect production selection history by default.

## 4. Schema Compatibility Rules

The application should fail clearly when required properties are missing or incompatible.

Recommended behavior:

- Missing required database ID: fail at startup.
- Missing required Notion property: fail with a schema mismatch error.
- Missing optional property: use a safe default.
- Unknown select value: treat as ineligible or fail clearly, depending on risk.
- Empty recipient email: skip recipient and log sanitized warning.

## 5. Synthetic Test Data Example

Use fake data only:

```json
{
  "title": "Long-term thinking",
  "text": "Small actions compound when repeated with judgment.",
  "author": "Synthetic Example",
  "source": "Sample Fixture",
  "category": "decision_making",
  "tags": ["compounding", "discipline"],
  "audience": ["general"],
  "importance": 4,
  "status": "active",
  "min_repeat_days": 90
}
```
