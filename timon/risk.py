"""The Risk Auditor's deterministic gate.

Every proposal passes through `gate()`. It returns one verdict —
APPROVE | SHRINK | ESCALATE | BLOCK — plus a sized quantity and a list of
named checks, each with pass/fail and a human-readable detail. The LLM
auditor may add context or ask the Advisor, but it cannot overrule a BLOCK.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Check:
    name: str
    passed: bool
    detail: str
    hard: bool = True  # hard failure => BLOCK


@dataclass
class Verdict:
    verdict: str
    qty: int = 0
    risk_usd: float = 0.0
    risk_pct: float = 0.0
    notional: float = 0.0
    reasons: list[str] = field(default_factory=list)
    checks: list[Check] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict, "qty": self.qty, "risk_usd": round(self.risk_usd, 2),
            "risk_pct": round(self.risk_pct, 4), "notional": round(self.notional, 2),
            "reasons": self.reasons,
            "checks": [c.__dict__ for c in self.checks],
        }


def _age_sec(ts: str | None, now: datetime) -> float | None:
    if not ts:
        return None
    t = datetime.fromisoformat(ts)
    if t.tzinfo is None:
        return None
    return (now - t).total_seconds()


def gross_exposure(positions: list[dict]) -> float:
    return sum(abs(p.get("market_value", p.get("qty", 0) * p.get("last", p.get("avg_price", 0))))
               for p in positions)


def gate(proposal: dict, state: dict, account_cfg: dict, limits: dict,
         session: dict, now: datetime) -> Verdict:
    checks: list[Check] = []
    add = checks.append

    # 1. Account guard — never trade anywhere but the competition SIMULATE account.
    want = (account_cfg.get("competition_account_id") or "").strip()
    have = str(state.get("account_id") or "").strip()
    add(Check("account_configured", bool(want), "competition_account_id set in config/account.yaml"
              if want else "competition_account_id is empty — refuse all orders"))
    add(Check("account_match", bool(want) and want == have,
              f"state account {have or '∅'} {'==' if want == have else '!='} competition {want or '∅'}"))
    add(Check("simulate_env", account_cfg.get("trd_env") == "SIMULATE" and state.get("trd_env", "SIMULATE") == "SIMULATE",
              f"trd_env config={account_cfg.get('trd_env')} state={state.get('trd_env', 'SIMULATE')}"))

    # 2. Kill-switch state
    add(Check("executor_enabled", not state.get("disabled", False),
              "executor disabled by drawdown kill switch" if state.get("disabled") else "executor enabled"))
    add(Check("not_halted_today", not state.get("halted_today", False),
              "new orders halted for today" if state.get("halted_today") else "no daily halt"))

    # 3. Session
    add(Check("session_allows_entry", bool(session.get("can_enter")), session.get("reason", "")))

    # 4. Proposal sanity
    side = proposal.get("side")
    entry, stop = proposal.get("entry"), proposal.get("stop")
    valid = side in ("BUY", "SELL_SHORT") and entry and stop and entry > 0 and stop > 0 and entry != stop
    if valid:
        valid = (stop < entry) if side == "BUY" else (stop > entry)
    add(Check("proposal_valid", bool(valid), f"side={side} entry={entry} stop={stop}"))

    # 5. Fresh data
    kl = limits["kill_switch"]
    age = _age_sec(proposal.get("quote_time"), now)
    add(Check("quote_fresh", age is not None and 0 <= age <= kl["max_quote_age_sec"],
              "quote_time missing" if age is None else f"quote age {age:.0f}s (max {kl['max_quote_age_sec']}s)"))

    # 6. Universe
    uni = limits["universe"]
    sym = proposal.get("symbol", "")
    in_list = sym in uni["symbols"]
    add(Check("in_universe", in_list, f"{sym} {'in' if in_list else 'not in'} configured universe"))
    price = proposal.get("entry") or 0
    add(Check("min_price", price >= uni["min_price"], f"price {price} >= {uni['min_price']}"))
    mcap = proposal.get("market_cap")
    add(Check("min_market_cap", (mcap is None and in_list) or (mcap is not None and mcap >= uni["min_market_cap_usd"]),
              "market cap n/a — whitelisted ETF" if mcap is None else f"market cap {mcap:,.0f}"))
    vol = proposal.get("avg_volume")
    add(Check("min_avg_volume", vol is None and in_list or (vol is not None and vol >= uni["min_avg_volume"]),
              "avg volume n/a — whitelisted ETF" if vol is None else f"avg volume {vol:,.0f}", hard=vol is not None))

    # 7. Event risk
    strat = limits["strategy"]
    edays = proposal.get("earnings_within_days")
    add(Check("no_earnings", edays is None or edays > strat["earnings_block_days"],
              "no earnings flag" if edays is None else f"earnings in {edays} day(s)"))
    add(Check("no_news_veto", not proposal.get("news_veto", False),
              proposal.get("news_veto_reason") or "no news veto"))

    # 8. Order capacity and duplicates
    ol = limits["orders"]
    add(Check("orders_per_day", state.get("orders_today", 0) + 2 <= ol["max_orders_per_day"],
              f"{state.get('orders_today', 0)} orders today (+2 for entry and target) / {ol['max_orders_per_day']}"))
    add(Check("entries_per_day", state.get("entries_today", 0) < ol["max_new_entries_per_day"],
              f"{state.get('entries_today', 0)} entries today / {ol['max_new_entries_per_day']}"))
    held = {p["symbol"] for p in state.get("positions", [])}
    add(Check("no_duplicate", sym not in held, f"{sym} {'already held' if sym in held else 'not held'}"))

    hard_fail = [c for c in checks if not c.passed and c.hard]
    if hard_fail:
        return Verdict("BLOCK", reasons=[f"{c.name}: {c.detail}" for c in hard_fail], checks=checks)

    # 9. Sizing
    sz, ex = limits["sizing"], limits["exposure"]
    equity = float(state["equity"])
    regime = proposal.get("regime", "CHOP")
    risk_pct = float(sz["risk_per_trade_pct"])
    notes: list[str] = []
    if regime == "CHOP":
        risk_pct *= ex["chop_size_multiplier"]
        notes.append(f"CHOP: risk x{ex['chop_size_multiplier']}")
    if state.get("consecutive_losses", 0) >= limits["kill_switch"]["loss_streak_halve"]:
        risk_pct *= 0.5
        notes.append(f"{state['consecutive_losses']} losses in a row: risk halved")

    per_share = abs(entry - stop)
    qty_risk = math.floor(equity * risk_pct / 100 / per_share)
    qty_notional = math.floor(equity * sz["max_position_notional_pct"] / 100 / entry)
    qty_gap = math.floor(equity * sz["gap_loss_cap_pct"] / 100 / (per_share * sz["gap_multiple"]))
    room = equity * ex["gross_cap_pct"].get(regime, 0) / 100 - gross_exposure(state.get("positions", []))
    qty_gross = max(0, math.floor(room / entry))
    qty_platform = math.floor(equity * ex["platform_single_stock_cap_pct"] / 100 / entry)

    qty = min(qty_risk, qty_notional, qty_gap, qty_gross, qty_platform)
    binding = min([("risk", qty_risk), ("notional cap", qty_notional), ("gap rule", qty_gap),
                   ("gross exposure", qty_gross), ("platform 40% cap", qty_platform)], key=lambda x: x[1])

    if qty < sz["min_shares"]:
        checks.append(Check("size_positive", False, f"sized qty {qty} (bound by {binding[0]})"))
        return Verdict("BLOCK", reasons=[f"size_positive: qty {qty} bound by {binding[0]}"] + notes,
                       checks=checks)
    checks.append(Check("size_positive", True, f"qty {qty} (bound by {binding[0]})"))

    risk_usd = qty * per_share
    v = Verdict("APPROVE", qty=qty, risk_usd=risk_usd, risk_pct=risk_usd / equity * 100,
                notional=qty * entry, reasons=notes, checks=checks)
    if binding[0] != "risk" or notes:
        v.verdict = "SHRINK"
        v.reasons.append(f"size reduced: bound by {binding[0]}")

    # 10. Earned autonomy
    stage = int(limits["autonomy"]["stage"])
    if stage == 1:
        v.reasons.append("autonomy stage 1: every order needs human approval")
        v.verdict = "ESCALATE"
    elif stage == 2 and v.risk_pct > float(limits["autonomy"]["auto_risk_pct_stage2"]):
        v.reasons.append(f"autonomy stage 2: risk {v.risk_pct:.2f}% > auto limit")
        v.verdict = "ESCALATE"
    return v
