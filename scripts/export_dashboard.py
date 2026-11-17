"""Export the dashboard payload from the ledger, state and an optional snapshot.

Read-only: never logs a cycle, never touches a broker.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from timon import clock, config, journal, plan as plan_mod

LEDGER = ROOT / "logs" / "decisions.jsonl"
STATE = ROOT / "state" / "state.json"
OUT = ROOT / "dashboard" / "data.json"


def _json(path: Path, default):
    return json.loads(path.read_text()) if path.exists() else default


def equity_curve(records: list[dict], state: dict) -> dict:
    closes = [r for r in records if r.get("type") == "close" and r.get("pnl") is not None and r.get("ts")]
    equity = float(state.get("equity") or 0.0)
    base = equity - sum(float(r["pnl"]) for r in closes)

    by_day: dict[str, float] = {}
    for r in closes:
        day = r["ts"][:10]
        by_day[day] = by_day.get(day, 0.0) + float(r["pnl"])

    points, running = [], base
    for day in sorted(by_day):
        running += by_day[day]
        points.append({"date": day, "equity": round(running, 2)})

    today = datetime.now(timezone.utc).date().isoformat()
    if points and points[-1]["date"] == today:
        points[-1]["equity"] = round(equity, 2)
    else:
        points.append({"date": today, "equity": round(equity, 2)})

    peak, max_dd = 0.0, 0.0
    for p in points:
        peak = max(peak, p["equity"])
        if peak:
            max_dd = max(max_dd, (peak - p["equity"]) / peak * 100)
    current_dd = (peak - points[-1]["equity"]) / peak * 100 if peak else 0.0

    returns = [
        (points[i]["equity"] - points[i - 1]["equity"]) / points[i - 1]["equity"] * 100
        for i in range(1, len(points))
        if points[i - 1]["equity"]
    ]

    return {
        "start_equity": round(base, 2),
        "points": points,
        "daily_returns_pct": [round(r, 4) for r in returns],
        "max_drawdown_pct": round(max_dd, 2),
        "current_drawdown_pct": round(current_dd, 2),
    }


def build_payload(snapshot_path: Path | None, now: datetime) -> dict:
    limits, cal, acct = config.limits(), config.calendar(), config.account()
    state = _json(STATE, {})
    records = journal.read(LEDGER)
    verified = journal.verify(LEDGER)
    curve = equity_curve(records, state)
    metrics = journal.metrics(records, curve["daily_returns_pct"])

    snap = _json(snapshot_path, None) if snapshot_path else None
    plan = plan_mod.build(snap, limits, cal, acct) if snap else None

    verdicts = [r for r in records if r.get("type") == "verdict"][-25:][::-1]
    ledger_tail = records[-12:][::-1]

    return {
        "generated_at": now.isoformat(),
        "session": clock.session_info(now, cal, limits).to_dict(),
        "kill": plan["kill"] if plan else None,
        "regime": (plan or {}).get("regime"),
        "plan": None
        if plan is None
        else {
            "run_id": plan["run_id"],
            "note": plan.get("note"),
            "signals": len(plan["signals"]),
            "verdicts": len(plan["verdicts"]),
            "orders": len(plan["orders"]),
            "escalations": len(plan["escalations"]),
            "exits": len(plan["exits"]),
            "shadow": [s for s in plan["shadow"] if s.get("action") == "PROPOSE"],
        },
        "account": {
            "configured": bool(acct.get("competition_account_id")),
            "id": acct.get("competition_account_id") or "",
            "name": acct.get("competition_account_name", ""),
            "env": acct.get("trd_env", ""),
        },
        "state": state,
        "limits": {
            "risk_per_trade_pct": limits["sizing"]["risk_per_trade_pct"],
            "max_position_notional_pct": limits["sizing"]["max_position_notional_pct"],
            "max_orders_per_day": limits["orders"]["max_orders_per_day"],
            "max_new_entries_per_day": limits["orders"]["max_new_entries_per_day"],
            "entry_cutoff_et": limits["orders"]["entry_cutoff_et"],
            "eod_flatten_et": limits["strategy"]["eod_flatten_et"],
            "target_r": limits["strategy"]["target_r"],
            "gross_cap_pct": limits["exposure"]["gross_cap_pct"],
            "daily_loss_halt_pct": limits["kill_switch"]["daily_loss_halt_pct"],
            "drawdown_flatten_pct": limits["kill_switch"]["drawdown_flatten_pct"],
            "stage": limits["autonomy"]["stage"],
        },
        "universe": limits["universe"]["symbols"],
        "metrics": metrics,
        "equity": curve,
        "ledger": {"ok": verified["ok"], "entries": verified["entries"], "broken_at": verified["broken_at"]},
        "verdicts": verdicts,
        "recent": ledger_tail,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="export_dashboard")
    ap.add_argument("--snapshot", type=Path, default=ROOT / "state" / "snapshot.json")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--now")
    a = ap.parse_args(argv)

    snapshot = a.snapshot if a.snapshot.exists() else None
    now = datetime.fromisoformat(a.now) if a.now else datetime.now(timezone.utc)
    payload = build_payload(snapshot, now)

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    print(json.dumps({"out": str(a.out), "snapshot": str(snapshot) if snapshot else None,
                      "entries": payload["ledger"]["entries"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
