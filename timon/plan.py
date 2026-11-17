"""One trading cycle as a pure function: snapshot in, plan out.

The LLM agents' job shrinks to three things:
  1. gather a snapshot from the Moomoo MCP (see skills/timon-researcher)
  2. run `timon plan snapshot.json`
  3. execute the plan's orders and report fills (skills/timon-executor)

Order of operations (safety first):
  session -> kill switch -> exits -> regime -> signals -> risk gate -> orders
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from . import clock, killswitch, regime as regime_mod, risk, signals
from .indicators import atr, opening_range


def build(snapshot: dict, limits: dict, cal: dict, account_cfg: dict) -> dict:
    now = datetime.fromisoformat(snapshot["now"]) if snapshot.get("now") else datetime.now(timezone.utc)
    state = snapshot["state"]
    quotes = snapshot.get("quotes", {})
    run_id = snapshot.get("run_id") or uuid.uuid4().hex[:12]

    sess = clock.session_info(now, cal, limits).to_dict()
    kill = killswitch.evaluate(state, limits, sess, now)

    plan: dict = {"run_id": run_id, "now": now.isoformat(), "session": sess, "kill": kill,
                  "exits": [], "regime": None, "signals": [], "shadow": [], "verdicts": [],
                  "orders": [], "escalations": [], "state_updates": {}}

    positions = state.get("positions", [])
    last_px = {s: q.get("last") for s, q in quotes.items() if q.get("last") is not None}

    # Exits first
    if kill["action"] in ("FLATTEN_ALL", "FLATTEN_AND_DISABLE"):
        for p in positions:
            plan["exits"].append({"symbol": p["symbol"], "qty": abs(p["qty"]),
                                  "side": "SELL" if p["qty"] > 0 else "BUY_TO_COVER",
                                  "reason": f"kill switch {kill['action']}: {'; '.join(kill['reasons'])}",
                                  "limit_hint": last_px.get(p["symbol"])})
        if kill["action"] == "FLATTEN_AND_DISABLE":
            plan["state_updates"]["disabled"] = True
    else:
        plan["exits"] = killswitch.manage_positions(positions, last_px)

    if kill["action"] != "NONE":
        if kill["action"] == "HALT_NEW":
            plan["state_updates"]["halted_today"] = True
        plan["note"] = "no new entries: kill switch " + kill["action"]
        plan["state_updates"]["last_check"] = now.isoformat()
        return plan

    plan["state_updates"]["last_check"] = now.isoformat()

    # Regime
    sector = snapshot.get("sector_daily_closes", {})
    reg = regime_mod.classify(snapshot.get("spy_daily_closes", []), snapshot.get("vix"),
                              regime_mod.breadth(sector) if sector else None)
    plan["regime"] = reg

    if not sess["can_enter"]:
        plan["note"] = "no new entries: " + sess["reason"]
        return plan

    strat = limits["strategy"]
    exiting = {e["symbol"] for e in plan["exits"]}
    for sym in limits["universe"]["symbols"]:
        q = quotes.get(sym)
        bars = snapshot.get("opening_range_bars", {}).get(sym)
        if not q or q.get("last") is None or not bars:
            plan["signals"].append({"symbol": sym, "action": "HOLD", "reason": "missing quote or opening-range bars"})
            continue
        orng = opening_range(bars)
        a = atr(snapshot.get("daily_bars", {}).get(sym, []), 14)
        kw = dict(target_r=strat["target_r"], stop_atr_multiple=strat["stop_atr_multiple"],
                  allow_short=bool(snapshot.get("allow_short", False)))
        sig = signals.orb_signal(sym, reg["regime"], orng, q["last"], a, **kw)
        plan["shadow"].append(signals.orb_signal(sym, reg["regime"], orng, q["last"], a, shadow=True, **kw))
        plan["signals"].append(sig)
        if sig["action"] != "PROPOSE" or sym in exiting:
            continue

        ev = snapshot.get("events", {}).get(sym, {})
        proposal = {**sig, "quote_time": q.get("time"), "market_cap": q.get("market_cap"),
                    "avg_volume": q.get("avg_volume"), **ev}
        v = risk.gate(proposal, state, account_cfg, limits, sess, now).to_dict()
        v["symbol"] = sym
        plan["verdicts"].append(v)

        order = {"intent": "ENTRY", "symbol": sym, "side": sig["side"], "qty": v["qty"],
                 "limit": sig["entry"], "stop": sig["stop"], "target": sig["target"],
                 "risk_usd": v["risk_usd"], "verdict": v["verdict"], "reason": sig["reason"]}
        if v["verdict"] in ("APPROVE", "SHRINK"):
            plan["orders"].append(order)
            state = {**state, "positions": positions + [{"symbol": sym, "qty": v["qty"],
                                                         "market_value": v["notional"]}],
                     "entries_today": state.get("entries_today", 0) + 1,
                     "orders_today": state.get("orders_today", 0) + 2}
            positions = state["positions"]
        elif v["verdict"] == "ESCALATE":
            plan["escalations"].append(order)

    return plan
