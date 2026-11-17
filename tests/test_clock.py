from timon.clock import session_info
from conftest import et


def test_opening_range_forming_blocks_entries(cal, limits):
    s = session_info(et("2026-11-19T09:45"), cal, limits)
    assert s.session == "REGULAR" and not s.can_enter and "opening range" in s.reason


def test_entries_allowed_mid_morning(cal, limits):
    s = session_info(et("2026-11-19T10:30"), cal, limits)
    assert s.can_enter and not s.must_flatten


def test_entry_cutoff(cal, limits):
    s = session_info(et("2026-11-19T13:30"), cal, limits)
    assert not s.can_enter and not s.must_flatten


def test_eod_flatten(cal, limits):
    s = session_info(et("2026-11-19T15:52"), cal, limits)
    assert s.must_flatten and not s.can_enter


def test_premarket_no_entries(cal, limits):
    s = session_info(et("2026-11-19T08:00"), cal, limits)
    assert s.session == "PRE" and not s.can_enter


def test_thanksgiving_closed(cal, limits):
    s = session_info(et("2026-11-26T11:00"), cal, limits)
    assert not s.trading_day and s.session == "CLOSED"


def test_half_day_cutoff_and_flatten(cal, limits):
    # half day closes 13:00 -> entry cutoff 12:00, flatten from 12:45 (final flatten)
    assert session_info(et("2026-11-27T11:00"), cal, limits).can_enter
    assert not session_info(et("2026-11-27T12:10"), cal, limits).can_enter
    s = session_info(et("2026-11-27T12:46"), cal, limits)
    assert s.must_flatten and s.final_flatten_passed


def test_sgt_shown(cal, limits):
    s = session_info(et("2026-11-19T09:30"), cal, limits)
    assert s.sgt == "2026-11-19 22:30 SGT"
