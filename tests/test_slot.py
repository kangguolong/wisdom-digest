from datetime import UTC, datetime

from wisdom_digest.models import Slot
from wisdom_digest.slot import (
    CANDIDATE_UTC_CRONS,
    SLOT_TIMES,
    infer_current_slot,
    normalize_slot,
)


def test_slot_times_match_v1_schedule():
    assert SLOT_TIMES[Slot.MORNING].hour == 9
    assert SLOT_TIMES[Slot.NOON].hour == 13
    assert SLOT_TIMES[Slot.EVENING].hour == 18


def test_candidate_crons_cover_auckland_dst_offsets():
    assert CANDIDATE_UTC_CRONS[Slot.MORNING] == "0 20,21 * * *"
    assert CANDIDATE_UTC_CRONS[Slot.NOON] == "0 0,1 * * *"
    assert CANDIDATE_UTC_CRONS[Slot.EVENING] == "0 5,6 * * *"


def test_normalize_slot():
    assert normalize_slot(" Morning ") is Slot.MORNING


def test_infer_current_slot_handles_nzst_candidate_times():
    assert (
        infer_current_slot(
            now=datetime(2026, 6, 12, 21, 0, tzinfo=UTC),
        )
        is Slot.MORNING
    )
    assert (
        infer_current_slot(
            now=datetime(2026, 6, 13, 1, 0, tzinfo=UTC),
        )
        is Slot.NOON
    )
    assert (
        infer_current_slot(
            now=datetime(2026, 6, 13, 6, 0, tzinfo=UTC),
        )
        is Slot.EVENING
    )


def test_infer_current_slot_handles_nzdt_candidate_times():
    assert (
        infer_current_slot(
            now=datetime(2026, 12, 12, 20, 0, tzinfo=UTC),
        )
        is Slot.MORNING
    )
    assert (
        infer_current_slot(
            now=datetime(2026, 12, 13, 0, 0, tzinfo=UTC),
        )
        is Slot.NOON
    )
    assert (
        infer_current_slot(
            now=datetime(2026, 12, 13, 5, 0, tzinfo=UTC),
        )
        is Slot.EVENING
    )


def test_infer_current_slot_allows_delayed_run_inside_slot_hour():
    assert (
        infer_current_slot(
            now=datetime(2026, 6, 15, 21, 56, 21, tzinfo=UTC),
        )
        is Slot.MORNING
    )


def test_infer_current_slot_accepts_start_and_end_of_local_slot_hour():
    assert (
        infer_current_slot(now=datetime(2026, 6, 15, 21, 0, tzinfo=UTC))
        is Slot.MORNING
    )
    assert (
        infer_current_slot(now=datetime(2026, 6, 15, 21, 59, tzinfo=UTC))
        is Slot.MORNING
    )
    assert (
        infer_current_slot(now=datetime(2026, 6, 16, 1, 59, tzinfo=UTC))
        is Slot.NOON
    )
    assert (
        infer_current_slot(now=datetime(2026, 6, 16, 6, 59, tzinfo=UTC))
        is Slot.EVENING
    )


def test_infer_current_slot_rejects_first_minute_after_slot_hour():
    assert infer_current_slot(now=datetime(2026, 6, 15, 22, 0, tzinfo=UTC)) is None
    assert infer_current_slot(now=datetime(2026, 6, 16, 2, 0, tzinfo=UTC)) is None
    assert infer_current_slot(now=datetime(2026, 6, 16, 7, 0, tzinfo=UTC)) is None


def test_infer_current_slot_returns_none_for_non_slot_time():
    assert infer_current_slot(now=datetime(2026, 6, 13, 2, 0, tzinfo=UTC)) is None
