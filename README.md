# Wisdom Digest

Wisdom Digest is a lightweight personal wisdom delivery system.

It stores curated wisdom items in Notion, selects relevant items for active recipients, sends a clean HTML email through Gmail, and records delivery history back to Notion.

The project is designed for a small trusted group, such as the maintainer, spouse, and invited friends. It is not a SaaS product.

## V1 Architecture

```text
Notion
  - Wisdom Items
  - Recipients
  - Delivery Logs
        ↓
GitHub Actions cron
        ↓
Python app
        ↓
Gmail SMTP
        ↓
Recipients
```

## V1 Scope

V1 includes:

- Notion content storage.
- Multi-recipient delivery.
- Recipient-level subscription slots.
- Morning, noon, and evening scheduled sends.
- Deterministic selection logic.
- HTML email with plain-text fallback.
- Gmail SMTP delivery.
- Dry-run mode.
- Delivery logs.
- GitHub Actions automation.

V1 does not include:

- AI quote sourcing.
- AI ranking.
- External quote scraping.
- Public signup page.
- Web UI.
- User login.
- SaaS functionality.

## Schedule

Default delivery times are Singapore time:

| Slot | Asia/Singapore | UTC cron |
|---|---:|---:|
| morning | 09:00 | `0 1 * * *` |
| noon | 13:00 | `0 5 * * *` |
| evening | 18:00 | `0 10 * * *` |

GitHub Actions cron uses UTC.

## Documentation

Start here:

- `docs/v1-build-spec.md` — main implementation specification.
- `docs/notion-schema.md` — required Notion database schema.
- `docs/selection-logic.md` — deterministic V1 selection logic.
- `docs/email-template-spec.md` — HTML and plain-text email requirements.
- `docs/security-model.md` — security and privacy rules.
- `docs/codex-prompts.md` — prompts for phased Codex implementation.

## Environment

Copy `.env.example` to `.env` for local development.

```bash
cp .env.example .env
```

Never commit `.env`.

Required variables:

```text
NOTION_API_KEY
NOTION_WISDOM_DATABASE_ID
NOTION_RECIPIENTS_DATABASE_ID
NOTION_DELIVERY_LOGS_DATABASE_ID
GMAIL_USER
GMAIL_APP_PASSWORD
```

For GitHub Actions, configure these as GitHub Secrets.

## Safety Defaults

- `DRY_RUN=true` should be used for local setup and first test runs.
- Real recipient emails should live only in Notion, not in the repository.
- Real Notion database IDs should live only in local `.env` or GitHub Secrets.
- Logs should mask recipient emails.
- Tests should use synthetic data only.

## Implementation Workflow

Recommended workflow:

1. Read `docs/v1-build-spec.md`.
2. Ask Codex to produce an implementation plan without writing code.
3. Review the plan against V1 scope.
4. Implement in phases using `docs/codex-prompts.md`.
5. Review security before enabling real sends.
6. Keep the repository private until secrets and sample data are verified safe.

## License

License has not been finalized yet.
