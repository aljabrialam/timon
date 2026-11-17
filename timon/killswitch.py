"""Kill switch and position management.

Runs at the start of every cycle, before any new entry is considered.
Actions, from mildest to strongest:
  NONE                 nothing to do
  HALT_NEW             no new orders today; manage existing positions
  FLATTEN_ALL          close all positions now (EOD, final day, missed check)
  FLATTEN_AND_DISABLE  close all and disable the executor (drawdown breach)
"""

from __future__ import annotations

from datetime import datetime

ORDER = ["NONE", "HALT_NEW", "FLATTEN_ALL", "FLATTEN_AND_DISABLE"]


def _max(a: str, b: str) -> str:
    return a if ORDER.index(a) >= ORDER.index(b) else b


def evaluate(state: dict, limits: dict, session: dict, now: datetime) -> dict:
    kl = limits["kill_switch"]
    action, reasons = "NONE", []
    equity = float(state["equity"])
    sod = float(state.get("start_of_day_equity") or equity)
    peak = float(state.get("peak_equity") or equity)
    positions = state.get("positions", [])

    day_pnl_pct = (equity / sod - 1) * 100 if sod else 0.0
    dd_pct = (1 - equity / peak) * 100 if peak else 0.0

    if state.get("disabled"):
        action = _max(action, "FLATTEN_AND_DISABLE" if positions else "HALT_NEW")
        reasons.append("executor already disabled")

    if dd_pct >= kl["drawdown_flatten_pct"]:
        action = _max(action, "FLATTEN_AND_DISABLE")
        reasons.append(f"drawdown {dd_pct:.2f}% >= {kl['drawdown_flatten_pct']}% from peak")

    if -day_pnl_pct >= kl["daily_loss_halt_pct"]:
        action = _max(action, "HALT_NEW")
        reasons.append(f"day P&L {day_pnl_pct:.2f}% breached -{kl['daily_loss_halt_pct']}%")

    if positions and session.get("must_flatten"):
        action = _max(action, "FLATTEN_ALL")
        reasons.append(session.get("reason", "flatten window"))

    last = state.get("last_check")
    if positions and last:
        gap_min = (now - datetime.fromisoformat(last)).total_seconds() / 60
        if gap_min > kl["missed_check_minutes"]:
            action = _max(action, "FLATTEN_ALL")
            reasons.append(f"{gap_min:.0f} min since last check (> {kl['missed_check_minutes']}) — "
                           "positions were unprotected")

    if state.get("data_error"):
        action = _max(action, "HALT_NEW")
        reasons.append(f"data error: {state['data_error']}")

    return {"action": action, "reasons": reasons or ["all clear"],
            "day_pnl_pct": round(day_pnl_pct, 3), "drawdown_pct": round(dd_pct, 3)}


def manage_positions(positions: list[dict], quotes: dict[str, float]) -> list[dict]:
    """Agent-checked stops and targets (the paper API has no resting stop orders).

    Returns exit instructions: [{symbol, qty, side, reason, limit_hint}].
    Missing quote for a held symbol => exit (fail closed).
    """
    exits = []
    for p in positions:
        sym, qty = p["symbol"], p["qty"]
        long = qty > 0
        close_side = "SELL" if long else "BUY_TO_COVER"
        px = quotes.get(sym)
        if px is None:
            exits.append({"symbol": sym, "qty": abs(qty), "side": close_side,
                          "reason": "no fresh quote — fail closed", "limit_hint": None})
            continue
        stop, target = p.get("stop"), p.get("target")
        if stop is not None and ((long and px <= stop) or (not long and px >= stop)):
            exits.append({"symbol": sym, "qty": abs(qty), "side": close_side,
                          "reason": f"stop hit: {px} vs stop {stop}", "limit_hint": px})
        elif target is not None and ((long and px >= target) or (not long and px <= target)):
            exits.append({"symbol": sym, "qty": abs(qty), "side": close_side,
                          "reason": f"target hit: {px} vs target {target}", "limit_hint": px})
    return exits
