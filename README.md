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

Default delivery times are New Zealand time using the IANA timezone `Pacific/Auckland`.
New Zealand observes daylight saving time, so GitHub Actions should run at both possible UTC candidate times and let the application confirm the current local slot.

| Slot | Pacific/Auckland | NZST UTC+12 | NZDT UTC+13 | Candidate UTC cron |
|---|---:|---:|---:|---:|
| morning | 09:00 | 21:00 previous day | 20:00 previous day | `0 20,21 * * *` |
| noon | 13:00 | 01:00 same day | 00:00 same day | `0 0,1 * * *` |
| evening | 18:00 | 06:00 same day | 05:00 same day | `0 5,6 * * *` |

GitHub Actions cron uses UTC. Candidate runs that do not match the current Auckland local slot should exit cleanly without sending email or writing delivery logs.

## Documentation

Start here:

- `docs/v1-build-spec.md` — main implementation specification.
- `docs/notion-schema.md` — required Notion database schema.
- `docs/selection-logic.md` — deterministic V1 selection logic.
- `docs/email-template-spec.md` — HTML and plain-text email requirements.
- `docs/security-model.md` — security and privacy rules.
- `docs/codex-prompts.md` — prompts for phased Codex implementation.

## Environment

This project uses Python 3.11 and `uv` for dependency management.

Install dependencies:

```bash
uv sync --dev
```

Run tests and lint:

```bash
uv run pytest
uv run ruff check .
```

Run the local entrypoint:

```bash
uv run wisdom-digest
```

Current implementation status:

- Deterministic selection engine is implemented.
- Notion client parsing and delivery-log payload building are implemented.
- Email rendering and Gmail SMTP provider are implemented.
- Main workflow orchestration is the next implementation phase.

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
- `WRITE_DRY_RUN_LOGS=false` should be the default so local tests do not affect production selection history.
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
