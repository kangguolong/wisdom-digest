import logging
from datetime import UTC, datetime

import pytest

from wisdom_digest.config import Settings
from wisdom_digest.email_sender import RenderedEmail, SendResult
from wisdom_digest.models import DeliveryLog, DeliveryStatus, Recipient, WisdomItem
from wisdom_digest.workflow import resolve_slot, run_digest

NOW = datetime(2026, 6, 12, 21, 0, tzinfo=UTC)


def settings(
    *,
    digest_slot: str | None = "morning",
    dry_run: bool = True,
    write_dry_run_logs: bool = False,
    notion_api_key: str | None = "fake-notion-key",
    gmail_user: str | None = "sender@example.com",
    gmail_app_password: str | None = "fake-app-password",
) -> Settings:
    return Settings(
        notion_api_key=notion_api_key,
        notion_wisdom_database_id="wisdom-db",
        notion_recipients_database_id="recipients-db",
        notion_delivery_logs_database_id="logs-db",
        gmail_user=gmail_user,
        gmail_app_password=gmail_app_password,
        dry_run=dry_run,
        write_dry_run_logs=write_dry_run_logs,
        digest_slot=digest_slot,
    )


def recipient(email: str = "person@example.com") -> Recipient:
    return Recipient(
        id="recipient-1",
        name="Synthetic Recipient",
        email=email,
        status="active",
        frequency={"morning"},
    )


def wisdom_item() -> WisdomItem:
    return WisdomItem(
        id="item-1",
        title="Synthetic Item",
        text="Synthetic wisdom text.",
        status="active",
        importance=4,
    )


class FakeGateway:
    def __init__(
        self,
        recipients: list[Recipient] | None = None,
        wisdom_items: list[WisdomItem] | None = None,
        delivery_logs: list[DeliveryLog] | None = None,
    ) -> None:
        self.recipients = recipients if recipients is not None else [recipient()]
        self.wisdom_items = (
            wisdom_items if wisdom_items is not None else [wisdom_item()]
        )
        self.delivery_logs = delivery_logs if delivery_logs is not None else []
        self.fetch_calls: list[str] = []
        self.written_logs: list[DeliveryLog] = []

    def fetch_wisdom_items(self) -> list[WisdomItem]:
        self.fetch_calls.append("wisdom_items")
        return self.wisdom_items

    def fetch_recipients(self) -> list[Recipient]:
        self.fetch_calls.append("recipients")
        return self.recipients

    def fetch_recent_delivery_logs(
        self,
        since: datetime | None = None,
    ) -> list[DeliveryLog]:
        self.fetch_calls.append("delivery_logs")
        return self.delivery_logs

    def write_delivery_log(self, delivery_log: DeliveryLog) -> None:
        self.written_logs.append(delivery_log)


class FakeEmailProvider:
    def __init__(self, status: str = DeliveryStatus.DRY_RUN.value) -> None:
        self.status = status
        self.rendered: list[tuple[Recipient, WisdomItem, str, str]] = []
        self.sent: list[tuple[Recipient, RenderedEmail]] = []

    def render_digest(
        self,
        recipient: Recipient,
        wisdom_item: WisdomItem,
        slot_label: str,
        send_date: str,
    ) -> RenderedEmail:
        self.rendered.append((recipient, wisdom_item, slot_label, send_date))
        return RenderedEmail(
            subject="Synthetic subject",
            html_body="<p>Synthetic</p>",
            text_body="Synthetic",
        )

    def send(self, recipient: Recipient, email: RenderedEmail) -> SendResult:
        self.sent.append((recipient, email))
        return SendResult(status=self.status)


def test_resolve_slot_prefers_explicit_digest_slot():
    resolved = resolve_slot(
        settings(digest_slot="evening"),
        now=datetime(2026, 6, 12, 21, 0, tzinfo=UTC),
    )

    assert resolved.value == "evening"


def test_resolve_slot_invalid_explicit_slot_fails_clearly():
    with pytest.raises(ValueError, match="not-a-slot"):
        resolve_slot(settings(digest_slot="not-a-slot"), now=NOW)


