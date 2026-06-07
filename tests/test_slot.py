from wisdom_digest.models import Slot
from wisdom_digest.slot import CANDIDATE_UTC_CRONS, SLOT_TIMES, normalize_slot


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
