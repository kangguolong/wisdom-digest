# Codex Prompts

Use this document to drive Codex implementation in controlled phases.

General rule: Codex should treat `docs/v1-build-spec.md` as the source of truth.

## Prompt 1: Planning Only

```text
Read the repository documentation, especially docs/v1-build-spec.md.

Do not write code yet.

Produce an implementation plan for Wisdom Digest V1.

Constraints:
- Treat docs/v1-build-spec.md as the source of truth.
- Do not add features outside V1 scope.
- Do not add AI quote sourcing.
- Do not add AI ranking.
- Do not add a web UI.
- Do not hardcode secrets.
- Do not include real emails, real Notion IDs, or real API keys.
- Keep the implementation simple and maintainable.

The plan should include:
1. Proposed file structure
2. Python dependencies
3. Main modules
4. Implementation phases
5. Testing strategy
6. Security considerations
7. Open questions, if any
```

## Prompt 2: Repository Skeleton

```text
Implement Phase 1: repository skeleton.

Use docs/v1-build-spec.md as the source of truth.

Create:
- Python src package structure
- requirements.txt
- .env.example if missing
- .gitignore if missing
- README skeleton if missing
- SECURITY.md if missing
- GitHub Actions workflow skeleton
- basic test directory

Do not implement external AI sourcing.
Do not add real secrets, real emails, real Notion IDs, or real user data.
Do not implement a web UI.

Add minimal placeholder modules with clear interfaces:
- config.py
- models.py
- notion_client.py
- selector.py
- email_sender.py
- slot.py
- logging_utils.py
- main.py

Open a PR with a concise summary.
```

## Prompt 3: Selection Engine

```text
Implement Phase 2: V1 deterministic selection engine.

Use docs/selection-logic.md and docs/v1-build-spec.md as the source of truth.

Requirements:
- Filter active wisdom items only.
- Filter recipients by active status and subscribed slot.
- Respect excluded tags.
- Prefer matching preference tags.
- Avoid items sent recently to the same recipient.
- Prefer lower sent count for that recipient.
- Use importance as a positive weight.
- Return exactly one selected wisdom item per eligible recipient.
- Add unit tests for core selection cases.

Do not call Notion API in selector tests.
Use fixtures or plain Python objects.
Do not add AI ranking.
Do not add random opaque recommendation logic.
```

## Prompt 4: Notion Client

```text
Implement Phase 3: Notion client integration.

Use docs/notion-schema.md and docs/v1-build-spec.md as the source of truth.

Requirements:
- Read Wisdom Items database.
- Read Recipients database.
- Read recent Delivery Logs for each recipient.
- Write Delivery Logs after send attempts.
- Keep dry-run log writes optional and disabled by default with `WRITE_DRY_RUN_LOGS=false`.
- Parse Notion property types safely.
- Fail clearly on schema mismatch.
- Avoid logging sensitive data.
- Add tests for parsing logic using mocked Notion responses.

Security:
- Use environment variables only.
- Do not hardcode database IDs.
- Do not print API keys, emails, or full Notion responses.
```

## Prompt 5: Email Rendering and Gmail SMTP

```text
Implement Phase 4: HTML email rendering and Gmail SMTP sending.

Use docs/email-template-spec.md and docs/v1-build-spec.md as the source of truth.

Requirements:
- Use Jinja2 for HTML template rendering.
- Include plain-text fallback.
- Use Gmail SMTP with app password from environment variables.
- Support DRY_RUN mode.
- Do not send email when DRY_RUN=true.
- Do not write dry-run delivery logs unless WRITE_DRY_RUN_LOGS=true.
- Mask recipient emails in logs.
- Add tests for template rendering.
- Keep EmailProvider abstraction simple so provider can be replaced later.

Do not add SendGrid, Resend, Postmark, SES, or Gmail OAuth in V1.
```

## Prompt 6: Main Workflow and GitHub Actions

```text
Implement Phase 5: main workflow and GitHub Actions.

Use docs/v1-build-spec.md as the source of truth.

Requirements:
- Determine slot from environment variable or current `Pacific/Auckland` local time.
- Support morning/noon/evening.
- Query active recipients.
- Select one item per eligible recipient.
- Render email.
- Send email unless DRY_RUN=true.
- Write delivery log with sent or failed status. Dry-run logs are written only when WRITE_DRY_RUN_LOGS=true.
- Ensure GitHub Actions runs at DST-safe candidate UTC times:
  - `0 20,21 * * *` for 09:00 Pacific/Auckland
  - `0 0,1 * * *` for 13:00 Pacific/Auckland
  - `0 5,6 * * *` for 18:00 Pacific/Auckland
- Candidate cron runs that do not match the current Auckland local slot must exit cleanly without sending or logging.
- Add workflow_dispatch for manual testing.
- Use GitHub Secrets for all sensitive environment variables.
- Add tests for slot inference around NZST and NZDT.

Do not include real secrets.
Do not include real recipient data.
```

## Prompt 7: Security and Maintainability Review

```text
Perform a security and maintainability review of the repository.

Check:
- No secrets are committed.
- .env is ignored.
- .env.example contains no real values.
- No real emails or Notion IDs are present.
- Logs mask recipient emails.
- GitHub Actions uses secrets only.
- DRY_RUN defaults safely.
- WRITE_DRY_RUN_LOGS defaults safely.
- Tests use fake data only.
- README does not instruct users to commit secrets.
- Scope matches docs/v1-build-spec.md.

Do not add new features.
Open a PR only for necessary fixes.
```

## Review Prompt for ChatGPT or Human Reviewer

```text
Review this PR against docs/v1-build-spec.md.

Focus on:
- Scope discipline.
- Security.
- Simplicity.
- Test coverage.
- Notion schema compatibility.
- GitHub Actions correctness.
- Logs and sensitive data handling.

Flag anything that:
- Adds V2 features prematurely.
- Hardcodes secrets or identifiers.
- Uses real personal data.
- Makes the system unnecessarily complex.
- Breaks deterministic selection behavior.
```