def test_no_matching_slot_exits_without_external_calls():
    gateway = FakeGateway()
    email_provider = FakeEmailProvider()

    result = run_digest(
        settings(digest_slot=None, notion_api_key=None, gmail_user=None),
        now=datetime(2026, 6, 12, 22, 0, tzinfo=UTC),
        notion_gateway=gateway,
        email_provider=email_provider,
    )

    assert result.slot is None
    assert result.skipped_reason == "no_matching_slot"
    assert gateway.fetch_calls == []
    assert email_provider.rendered == []
    assert email_provider.sent == []


def test_dry_run_processes_selection_without_writing_logs_by_default():
    gateway = FakeGateway()
    email_provider = FakeEmailProvider(status=DeliveryStatus.DRY_RUN.value)

    result = run_digest(
        settings(write_dry_run_logs=False),
        now=NOW,
        notion_gateway=gateway,
        email_provider=email_provider,
    )

    assert result.slot == "morning"
    assert result.selections_count == 1
    assert result.dry_run_count == 1
    assert result.delivery_logs_written == 0
    assert gateway.written_logs == []
    assert len(email_provider.rendered) == 1
    assert len(email_provider.sent) == 1
    assert email_provider.rendered[0][2:] == ("Morning", "2026-06-13")


def test_dry_run_writes_log_only_when_enabled():
    gateway = FakeGateway()

    result = run_digest(
        settings(write_dry_run_logs=True),
        now=NOW,
        notion_gateway=gateway,
        email_provider=FakeEmailProvider(status=DeliveryStatus.DRY_RUN.value),
    )

    assert result.delivery_logs_written == 1
    assert gateway.written_logs[0].status == DeliveryStatus.DRY_RUN.value
    assert gateway.written_logs[0].slot == "morning"


def test_sent_and_failed_results_write_delivery_logs():
    sent_gateway = FakeGateway()
    sent_result = run_digest(
        settings(dry_run=False),
        now=NOW,
        notion_gateway=sent_gateway,
        email_provider=FakeEmailProvider(status=DeliveryStatus.SENT.value),
    )

    failed_gateway = FakeGateway()
    failed_result = run_digest(
        settings(dry_run=False),
        now=NOW,
        notion_gateway=failed_gateway,
        email_provider=FakeEmailProvider(status=DeliveryStatus.FAILED.value),
    )

    assert sent_result.sent_count == 1
    assert sent_gateway.written_logs[0].status == DeliveryStatus.SENT.value
    assert failed_result.failed_count == 1
    assert failed_gateway.written_logs[0].status == DeliveryStatus.FAILED.value


def test_empty_selection_exits_cleanly():
    gateway = FakeGateway(recipients=[recipient()], wisdom_items=[])

    result = run_digest(
        settings(),
        now=NOW,
        notion_gateway=gateway,
        email_provider=FakeEmailProvider(),
    )

    assert result.selections_count == 0
    assert result.delivery_logs_written == 0


def test_missing_notion_settings_fail_when_slot_matches():
    with pytest.raises(RuntimeError, match="NOTION_API_KEY"):
        run_digest(settings(notion_api_key=None), now=NOW)


def test_missing_gmail_settings_fail_only_for_real_send():
    run_digest(
        settings(gmail_user=None, gmail_app_password=None, dry_run=True),
        now=NOW,
        notion_gateway=FakeGateway(),
        email_provider=FakeEmailProvider(),
    )

    with pytest.raises(RuntimeError, match="GMAIL_USER"):
        run_digest(
            settings(gmail_user=None, gmail_app_password=None, dry_run=False),
            now=NOW,
            notion_gateway=FakeGateway(),
            email_provider=FakeEmailProvider(status=DeliveryStatus.SENT.value),
        )


def test_logs_mask_recipient_email(caplog):
    gateway = FakeGateway(recipients=[recipient(email="person@example.com")])

    with caplog.at_level(logging.INFO):
        run_digest(
            settings(),
            now=NOW,
            notion_gateway=gateway,
            email_provider=FakeEmailProvider(),
        )

    assert "p***n@example.com" in caplog.text
    assert "person@example.com" not in caplog.text
