# Codex Guidance for Wisdom Digest

## Source of Truth

- Treat `docs/v1-build-spec.md` as the primary implementation spec.
- Use the supporting docs for exact behavior:
  - `docs/notion-schema.md` for Notion database shape.
  - `docs/selection-logic.md` for deterministic selection.
  - `docs/email-template-spec.md` for email rendering.
  - `docs/security-model.md` for safety requirements.
  - `docs/codex-prompts.md` for the intended implementation phases.
- If docs conflict, stop and surface the conflict before implementing.

## Product Scope

Wisdom Digest V1 is a small personal automation:

- Read curated wisdom items, recipients, and delivery logs from Notion.
- Select one eligible wisdom item per active subscribed recipient.
- Render calm HTML email with a plain-text fallback.
- Send through Gmail SMTP with an app password.
- Record delivery attempts back to Notion.
- Run locally and through GitHub Actions cron/manual dispatch.

Do not add V2 or SaaS features in V1:

- No AI quote sourcing, AI ranking, embeddings, scraping, or external discovery.
- No public signup, web UI, login, dashboard, payments, or multi-tenant behavior.
- No database beyond Notion.
- No Gmail OAuth or extra email providers unless the spec changes.

## Implementation Order

Follow the phased order in `docs/codex-prompts.md`:

1. Repository skeleton.
2. Deterministic selection engine.
3. Notion client and parsers.
4. Email rendering and Gmail SMTP.
5. Main workflow and GitHub Actions.
6. Security and maintainability review.

Keep changes scoped to the current phase unless the user explicitly asks to combine phases.

## Preferred Stack and Layout

- Use Python for the runtime.
- Prefer a small package under `src/`.
- Keep module responsibilities narrow: `config`, `models`, `selector`, `notion_client`, `email_sender`, `slot`, `logging_utils`, and `main`.
- Use Jinja2 for `src/templates/digest.html`.
- Use pytest for tests.
- Keep tests offline by default; mock Notion and SMTP.
- Use `uv` as the dependency manager. Keep `pyproject.toml` and `uv.lock` as the source of truth.
- Add dependencies only when they directly support V1. Runtime dependencies should stay limited to `notion-client`, `jinja2`, and `python-dotenv` unless the spec changes. Dev dependencies should stay limited to `pytest` and `ruff` for now.

## Scheduling Rules

- Default timezone is `Pacific/Auckland`.
- Preserve Auckland daylight-saving behavior by using timezone-aware datetimes.
- GitHub Actions should run at candidate UTC hours for both NZST and NZDT.
- The application must infer the actual slot from Auckland local time and exit cleanly when a candidate cron run does not match morning, noon, or evening.
- Keep `DIGEST_SLOT` available for manual runs.

## Security Rules

- Never commit real secrets, real recipient emails, real Notion database IDs, real Notion URLs, or private wisdom content.
- Keep `.env` local and ignored; commit only placeholder values in `.env.example`.
- Default local examples to `DRY_RUN=true`.
- Default `WRITE_DRY_RUN_LOGS=false`; dry-run logs must not affect production selection by default.
- Mask recipient emails in logs and delivery logs.
- Do not log API keys, app passwords, full Notion API responses, or full production email bodies.
- Use synthetic fixtures only.
- GitHub Actions must read sensitive values from GitHub Secrets and use least-privilege permissions.

## Verification Expectations

Before finishing implementation work:

- Run `uv run pytest` when a test suite exists.
- Run `uv run ruff check .` for Python changes.
- Confirm `.env` and credential files remain ignored.
- Check that fixtures and docs contain only synthetic emails, IDs, and content.
- Verify dry-run behavior before any real send path.
- Keep summaries explicit about any tests not run.
