"""Market calendar and session logic for the competition window.

All decisions use America/New_York time. SGT is shown only for humans.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
SGT = ZoneInfo("Asia/Singapore")


def _t(s: str) -> time:
    h, m = s.split(":")
    return time(int(h), int(m))


def to_et(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return dt.astimezone(ET)


@dataclass(frozen=True)
class SessionInfo:
    et: str
    sgt: str
    trading_day: bool
    session: str               # PRE | REGULAR | AFTER | CLOSED
    regular_close_et: str | None
    can_enter: bool            # new entries allowed now
    must_flatten: bool         # past EOD flatten / final flatten / closing soon
    final_flatten_passed: bool
    reason: str

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def session_info(now: datetime, cal: dict, limits: dict) -> SessionInfo:
    et = to_et(now)
    day = et.date().isoformat()
    sgt = now.astimezone(SGT).strftime("%Y-%m-%d %H:%M SGT")
    et_s = et.strftime("%Y-%m-%d %H:%M ET")

    final = datetime.fromisoformat(cal["final_flatten_et"]).replace(tzinfo=ET)
    final_passed = et >= final

    if day not in cal.get("trading_days", []) or day in cal.get("closed_days", []):
        return SessionInfo(et_s, sgt, False, "CLOSED", None, False, final_passed, final_passed,
                           "not a competition trading day")

    sessions = cal["sessions"]
    reg_open = _t(sessions["regular"][0])
    reg_close = _t(cal.get("half_days", {}).get(day, sessions["regular"][1]))
    pre_open = _t(sessions["pre"][0])
    after_close = _t(sessions["after"][1])
    t = et.time()

    if pre_open <= t < reg_open:
        session = "PRE"
    elif reg_open <= t < reg_close:
        session = "REGULAR"
    elif reg_close <= t < after_close and day not in cal.get("half_days", {}):
        session = "AFTER"
    else:
        session = "CLOSED"

    strat = limits["strategy"]
    orders = limits["orders"]
    eod = min(_t(strat["eod_flatten_et"]), _minus_minutes(reg_close, 10))
    cutoff = min(_t(orders["entry_cutoff_et"]), _minus_minutes(reg_close, 60))
    or_end = _plus_minutes(reg_open, int(strat["opening_range_minutes"]))

    must_flatten = final_passed or (session == "REGULAR" and t >= eod) or session in ("AFTER",)
    can_enter = (session == "REGULAR" and or_end <= t < cutoff and not must_flatten)

    if final_passed:
        reason = "final flatten time passed — competition trading over"
    elif must_flatten:
        reason = f"end-of-day flatten window (from {eod.strftime('%H:%M')} ET)"
    elif session != "REGULAR":
        reason = f"{session} session — Timón trades regular hours only"
    elif t < or_end:
        reason = f"opening range still forming until {or_end.strftime('%H:%M')} ET"
    elif t >= cutoff:
        reason = f"past entry cutoff {cutoff.strftime('%H:%M')} ET — manage only"
    else:
        reason = "entries allowed"

    return SessionInfo(et_s, sgt, True, session, reg_close.strftime("%H:%M"), can_enter,
                       must_flatten, final_passed, reason)


def _minus_minutes(t: time, m: int) -> time:
    total = t.hour * 60 + t.minute - m
    return time(total // 60, total % 60)


def _plus_minutes(t: time, m: int) -> time:
    total = t.hour * 60 + t.minute + m
    return time(total // 60, total % 60)
