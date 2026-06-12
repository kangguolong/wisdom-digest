import logging

import pytest

from wisdom_digest.email_sender import (
    DEFAULT_REFLECTION_PROMPT,
    GmailSmtpEmailProvider,
)
from wisdom_digest.models import DeliveryStatus, Recipient, WisdomItem


def recipient(email: str = "person@example.com") -> Recipient:
    return Recipient(
        id="recipient-1",
        name="Test Recipient",
        email=email,
        status="active",
        frequency={"morning"},
    )


def wisdom_item(**overrides: object) -> WisdomItem:
    values = {
        "id": "item-1",
        "title": "Synthetic Item",
        "text": "Notice the useful constraint.",
        "status": "active",
        "importance": 4,
        "tags": {"discipline", "judgment"},
        "audience": {"personal"},
        "category": "Practice",
        "author": "Synthetic Author",
        "source": "Synthetic Source",
        "reflection_prompt": "What can I improve today?",
    }
    values.update(overrides)
    return WisdomItem(**values)


def provider(dry_run: bool = True) -> GmailSmtpEmailProvider:
    return GmailSmtpEmailProvider(
        gmail_user="sender@example.com",
        gmail_app_password="app-password",
        dry_run=dry_run,
    )


def test_render_digest_includes_html_and_text_content():
    rendered = provider().render_digest(
        recipient=recipient(),
        wisdom_item=wisdom_item(),
        slot_label="Morning",
        send_date="2026-06-12",
    )

    assert rendered.subject == "Wisdom Digest · Morning · 2026-06-12"
    assert "Notice the useful constraint." in rendered.html_body
    assert "Synthetic Author" in rendered.html_body
    assert "Synthetic Source" in rendered.html_body
    assert "Category: Practice" in rendered.html_body
    assert "Tags: discipline, judgment" in rendered.html_body
    assert "Reflection" in rendered.html_body
    assert "What can I improve today?" in rendered.text_body
    assert "Sent by Wisdom Digest" in rendered.text_body


def test_render_digest_handles_missing_optional_fields():
    rendered = provider().render_digest(
        recipient=recipient(),
        wisdom_item=wisdom_item(
            author=None,
            source=None,
            category=None,
            tags=set(),
            reflection_prompt=None,
        ),
        slot_label="Evening",
        send_date="2026-06-12",
    )

    assert DEFAULT_REFLECTION_PROMPT in rendered.html_body
    assert DEFAULT_REFLECTION_PROMPT in rendered.text_body
    assert "Category:" not in rendered.text_body
    assert "Tags:" not in rendered.text_body


def test_render_digest_escapes_user_provided_html():
    rendered = provider().render_digest(
        recipient=recipient(),
        wisdom_item=wisdom_item(text="<script>alert('x')</script>"),
        slot_label="Noon",
        send_date="2026-06-12",
    )

    assert "<script>" not in rendered.html_body
    assert "&lt;script&gt;" in rendered.html_body
    assert "<img" not in rendered.html_body
    assert "javascript:" not in rendered.html_body.lower()


def test_dry_run_send_does_not_open_smtp():
    class FailingSmtp:
        def __init__(self, *_args: object) -> None:
            raise AssertionError("SMTP should not be opened in dry-run mode")

    email_provider = GmailSmtpEmailProvider(
        gmail_user=None,
        gmail_app_password=None,
        dry_run=True,
        smtp_factory=FailingSmtp,
    )
    rendered = email_provider.render_digest(
        recipient=recipient(),
        wisdom_item=wisdom_item(),
        slot_label="Morning",
        send_date="2026-06-12",
    )

    result = email_provider.send(recipient(), rendered)

    assert result.status == DeliveryStatus.DRY_RUN.value
    assert result.message_id is None
    assert result.error is None


def test_real_send_builds_multipart_email_and_uses_smtp():
    sent_messages = []
    login_calls = []

    class FakeSmtp:
        def __init__(self, host: str, port: int) -> None:
            self.host = host
            self.port = port

        def __enter__(self) -> "FakeSmtp":
            return self

        def __exit__(
            self,
            exc_type: object,
            exc: object,
            traceback: object,
        ) -> None:
            return None

        def login(self, user: str, password: str) -> None:
            login_calls.append((user, password))

        def send_message(self, msg: object) -> None:
            sent_messages.append(msg)

    email_provider = GmailSmtpEmailProvider(
        gmail_user="sender@example.com",
        gmail_app_password="app-password",
        dry_run=False,
        smtp_factory=FakeSmtp,
    )
    rendered = email_provider.render_digest(
        recipient=recipient(),
        wisdom_item=wisdom_item(),
        slot_label="Morning",
        send_date="2026-06-12",
    )

    result = email_provider.send(recipient(), rendered)

    assert result.status == DeliveryStatus.SENT.value
    assert result.message_id is not None
    assert login_calls == [("sender@example.com", "app-password")]
    assert len(sent_messages) == 1
    message = sent_messages[0]
    assert message["From"] == "sender@example.com"
    assert message["To"] == "person@example.com"
    assert message["Subject"] == rendered.subject
    assert message.is_multipart()
    assert message.get_body(("plain",)).get_content().strip() == rendered.text_body
    assert rendered.html_body in message.get_body(("html",)).get_content()


def test_missing_gmail_credentials_fail_only_when_not_dry_run():
    email_provider = GmailSmtpEmailProvider(
        gmail_user=None,
        gmail_app_password=None,
        dry_run=False,
    )
    rendered = provider().render_digest(
        recipient=recipient(),
        wisdom_item=wisdom_item(),
        slot_label="Morning",
        send_date="2026-06-12",
    )

    with pytest.raises(RuntimeError, match="Missing Gmail SMTP credentials"):
        email_provider.send(recipient(), rendered)


def test_smtp_failure_returns_sanitized_error_and_masks_email(caplog):
    class FailingSmtp:
        def __init__(self, *_args: object) -> None:
            pass

        def __enter__(self) -> "FailingSmtp":
            return self

        def __exit__(
            self,
            exc_type: object,
            exc: object,
            traceback: object,
        ) -> None:
            return None

        def login(self, _user: str, _password: str) -> None:
            return None

        def send_message(self, _msg: object) -> None:
            raise RuntimeError("failed for person@example.com with app-password")

    email_provider = GmailSmtpEmailProvider(
        gmail_user="sender@example.com",
        gmail_app_password="app-password",
        dry_run=False,
        smtp_factory=FailingSmtp,
    )
    rendered = email_provider.render_digest(
        recipient=recipient(),
        wisdom_item=wisdom_item(),
        slot_label="Morning",
        send_date="2026-06-12",
    )

    with caplog.at_level(logging.WARNING):
        result = email_provider.send(recipient(), rendered)

    assert result.status == DeliveryStatus.FAILED.value
    assert result.error == "RuntimeError: SMTP delivery failed"
    assert "p***n@example.com" in caplog.text
    assert "person@example.com" not in result.error
    assert "person@example.com" not in caplog.text
    assert "app-password" not in result.error
    assert "app-password" not in caplog.text
