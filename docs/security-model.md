# Security Model

Wisdom Digest may become a public repository, so V1 must be safe by default.

## 1. Threat Model

Primary risks:

1. Secret leakage through committed files.
2. Secret leakage through GitHub Actions logs.
3. Exposure of private recipient emails.
4. Exposure of private Notion workspace structure.
5. Accidental public sharing of private wisdom content.
6. Uncontrolled email sending during tests or development.
7. Over-broad provider credentials.

## 2. Sensitive Data

Never commit:

```text
NOTION_API_KEY
NOTION_WISDOM_DATABASE_ID
NOTION_RECIPIENTS_DATABASE_ID
NOTION_DELIVERY_LOGS_DATABASE_ID
GMAIL_USER
GMAIL_APP_PASSWORD
GMAIL_CLIENT_ID
GMAIL_CLIENT_SECRET
GMAIL_REFRESH_TOKEN
RECIPIENT_EMAILS
.env
.env.local
.env.production
credentials.json
token.json
secrets.json
real Notion page URLs
real private wisdom content
real delivery logs
```

## 3. Environment Variables

Use environment variables for all runtime configuration.

Local development:

- Use `.env` locally.
- Commit only `.env.example`.
- Default `DRY_RUN=true` in `.env.example`.
- Default `WRITE_DRY_RUN_LOGS=false` in `.env.example`.

GitHub Actions:

- Use GitHub Secrets for secrets.
- Do not echo secrets.
- Do not print full environment variables.
- Scheduled production runs use `DRY_RUN=false`; manual dispatch runs should default to `DRY_RUN=true`.

## 4. GitHub Actions Security

Workflow rules:

- Use least necessary permissions.
- Avoid printing full payloads.
- Keep manual `workflow_dispatch` runs defaulted to `DRY_RUN=true` for test runs.
- Scheduled production runs may use `DRY_RUN=false` after a controlled real send has been validated.
- Keep `WRITE_DRY_RUN_LOGS=false` unless dry-run audit records are intentionally needed.
- Use Node 24-compatible action versions and pin immutable third-party action tags where required, e.g. `actions/checkout@v6`, `actions/setup-python@v6`, and `astral-sh/setup-uv@v8.2.0`.
- Do not upload artifacts containing logs with private data.

Recommended workflow permissions:

```yaml
permissions:
  contents: read
```

## 5. Logging Rules

Logs may include:

- Current slot.
- Number of active recipients.
- Number of active wisdom items.
- Recipient internal ID.
- Wisdom item internal ID.
- Sanitized status.

Logs must not include:

- API keys.
- App passwords.
- Full recipient emails.
- Full Notion API responses.
- Full email body in production.
- Full exception payloads from external APIs if they contain request metadata.

## 6. Email Masking

Use email masking in logs and delivery logs.

Example:

```text
p***r@example.com
```

Rules:

- Preserve domain for operational debugging.
- Mask most of the local part.
- For very short local parts, use `***@domain.com`.

## 7. Gmail Security

V1 uses Gmail SMTP with app password.

Requirements:

- Gmail account must have 2FA enabled.
- Use a dedicated Gmail app password.
- Do not use the normal Gmail account password.
- Store app password only in local `.env` or GitHub Secrets.
- Rotate the app password if exposure is suspected.

Future provider abstraction may support Resend, Postmark, SES, or Gmail API OAuth, but those are not V1 requirements.

## 8. Notion Security

Requirements:

- Create a dedicated Notion integration for this project.
- Share only the required Notion databases with the integration.
- Do not grant workspace-wide access if avoidable.
- Do not commit real database IDs.
- Do not include real Notion URLs in docs or test fixtures.

## 9. Dry-Run Safety

`DRY_RUN=true` means:

- Select recipients.
- Select wisdom items.
- Render email.
- Do not send email.
- Write delivery log with status `dry_run` only if `WRITE_DRY_RUN_LOGS=true`.

The application should default safely in local examples. Dry-run logs must not affect production selection history unless explicitly configured in a future version.

## 10. Test Data Rules

Tests must use:

- Fake emails such as `user@example.com`.
- Fake Notion IDs.
- Synthetic wisdom content.
- Mocked Notion responses.
- Mocked SMTP sender.

Tests must not call real Notion or Gmail services by default.

## 11. Public Repo Checklist

Before making the repository public:

- Search for secrets.
- Search for real emails.
- Search for real Notion IDs.
- Search for `.env` files.
- Search for private notes.
- Confirm `.gitignore` blocks sensitive files.
- Confirm `.env.example` contains placeholders only.
- Confirm GitHub Actions logs are safe.
- Confirm README does not instruct users to commit secrets.
- Confirm SECURITY.md is present.

## 12. Incident Response

If a secret is committed:

1. Revoke or rotate the secret immediately.
2. Remove the secret from the repository.
3. Assume the secret is compromised even if the repository is private.
4. Review GitHub Actions logs for exposure.
5. Consider rewriting Git history only if necessary, but rotation is mandatory.

If recipient emails are exposed:

1. Remove the exposed data.
2. Notify affected recipients if appropriate.
3. Replace real examples with synthetic fixtures.
4. Add tests or checks to prevent recurrence.
