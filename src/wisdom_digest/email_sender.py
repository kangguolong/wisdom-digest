"""Email rendering and sending interface."""

from __future__ import annotations

from dataclasses import dataclass

from wisdom_digest.models import Recipient, WisdomItem


@dataclass(frozen=True)
class RenderedEmail:
    subject: str
    html_body: str
    text_body: str


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
        raise NotImplementedError("Email rendering is implemented in Phase 4.")

    def send(self, recipient: Recipient, email: RenderedEmail) -> str | None:
        _ = (recipient, email)
        raise NotImplementedError("Email sending is implemented in Phase 4.")
