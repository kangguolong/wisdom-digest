"""Main Wisdom Digest workflow orchestration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from zoneinfo import ZoneInfo

from wisdom_digest.config import Settings
from wisdom_digest.email_sender import EmailProvider, GmailSmtpEmailProvider
from wisdom_digest.logging_utils import mask_email
from wisdom_digest.models import (
    DeliveryLog,
    DeliveryStatus,
    Recipient,
    SelectionResult,
    Slot,
    WisdomItem,
)
from wisdom_digest.notion_client import NotionGateway
from wisdom_digest.selector import select_items_for_recipients
from wisdom_digest.slot import infer_current_slot, normalize_slot

LOGGER = logging.getLogger(__name__)


class NotionGatewayProtocol(Protocol):
    def fetch_wisdom_items(self) -> list[WisdomItem]: ...

    def fetch_recipients(self) -> list[Recipient]: ...

    def fetch_recent_delivery_logs(
        self,
        since: datetime | None = None,
    ) -> list[DeliveryLog]: ...

    def write_delivery_log(self, delivery_log: DeliveryLog) -> None: ...


@dataclass(frozen=True)
class WorkflowResult:
    slot: str | None
    recipients_count: int = 0
    wisdom_items_count: int = 0
    selections_count: int = 0
    sent_count: int = 0
    failed_count: int = 0
    dry_run_count: int = 0
    delivery_logs_written: int = 0
    skipped_reason: str | None = None


def resolve_slot(settings: Settings, now: datetime | None = None) -> Slot | None:
    """Resolve the delivery slot from explicit config or local Auckland time."""
    if settings.digest_slot:
        return normalize_slot(settings.digest_slot)
    return infer_current_slot(settings.default_timezone, now=now)


def run_digest(
    settings: Settings,
    now: datetime | None = None,
    notion_gateway: NotionGatewayProtocol | None = None,
    email_provider: EmailProvider | None = None,
) -> WorkflowResult:
    """Run one digest workflow pass."""
    run_time = _as_aware_utc(now or datetime.now(UTC))
    slot = resolve_slot(settings, now=run_time)
    if slot is None:
        LOGGER.info("No matching digest slot; exiting without external calls")
        return WorkflowResult(slot=None, skipped_reason="no_matching_slot")

    _validate_notion_settings(settings)
    if not settings.dry_run:
        _validate_gmail_settings(settings)

    gateway = notion_gateway or NotionGateway(settings)
    provider = email_provider or GmailSmtpEmailProvider.from_settings(settings)

    wisdom_items = gateway.fetch_wisdom_items()
    recipients = gateway.fetch_recipients()
    delivery_logs = gateway.fetch_recent_delivery_logs()
    selections = select_items_for_recipients(
        recipients=recipients,
        wisdom_items=wisdom_items,
        delivery_logs=delivery_logs,
        current_slot=slot.value,
        now=run_time,
    )

    LOGGER.info(
        "Digest loaded slot=%s recipients=%s wisdom_items=%s selections=%s",
        slot.value,
        len(recipients),
        len(wisdom_items),
        len(selections),
    )

    recipients_by_id = {recipient.id: recipient for recipient in recipients}
    items_by_id = {item.id: item for item in wisdom_items}
    counters = _WorkflowCounters()

    for selection in selections:
        recipient = recipients_by_id.get(selection.recipient_id)
        wisdom_item = items_by_id.get(selection.wisdom_item_id)
        if recipient is None or wisdom_item is None:
            LOGGER.warning(
                "Skipping selection with missing model "
                "recipient_id=%s wisdom_item_id=%s",
                selection.recipient_id,
                selection.wisdom_item_id,
            )
            continue

        _process_selection(
            gateway=gateway,
            provider=provider,
            settings=settings,
            recipient=recipient,
            wisdom_item=wisdom_item,
            selection=selection,
            slot=slot,
            run_time=run_time,
            timezone_name=settings.default_timezone,
            counters=counters,
        )

    return WorkflowResult(
        slot=slot.value,
        recipients_count=len(recipients),
        wisdom_items_count=len(wisdom_items),
        selections_count=len(selections),
        sent_count=counters.sent_count,
        failed_count=counters.failed_count,
        dry_run_count=counters.dry_run_count,
        delivery_logs_written=counters.delivery_logs_written,
    )


@dataclass
class _WorkflowCounters:
    sent_count: int = 0
    failed_count: int = 0
    dry_run_count: int = 0
    delivery_logs_written: int = 0


def _process_selection(
    gateway: NotionGatewayProtocol,
    provider: EmailProvider,
    settings: Settings,
    recipient: Recipient,
    wisdom_item: WisdomItem,
    selection: SelectionResult,
    slot: Slot,
    run_time: datetime,
    timezone_name: str,
    counters: _WorkflowCounters,
) -> None:
    rendered = provider.render_digest(
        recipient=recipient,
        wisdom_item=wisdom_item,
        slot_label=slot.value.title(),
        send_date=run_time.astimezone(ZoneInfo(timezone_name)).date().isoformat(),
    )
    send_result = provider.send(recipient, rendered)
    status = send_result.status

    LOGGER.info(
        "Digest processed recipient=%s status=%s",
        mask_email(recipient.email),
        status,
    )

    if status == DeliveryStatus.SENT.value:
        counters.sent_count += 1
    elif status == DeliveryStatus.FAILED.value:
        counters.failed_count += 1
    elif status == DeliveryStatus.DRY_RUN.value:
        counters.dry_run_count += 1

    if status == DeliveryStatus.DRY_RUN.value and not settings.write_dry_run_logs:
        return

    if status in {
        DeliveryStatus.SENT.value,
        DeliveryStatus.FAILED.value,
        DeliveryStatus.DRY_RUN.value,
    }:
        gateway.write_delivery_log(
            DeliveryLog(
                recipient_id=selection.recipient_id,
                wisdom_item_id=selection.wisdom_item_id,
                sent_at=run_time,
                slot=slot.value,
                status=status,
            )
        )
        counters.delivery_logs_written += 1


def _validate_notion_settings(settings: Settings) -> None:
    missing = [
        name
        for name, value in {
            "NOTION_API_KEY": settings.notion_api_key,
            "NOTION_WISDOM_DATABASE_ID": settings.notion_wisdom_database_id,
            "NOTION_RECIPIENTS_DATABASE_ID": settings.notion_recipients_database_id,
            "NOTION_DELIVERY_LOGS_DATABASE_ID": (
                settings.notion_delivery_logs_database_id
            ),
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Missing required Notion environment variables: " + ", ".join(missing)
        )


def _validate_gmail_settings(settings: Settings) -> None:
    missing = [
        name
        for name, value in {
            "GMAIL_USER": settings.gmail_user,
            "GMAIL_APP_PASSWORD": settings.gmail_app_password,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Missing required Gmail environment variables: " + ", ".join(missing)
        )


def _as_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
