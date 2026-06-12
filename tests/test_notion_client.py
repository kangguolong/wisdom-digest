from datetime import UTC, datetime

import pytest

from wisdom_digest.config import Settings
from wisdom_digest.models import DeliveryLog
from wisdom_digest.notion_client import (
    NotionGateway,
    SchemaMismatchError,
    build_delivery_log_properties,
    parse_delivery_log_page,
    parse_recipient_page,
    parse_wisdom_item_page,
)


def settings() -> Settings:
    return Settings(
        notion_api_key="fake-notion-key",
        notion_wisdom_database_id="wisdom-db",
        notion_recipients_database_id="recipients-db",
        notion_delivery_logs_database_id="logs-db",
        gmail_user="sender@example.com",
        gmail_app_password="fake-app-password",
    )


def title(value: str) -> dict:
    return {"type": "title", "title": [{"plain_text": value}]}


def rich_text(value: str) -> dict:
    return {"type": "rich_text", "rich_text": [{"plain_text": value}]}


def select(value: str | None) -> dict:
    return {"type": "select", "select": {"name": value} if value else None}


def multi_select(*values: str) -> dict:
    return {
        "type": "multi_select",
        "multi_select": [{"name": value} for value in values],
    }


def number(value: int | None) -> dict:
    return {"type": "number", "number": value}


def email(value: str | None) -> dict:
    return {"type": "email", "email": value}


def relation(*ids: str) -> dict:
    return {"type": "relation", "relation": [{"id": value} for value in ids]}


def date(value: str | None) -> dict:
    return {"type": "date", "date": {"start": value} if value else None}


def wisdom_page(**overrides) -> dict:
    properties = {
        "Title": title("Long-term thinking"),
        "Text": rich_text("Small actions compound."),
        "Status": select("active"),
        "Importance": number(4),
        "Author": rich_text("Synthetic Author"),
        "Source": rich_text("Synthetic Source"),
        "Category": select("decision_making"),
        "Tags": multi_select("discipline", "compounding"),
        "Audience": multi_select("general"),
        "Min Repeat Days": number(45),
        "Reflection Prompt": rich_text("What should I notice today?"),
    }
    properties.update(overrides)
    return {"id": "wisdom-page-1", "properties": properties}


def recipient_page(**overrides) -> dict:
    properties = {
        "Name": title("Synthetic Recipient"),
        "Email": email("recipient@example.com"),
        "Status": select("active"),
        "Frequency": multi_select("morning", "evening"),
        "Preference Tags": multi_select("discipline"),
        "Excluded Tags": multi_select("investing"),
        "Timezone": rich_text("Pacific/Auckland"),
    }
    properties.update(overrides)
    return {"id": "recipient-page-1", "properties": properties}


def delivery_log_page(**overrides) -> dict:
    properties = {
        "Title": title("2026-06-12 morning synthetic"),
        "Recipient": relation("recipient-page-1"),
        "Wisdom Item": relation("wisdom-page-1"),
        "Sent At": date("2026-06-12T09:00:00+00:00"),
        "Slot": select("morning"),
        "Status": select("sent"),
    }
    properties.update(overrides)
    return {"id": "log-page-1", "properties": properties}


class FakeDataSources:
    def __init__(self, responses: list[dict]) -> None:
        self.responses = responses
        self.calls: list[dict] = []

    def query(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)


class FakePages:
    def __init__(self) -> None:
        self.created: list[dict] = []

    def create(self, **kwargs):
        self.created.append(kwargs)
        return {"id": "created-log-page"}


class FakeClient:
    def __init__(self, responses: list[dict] | None = None) -> None:
        self.data_sources = FakeDataSources(responses or [])
        self.pages = FakePages()


def test_parse_wisdom_item_page_maps_required_and_optional_properties():
    parsed = parse_wisdom_item_page(wisdom_page())

    assert parsed.id == "wisdom-page-1"
    assert parsed.title == "Long-term thinking"
    assert parsed.text == "Small actions compound."
    assert parsed.status == "active"
    assert parsed.importance == 4
    assert parsed.tags == {"discipline", "compounding"}
    assert parsed.audience == {"general"}
    assert parsed.min_repeat_days == 45
    assert parsed.reflection_prompt == "What should I notice today?"


def test_parse_wisdom_item_page_defaults_missing_optional_properties():
    parsed = parse_wisdom_item_page(
        wisdom_page(
            Author=None,
            Source=None,
            Category=None,
            Tags=None,
            Audience=None,
            **{"Min Repeat Days": None, "Reflection Prompt": None},
        )
    )

    assert parsed.author is None
    assert parsed.source is None
    assert parsed.category is None
    assert parsed.tags == set()
    assert parsed.audience == set()
    assert parsed.min_repeat_days == 90
    assert parsed.reflection_prompt is None


