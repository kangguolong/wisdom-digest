"""Notion gateway and response parsers."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from notion_client import Client

from wisdom_digest.config import Settings
from wisdom_digest.models import DeliveryLog, Recipient, WisdomItem

DEFAULT_MIN_REPEAT_DAYS = 90


class SchemaMismatchError(ValueError):
    """Raised when a Notion page does not match the expected V1 schema."""


class NotionGateway:
    """Thin gateway for Notion database operations."""

    def __init__(self, settings: Settings, client: Any | None = None) -> None:
        self.settings = settings
        self.client = client or Client(auth=settings.notion_api_key or "")

    def fetch_wisdom_items(self) -> list[WisdomItem]:
        pages = self._query_all_pages(self._required_database_id("wisdom"))
        return [parse_wisdom_item_page(page) for page in pages]

    def fetch_recipients(self) -> list[Recipient]:
        pages = self._query_all_pages(self._required_database_id("recipients"))
        return [parse_recipient_page(page) for page in pages]

    def fetch_recent_delivery_logs(
        self,
        since: datetime | None = None,
    ) -> list[DeliveryLog]:
        filter_payload = None
        if since is not None:
            filter_payload = {
                "property": "Sent At",
                "date": {"on_or_after": since.isoformat()},
            }

        pages = self._query_all_pages(
            self._required_database_id("delivery_logs"),
            filter_payload=filter_payload,
        )
        return [parse_delivery_log_page(page) for page in pages]

    def write_delivery_log(self, delivery_log: DeliveryLog) -> None:
        self.client.pages.create(
            parent={"data_source_id": self._required_database_id("delivery_logs")},
            properties=build_delivery_log_properties(delivery_log),
        )

    def _query_all_pages(
        self,
        data_source_id: str,
        filter_payload: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        pages: list[dict[str, Any]] = []
        cursor: str | None = None

        while True:
            query_kwargs: dict[str, Any] = {"data_source_id": data_source_id}
            if cursor:
                query_kwargs["start_cursor"] = cursor
            if filter_payload is not None:
                query_kwargs["filter"] = filter_payload

            response = self.client.data_sources.query(**query_kwargs)
            pages.extend(response.get("results", []))
            if not response.get("has_more"):
                return pages
            cursor = response.get("next_cursor")

    def _required_database_id(self, database_name: str) -> str:
        values = {
            "wisdom": self.settings.notion_wisdom_database_id,
            "recipients": self.settings.notion_recipients_database_id,
            "delivery_logs": self.settings.notion_delivery_logs_database_id,
        }
        database_id = values[database_name]
        if not database_id:
            raise RuntimeError(f"Missing Notion database ID for {database_name}.")
        return database_id


def parse_wisdom_item_page(page: dict[str, Any]) -> WisdomItem:
    properties = _properties(page)
    return WisdomItem(
        id=_page_id(page),
        title=_title(properties, "Title", required=True) or "",
        text=_rich_text(properties, "Text", required=True) or "",
        status=_select(properties, "Status", required=True) or "",
        importance=_number(properties, "Importance", required=True),
        author=_rich_text(properties, "Author"),
        source=_rich_text(properties, "Source"),
        category=_select(properties, "Category"),
        tags=_multi_select(properties, "Tags"),
        audience=_multi_select(properties, "Audience"),
        min_repeat_days=_optional_int(properties, "Min Repeat Days")
        or DEFAULT_MIN_REPEAT_DAYS,
        reflection_prompt=_rich_text(properties, "Reflection Prompt"),
    )


def parse_recipient_page(page: dict[str, Any]) -> Recipient:
    properties = _properties(page)
    return Recipient(
        id=_page_id(page),
        name=_title(properties, "Name", required=True) or "",
        email=_email(properties, "Email", required=True) or "",
        status=_select(properties, "Status", required=True) or "",
        frequency=_multi_select(properties, "Frequency", required=True),
        preference_tags=_multi_select(properties, "Preference Tags"),
        excluded_tags=_multi_select(properties, "Excluded Tags"),
        timezone=_rich_text(properties, "Timezone"),
    )


def parse_delivery_log_page(page: dict[str, Any]) -> DeliveryLog:
    properties = _properties(page)
    return DeliveryLog(
        recipient_id=_single_relation_id(properties, "Recipient", required=True) or "",
        wisdom_item_id=_single_relation_id(
            properties,
            "Wisdom Item",
            required=True,
        )
        or "",
        sent_at=_date_start(properties, "Sent At", required=True),
        slot=_select(properties, "Slot", required=True) or "",
        status=_select(properties, "Status", required=True) or "",
    )


def build_delivery_log_properties(delivery_log: DeliveryLog) -> dict[str, Any]:
    sent_at = delivery_log.sent_at.isoformat()
    title = (
        f"{delivery_log.sent_at.date().isoformat()} "
        f"{delivery_log.slot} "
        f"{delivery_log.recipient_id[:8]}"
    )
    return {
        "Title": {"title": [{"text": {"content": title}}]},
        "Recipient": {"relation": [{"id": delivery_log.recipient_id}]},
        "Wisdom Item": {"relation": [{"id": delivery_log.wisdom_item_id}]},
        "Sent At": {"date": {"start": sent_at}},
        "Slot": {"select": {"name": delivery_log.slot}},
        "Status": {"select": {"name": delivery_log.status}},
    }


def _page_id(page: dict[str, Any]) -> str:
    page_id = page.get("id")
    if not isinstance(page_id, str) or not page_id:
        raise SchemaMismatchError("Notion page is missing required page id.")
    return page_id


def _properties(page: dict[str, Any]) -> dict[str, Any]:
    properties = page.get("properties")
    if not isinstance(properties, dict):
        raise SchemaMismatchError("Notion page is missing properties.")
    return properties


def _property(
    properties: dict[str, Any],
    name: str,
    expected_type: str,
    required: bool = False,
) -> dict[str, Any] | None:
    prop = properties.get(name)
    if prop is None:
        if required:
            raise SchemaMismatchError(f"Missing required Notion property: {name}.")
        return None

    if not isinstance(prop, dict) or prop.get("type") != expected_type:
        raise SchemaMismatchError(
            f"Notion property {name} must be type {expected_type}.",
        )
    return prop


def _title(
    properties: dict[str, Any],
    name: str,
    required: bool = False,
) -> str | None:
    prop = _property(properties, name, "title", required)
    if prop is None:
        return None
    return _join_plain_text(prop.get("title"), name, required)


def _rich_text(
    properties: dict[str, Any],
    name: str,
    required: bool = False,
) -> str | None:
    prop = _property(properties, name, "rich_text", required)
    if prop is None:
        return None
    return _join_plain_text(prop.get("rich_text"), name, required)


def _join_plain_text(
    values: Any,
    property_name: str,
    required: bool = False,
) -> str | None:
    if not isinstance(values, list):
        raise SchemaMismatchError(f"Notion property {property_name} must be text.")

    text = "".join(_plain_text(value, property_name) for value in values)
    if required and not text:
        raise SchemaMismatchError(f"Notion property {property_name} is required.")
    return text or None


def _plain_text(value: Any, property_name: str) -> str:
    if not isinstance(value, dict) or not isinstance(value.get("plain_text"), str):
        raise SchemaMismatchError(f"Notion property {property_name} must be text.")
    return value["plain_text"]


def _select(
    properties: dict[str, Any],
    name: str,
    required: bool = False,
) -> str | None:
    prop = _property(properties, name, "select", required)
    if prop is None:
        return None

    select_value = prop.get("select")
    if select_value is None and not required:
        return None
    if not isinstance(select_value, dict) or not isinstance(
        select_value.get("name"),
        str,
    ):
        raise SchemaMismatchError(f"Notion property {name} must be a select value.")
    return select_value["name"]


def _multi_select(
    properties: dict[str, Any],
    name: str,
    required: bool = False,
) -> set[str]:
    prop = _property(properties, name, "multi_select", required)
    if prop is None:
        return set()

    values = prop.get("multi_select")
    if not isinstance(values, list):
        raise SchemaMismatchError(f"Notion property {name} must be multi-select.")
    return set(_multi_select_name(value, name) for value in values)


def _multi_select_name(value: Any, property_name: str) -> str:
    if not isinstance(value, dict) or not isinstance(value.get("name"), str):
        raise SchemaMismatchError(
            f"Notion property {property_name} must be multi-select.",
        )
    return value["name"]


def _number(
    properties: dict[str, Any],
    name: str,
    required: bool = False,
) -> int:
    prop = _property(properties, name, "number", required)
    if prop is None:
        raise SchemaMismatchError(f"Missing required Notion property: {name}.")
    number = prop.get("number")
    if not isinstance(number, int):
        raise SchemaMismatchError(f"Notion property {name} must be an integer.")
    return number


def _optional_int(properties: dict[str, Any], name: str) -> int | None:
    prop = _property(properties, name, "number")
    if prop is None or prop.get("number") is None:
        return None
    number = prop.get("number")
    if not isinstance(number, int):
        raise SchemaMismatchError(f"Notion property {name} must be an integer.")
    return number


def _email(
    properties: dict[str, Any],
    name: str,
    required: bool = False,
) -> str | None:
    prop = _property(properties, name, "email", required)
    if prop is None:
        return None
    email = prop.get("email")
    if email is None and not required:
        return None
    if not isinstance(email, str) or not email:
        raise SchemaMismatchError(f"Notion property {name} must be an email.")
    return email


def _single_relation_id(
    properties: dict[str, Any],
    name: str,
    required: bool = False,
) -> str | None:
    prop = _property(properties, name, "relation", required)
    if prop is None:
        return None
    relation = prop.get("relation")
    if not isinstance(relation, list):
        raise SchemaMismatchError(f"Notion property {name} must be a relation.")
    if not relation and not required:
        return None
    if len(relation) != 1:
        raise SchemaMismatchError(
            f"Notion property {name} must have exactly one relation.",
        )

    relation_id = relation[0].get("id") if isinstance(relation[0], dict) else None
    if not isinstance(relation_id, str) or not relation_id:
        raise SchemaMismatchError(f"Notion property {name} relation is invalid.")
    return relation_id


def _date_start(
    properties: dict[str, Any],
    name: str,
    required: bool = False,
) -> datetime:
    prop = _property(properties, name, "date", required)
    if prop is None:
        raise SchemaMismatchError(f"Missing required Notion property: {name}.")
    date_value = prop.get("date")
    if not isinstance(date_value, dict) or not isinstance(date_value.get("start"), str):
        raise SchemaMismatchError(f"Notion property {name} must be a date.")
    try:
        return datetime.fromisoformat(date_value["start"])
    except ValueError as exc:
        raise SchemaMismatchError(f"Notion property {name} date is invalid.") from exc
