# Wisdom Digest V1 Build Spec

## 1. Purpose

Wisdom Digest is a lightweight, open-source personal wisdom delivery system.

The system stores curated wisdom items in Notion, selects relevant items for active recipients, renders a clean HTML email, sends it through Gmail, and records delivery history.

This is not a SaaS product. V1 is designed for a small trusted group such as the maintainer, spouse, and invited friends.

## 2. V1 Architecture

```text
Notion databases
  - Wisdom Items
  - Recipients
  - Delivery Logs
        ↓
GitHub Actions scheduled workflow
        ↓
Python application
  - load config
  - read Notion data
  - determine current slot
  - select one wisdom item per eligible recipient
  - render HTML and plain-text email
  - send through Gmail SMTP
  - write delivery log
        ↓
Recipients receive digest email
```

## 3. V1 Scope

V1 must implement:

- Notion-based content storage.
- Notion-based recipient management.
- Notion-based delivery logs.
- Multi-recipient email delivery.
- Recipient-level subscription slots.
- Scheduled runs at morning, noon, and evening New Zealand time using `Pacific/Auckland`.
- Deterministic selection logic.
- HTML email rendering with plain-text fallback.
- Gmail SMTP delivery using app password.
- Dry-run mode.
- Environment-variable configuration.
- GitHub Actions workflow.
- Tests for selection logic, Notion parsing, and template rendering.
- Safe logging with masked sensitive data.

## 4. V1 Non-Goals

Do not implement in V1:

- AI quote sourcing.
- AI ranking.
- External quote scraping.
- Public subscription page.
- Web UI.
- User login.
- Payment or SaaS features.
- Admin dashboard.
- Database beyond Notion.
- Gmail OAuth.
- SendGrid, Resend, Postmark, or SES.
- Mobile push notifications.
- WhatsApp or Telegram delivery.

## 5. Runtime Slots

The system supports three delivery slots in `Pacific/Auckland` local time:

| Slot | Pacific/Auckland | NZST UTC+12 | NZDT UTC+13 | Candidate UTC cron |
|---|---:|---:|---:|---:|
| morning | 09:00 | 21:00 previous day | 20:00 previous day | `0 20,21 * * *` |
| noon | 13:00 | 01:00 same day | 00:00 same day | `0 0,1 * * *` |
| evening | 18:00 | 06:00 same day | 05:00 same day | `0 5,6 * * *` |

GitHub Actions cron runs in UTC. Because Auckland switches between NZST and NZDT, the workflow must run at the candidate UTC hours above. The application must support either:

1. an explicit `DIGEST_SLOT` environment variable; or
2. automatic slot inference from the current `Pacific/Auckland` local time.

Candidate cron runs that do not map to a real local slot must exit cleanly without sending email or writing delivery logs.

Manual runs through `workflow_dispatch` should support setting `DIGEST_SLOT` when possible.

## 6. Environment Variables

Required runtime variables:

```env
NOTION_API_KEY=
NOTION_WISDOM_DATABASE_ID=
NOTION_RECIPIENTS_DATABASE_ID=
NOTION_DELIVERY_LOGS_DATABASE_ID=
GMAIL_USER=
GMAIL_APP_PASSWORD=
DEFAULT_TIMEZONE=Pacific/Auckland
DRY_RUN=true
WRITE_DRY_RUN_LOGS=false
```

Optional variables:

```env
DIGEST_SLOT=
LOG_LEVEL=INFO
```

Rules:

- All secrets must come from environment variables.
- GitHub Actions must read secrets from GitHub Secrets.
- No real API keys, passwords, Notion IDs, or recipient emails may be committed.
- `DRY_RUN` should default to `true` in local examples.
- `WRITE_DRY_RUN_LOGS` should default to `false` so dry-run tests do not affect production selection history.

## 7. Data Model Summary

V1 uses three Notion databases:

1. Wisdom Items
2. Recipients
3. Delivery Logs

Detailed schemas are defined in `docs/notion-schema.md`.

## 8. Selection Logic Summary

For each active recipient subscribed to the current slot:

1. Load active wisdom items.
2. Exclude items matching recipient excluded tags.
3. Prefer items matching recipient preference tags.
4. Avoid items sent recently to the same recipient.
5. Prefer lower recipient-specific sent count.
6. Use importance as a positive weight.
7. Select exactly one item when eligible items exist.

Detailed rules are defined in `docs/selection-logic.md`.

## 9. Email Requirements

Each email must include:

- Subject line.
- Digest slot label.
- Current date.
- Main wisdom text.
- Optional author.
- Optional source.
- Optional category.
- Reflection prompt.
- Minimal footer.
- Plain-text fallback.

Detailed requirements are defined in `docs/email-template-spec.md`.

## 10. Security Requirements

Security is a first-class V1 requirement because the repository may become public.

The implementation must:

- Never hardcode secrets.
- Never commit `.env`.
- Never commit real recipient emails.
- Never commit real Notion database IDs.
- Never print API keys or app passwords.
- Mask recipient emails in logs.
- Avoid logging full Notion API responses.
- Avoid logging full email body unless in explicit local dry-run debugging.
- Keep test fixtures fake and non-sensitive.
- Keep sample data synthetic.

Detailed rules are defined in `docs/security-model.md`.

## 11. Recommended Python Modules

```text
src/
  __init__.py
  main.py
  config.py
  models.py
  notion_client.py
  selector.py
  email_sender.py
  slot.py
  logging_utils.py
  templates/
    digest.html
```

## 12. Testing Requirements

Minimum tests:

- Selection filters inactive items.
- Selection filters inactive recipients.
- Selection respects subscribed slot.
- Selection respects excluded tags.
- Selection prefers matching preference tags.
- Selection avoids recently sent items.
- Selection prefers lower sent count.
- Selection uses importance weight.
- Notion parser handles missing optional fields.
- Notion parser fails clearly on required schema mismatch.
- Email template renders HTML and plain text without secrets.
- Dry-run mode does not send email.
- Slot inference handles both NZST and NZDT candidate UTC times.

## 13. Definition of Done

V1 is complete when:

- GitHub Actions can run on schedule and manually.
- A dry-run run completes without sending email.
- A real run can send one HTML email per eligible active recipient.
- Delivery Logs are written for sent and failed attempts. Dry-run logs are written only when explicitly configured and must not affect production selection by default.
- Selection tests pass.
- No secrets or real personal data are committed.
- README explains setup clearly.
- SECURITY.md explains safe usage and disclosure policy.

## 14. Future V2 Direction

V2 may add AI-assisted external wisdom candidate discovery, but candidates must enter a pending review queue before becoming active.

V2 must not automatically push unreviewed external quotes to recipients.