def test_parse_recipient_page_maps_properties():
    parsed = parse_recipient_page(recipient_page())

    assert parsed.id == "recipient-page-1"
    assert parsed.name == "Synthetic Recipient"
    assert parsed.email == "recipient@example.com"
    assert parsed.status == "active"
    assert parsed.frequency == {"morning", "evening"}
    assert parsed.preference_tags == {"discipline"}
    assert parsed.excluded_tags == {"investing"}
    assert parsed.timezone == "Pacific/Auckland"


def test_parse_recipient_page_defaults_missing_optional_properties():
    parsed = parse_recipient_page(
        recipient_page(
            **{
                "Preference Tags": None,
                "Excluded Tags": None,
                "Timezone": None,
            }
        )
    )

    assert parsed.preference_tags == set()
    assert parsed.excluded_tags == set()
    assert parsed.timezone is None


def test_parse_delivery_log_page_maps_required_properties():
    parsed = parse_delivery_log_page(delivery_log_page())

    assert parsed.recipient_id == "recipient-page-1"
    assert parsed.wisdom_item_id == "wisdom-page-1"
    assert parsed.sent_at == datetime(2026, 6, 12, 9, 0, tzinfo=UTC)
    assert parsed.slot == "morning"
    assert parsed.status == "sent"


def test_missing_required_property_raises_schema_mismatch():
    page = wisdom_page()
    del page["properties"]["Text"]

    with pytest.raises(SchemaMismatchError, match="Text"):
        parse_wisdom_item_page(page)


def test_wrong_required_property_type_raises_schema_mismatch():
    with pytest.raises(SchemaMismatchError, match="Importance"):
        parse_wisdom_item_page(wisdom_page(Importance=rich_text("high")))


def test_empty_required_relation_raises_schema_mismatch():
    with pytest.raises(SchemaMismatchError, match="Recipient"):
        parse_delivery_log_page(delivery_log_page(Recipient=relation()))


def test_gateway_fetches_all_paginated_wisdom_items():
    client = FakeClient(
        [
            {
                "results": [wisdom_page()],
                "has_more": True,
                "next_cursor": "cursor-2",
            },
            {
                "results": [wisdom_page(Title=title("Second item"))],
                "has_more": False,
                "next_cursor": None,
            },
        ]
    )
    gateway = NotionGateway(settings(), client=client)

    results = gateway.fetch_wisdom_items()

    assert [result.title for result in results] == [
        "Long-term thinking",
        "Second item",
    ]
    assert client.data_sources.calls == [
        {"data_source_id": "wisdom-db"},
        {"data_source_id": "wisdom-db", "start_cursor": "cursor-2"},
    ]


def test_gateway_fetch_recent_delivery_logs_passes_since_filter():
    since = datetime(2026, 6, 1, tzinfo=UTC)
    client = FakeClient(
        [{"results": [delivery_log_page()], "has_more": False, "next_cursor": None}]
    )
    gateway = NotionGateway(settings(), client=client)

    results = gateway.fetch_recent_delivery_logs(since=since)

    assert len(results) == 1
    assert client.data_sources.calls == [
        {
            "data_source_id": "logs-db",
            "filter": {
                "property": "Sent At",
                "date": {"on_or_after": "2026-06-01T00:00:00+00:00"},
            },
        }
    ]


def test_write_delivery_log_builds_safe_payload():
    client = FakeClient()
    gateway = NotionGateway(settings(), client=client)

    gateway.write_delivery_log(
        DeliveryLog(
            recipient_id="recipient-page-1",
            wisdom_item_id="wisdom-page-1",
            sent_at=datetime(2026, 6, 12, 9, 0, tzinfo=UTC),
            slot="morning",
            status="sent",
        )
    )

    assert client.pages.created == [
        {
            "parent": {"data_source_id": "logs-db"},
            "properties": {
                "Title": {
                    "title": [
                        {
                            "text": {
                                "content": "2026-06-12 morning recipien",
                            }
                        }
                    ]
                },
                "Recipient": {"relation": [{"id": "recipient-page-1"}]},
                "Wisdom Item": {"relation": [{"id": "wisdom-page-1"}]},
                "Sent At": {"date": {"start": "2026-06-12T09:00:00+00:00"}},
                "Slot": {"select": {"name": "morning"}},
                "Status": {"select": {"name": "sent"}},
            },
        }
    ]


def test_build_delivery_log_properties_uses_synthetic_title_only():
    properties = build_delivery_log_properties(
        DeliveryLog(
            recipient_id="recipient-page-1",
            wisdom_item_id="wisdom-page-1",
            sent_at=datetime(2026, 6, 12, 9, 0, tzinfo=UTC),
            slot="morning",
            status="dry_run",
        )
    )

    title_content = properties["Title"]["title"][0]["text"]["content"]
    assert title_content == "2026-06-12 morning recipien"
    assert "@" not in title_content
