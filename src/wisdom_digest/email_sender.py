"""Email rendering and sending."""

from __future__ import annotations

import logging
import smtplib
from collections.abc import Callable
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import make_msgid
from typing import Protocol

from jinja2 import Environment, PackageLoader, select_autoescape

from wisdom_digest.config import Settings
from wisdom_digest.logging_utils import mask_email
from wisdom_digest.models import DeliveryStatus, Recipient, WisdomItem

DEFAULT_REFLECTION_PROMPT = (
    "What does this remind me to notice, improve, or act on today?"
)
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RenderedEmail:
    subject: str
    html_body: str
    text_body: str


@dataclass(frozen=True)
class SendResult:
    status: str
    message_id: str | None = None
    error: str | None = None


class SmtpClient(Protocol):
    def login(self, user: str, password: str) -> object: ...

    def send_message(self, msg: EmailMessage) -> object: ...

    def __enter__(self) -> SmtpClient: ...

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> object: ...


class EmailProvider:
    """Interface for future email delivery providers."""

    def render_digest(
        self,
        recipient: Recipient,
        wisdom_item: WisdomItem,
        slot_label: str,
        send_date: str,
    ) -> RenderedEmail:
        _ = (recipient, wisdom_item, slot_label, send_date)
        raise NotImplementedError

    def send(self, recipient: Recipient, email: RenderedEmail) -> SendResult:
        _ = (recipient, email)
        raise NotImplementedError


class GmailSmtpEmailProvider(EmailProvider):
    """Render digest emails and send them through Gmail SMTP."""

    def __init__(
        self,
        gmail_user: str | None,
        gmail_app_password: str | None,
        dry_run: bool = True,
        smtp_host: str = SMTP_HOST,
        smtp_port: int = SMTP_PORT,
        smtp_factory: Callable[[str, int], SmtpClient] = smtplib.SMTP_SSL,
    ) -> None:
        self.gmail_user = gmail_user
        self.gmail_app_password = gmail_app_password
        self.dry_run = dry_run
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_factory = smtp_factory
        self._template_env = Environment(
            loader=PackageLoader("wisdom_digest", "templates"),
            autoescape=select_autoescape(("html", "xml")),
        )

    @classmethod
    def from_settings(cls, settings: Settings) -> GmailSmtpEmailProvider:
        return cls(
            gmail_user=settings.gmail_user,
            gmail_app_password=settings.gmail_app_password,
            dry_run=settings.dry_run,
        )

    def render_digest(
        self,
        recipient: Recipient,
        wisdom_item: WisdomItem,
        slot_label: str,
        send_date: str,
    ) -> RenderedEmail:
        subject = f"Wisdom Digest · {slot_label} · {send_date}"
        reflection_prompt = wisdom_item.reflection_prompt or DEFAULT_REFLECTION_PROMPT
        tags = sorted(wisdom_item.tags)
        context = {
            "slot_label": slot_label,
            "send_date": send_date,
            "recipient_name": recipient.name,
            "wisdom_text": wisdom_item.text,
            "author": wisdom_item.author,
            "source": wisdom_item.source,
            "category": wisdom_item.category,
            "reflection_prompt": reflection_prompt,
            "tags": tags,
            "footer_text": "Sent by Wisdom Digest",
        }

        template = self._template_env.get_template("digest.html")
        return RenderedEmail(
            subject=subject,
            html_body=template.render(**context),
            text_body=_render_text_body(
                slot_label=slot_label,
                send_date=send_date,
                wisdom_item=wisdom_item,
                reflection_prompt=reflection_prompt,
            ),
        )

    def send(self, recipient: Recipient, email: RenderedEmail) -> SendResult:
        masked_recipient = mask_email(recipient.email)
        if self.dry_run:
            logger.info("Dry-run email send skipped for %s", masked_recipient)
            return SendResult(status=DeliveryStatus.DRY_RUN.value)

        self._validate_credentials()
        message = self._build_message(recipient, email)
        message_id = message["Message-ID"]

        try:
            with self.smtp_factory(self.smtp_host, self.smtp_port) as smtp:
                smtp.login(self.gmail_user or "", self.gmail_app_password or "")
                smtp.send_message(message)
        except Exception as exc:  # noqa: BLE001
            error = _sanitize_smtp_error(exc)
            logger.warning("Email send failed for %s: %s", masked_recipient, error)
            return SendResult(
                status=DeliveryStatus.FAILED.value,
                message_id=message_id,
                error=error,
            )

        logger.info("Email sent to %s", masked_recipient)
        return SendResult(status=DeliveryStatus.SENT.value, message_id=message_id)

    def _validate_credentials(self) -> None:
        if not self.gmail_user or not self.gmail_app_password:
            raise RuntimeError("Missing Gmail SMTP credentials.")

    def _build_message(
        self,
        recipient: Recipient,
        email: RenderedEmail,
    ) -> EmailMessage:
        message = EmailMessage()
        message["Subject"] = email.subject
        message["From"] = self.gmail_user or ""
        message["To"] = recipient.email
        message["Message-ID"] = make_msgid(domain="wisdom-digest.local")
        message.set_content(email.text_body)
        message.add_alternative(email.html_body, subtype="html")
        return message


def _render_text_body(
    slot_label: str,
    send_date: str,
    wisdom_item: WisdomItem,
    reflection_prompt: str,
) -> str:
    lines = [
        f"Wisdom Digest · {slot_label} · {send_date}",
        "",
        wisdom_item.text,
        "",
    ]

    attribution = _format_attribution(wisdom_item)
    if attribution:
        lines.extend([attribution, ""])

    if wisdom_item.category:
        lines.extend([f"Category: {wisdom_item.category}", ""])

    if wisdom_item.tags:
        lines.extend([f"Tags: {', '.join(sorted(wisdom_item.tags))}", ""])

    lines.extend(["Reflection:", reflection_prompt, "", "Sent by Wisdom Digest"])
    return "\n".join(lines)


def _format_attribution(wisdom_item: WisdomItem) -> str | None:
    if wisdom_item.author and wisdom_item.source:
        return f"- {wisdom_item.author}, {wisdom_item.source}"
    if wisdom_item.author:
        return f"- {wisdom_item.author}"
    if wisdom_item.source:
        return wisdom_item.source
    return None


def _sanitize_smtp_error(exc: Exception) -> str:
    return f"{type(exc).__name__}: SMTP delivery failed"
