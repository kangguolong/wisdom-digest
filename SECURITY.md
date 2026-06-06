# Security Policy

## Supported Status

Wisdom Digest is an early-stage personal automation project.

Security issues should be treated seriously because the project interacts with:

- Notion API credentials.
- Gmail app passwords.
- Recipient email addresses.
- Private wisdom content.

## Reporting a Vulnerability

If you find a vulnerability, do not publish exploit details publicly before the maintainer has time to respond.

For now, report issues through a private channel to the repository maintainer. If the repository later becomes public and widely used, a dedicated security contact should be added here.

## Sensitive Data Rules

Never commit:

- `.env` files.
- API keys.
- Gmail app passwords.
- OAuth tokens.
- Real recipient emails.
- Real Notion database IDs.
- Real Notion page URLs.
- Private wisdom content.
- Real delivery logs.

Use `.env.example` for placeholders only.

## Runtime Secret Management

Local development:

- Store secrets in `.env`.
- Keep `.env` ignored by git.
- Use `DRY_RUN=true` by default.

GitHub Actions:

- Store secrets in GitHub Secrets.
- Do not print secrets in logs.
- Do not upload logs that contain sensitive data.

Required GitHub Secrets for V1:

```text
NOTION_API_KEY
NOTION_WISDOM_DATABASE_ID
NOTION_RECIPIENTS_DATABASE_ID
NOTION_DELIVERY_LOGS_DATABASE_ID
GMAIL_USER
GMAIL_APP_PASSWORD
```

## Gmail App Password Guidance

V1 uses Gmail SMTP with an app password.

Requirements:

- Enable 2FA on the Gmail account.
- Use a dedicated app password.
- Do not use the normal Gmail account password.
- Rotate the app password if it is exposed.

## Before Making the Repo Public

Run a security review:

- Search for secrets.
- Search for real emails.
- Search for Notion IDs.
- Search for private content.
- Confirm `.env` is ignored.
- Confirm `.env.example` contains placeholders only.
- Confirm logs mask recipient emails.
- Confirm tests use fake data only.

## Incident Response

If a secret is exposed:

1. Revoke or rotate it immediately.
2. Remove it from the repository.
3. Review GitHub Actions logs.
4. Assume the secret is compromised even if the repository is private.

If recipient data is exposed:

1. Remove the data.
2. Replace it with synthetic examples.
3. Notify affected people if appropriate.
