"""Safety-drill runner: a hand-written snapshot in, the real engine out.

The engine is imported, not reimplemented: `plan.build` is the function
`python -m timon plan` calls. Snapshot shape follows `examples/snapshot.json`.
Two deliberate differences, both so a drill can never be mistaken for a live run:

  · a drill account id (`DRILL-0000`) instead of the competition account
  · nothing is written to `logs/decisions.jsonl`; drills never pollute the ledger

    .venv/bin/python video/drill/drill.py approve
    .venv/bin/python video/drill/drill.py stop
    .venv/bin/python video/drill/drill.py stale
    .venv/bin/python video/drill/drill.py halt
    .venv/bin/python video/drill/drill.py flatten
    .venv/bin/python video/drill/drill.py approve --input     # print the snapshot
    .venv/bin/python video/drill/drill.py approve --stage 3   # autonomy override
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from timon import config, plan as plan_mod  # noqa: E402

# 2026-11-20 10:00 ET — a real trading day inside the competition window.
NOW = datetime(2026, 11, 20, 15, 0, tzinfo=timezone.utc)
DRILL_ACCOUNT = {"competition_account_id": "DRILL-0000", "trd_env": "SIMULATE"}

BASE = {"SPY": 560.0, "QQQ": 480.0, "IWM": 230.0, "XLK": 250.0, "XLF": 52.0,
        "XLE": 90.0, "XLV": 150.0, "XLY": 220.0, "SMH": 300.0}

SCENES = {
    "approve": "clean RISK_ON day, one breakout clears its opening range",
    "stop": "a long is through its stop; the cycle exits before it enters",
    "stale": "the breakout quote is ten minutes old; the gate refuses it",
    "halt": "the day is down past the halt line; no new entries",
    "flatten": "equity is past the drawdown line; flatten everything and disable",
}


def _uptrend(start: float, step: float, n: int = 60) -> list[float]:
    return [round(start + i * step, 2) for i in range(n)]


def _daily_bars(price: float, pct: float = 0.004) -> list[dict]:
    bars = []
    for i in range(20):
        close = price * (1 + 0.004 * (i - 10) / 10)
        bars.append({"high": round(close * (1 + pct), 2),
                     "low": round(close * (1 - pct), 2),
                     "close": round(close, 2)})
    return bars


def _opening_range(price: float, pct: float = 0.003) -> list[dict]:
    return [{"high": round(price * (1 + pct), 2), "low": round(price * (1 - pct), 2),
             "close": round(price, 2), "volume": 4_000_000} for _ in range(6)]


def _state(equity: float = 100_000.0, positions: list[dict] | None = None) -> dict:
    return {
        "account_id": "DRILL-0000",
        "trd_env": "SIMULATE",
        "equity": equity,
        "start_of_day_equity": 100_000.0,
        "peak_equity": 100_000.0,
        "positions": positions or [],
        "orders_today": 0,
        "entries_today": 0,
        "consecutive_losses": 0,
        "last_check": None,
        "halted_today": False,
        "disabled": False,
    }


def snapshot(scene: str) -> dict:
    # A wide opening range keeps the stop far enough that the risk budget — not the
    # notional cap — decides the size, so the approve scene shows a real APPROVE.
    or_pct = 0.02 if scene == "approve" else 0.003
    quotes, bars = {}, {}
    for sym, px in BASE.items():
        quotes[sym] = {"last": round(px * 1.001, 2),
                       "time": (NOW - timedelta(seconds=5)).isoformat(),
                       "market_cap": 1.2e12, "avg_volume": 8.0e7}
        bars[sym] = _opening_range(px, or_pct)

    # One breakout only: SPY clears its opening-range high, everything else holds.
    quotes["SPY"]["last"] = round(BASE["SPY"] * (1 + or_pct + 0.004), 2)

    state = _state()
    if scene == "stale":
        quotes["SPY"]["time"] = (NOW - timedelta(seconds=600)).isoformat()
    elif scene == "halt":
        state = _state(equity=98_000.0)
    elif scene == "stop":
        state = _state(positions=[{"symbol": "QQQ", "qty": 100, "avg_cost": 480.0,
                                   "market_value": 48_000.0, "stop": 476.0, "target": 492.0}])
        quotes["QQQ"]["last"] = 474.6
    elif scene == "flatten":
        state = _state(equity=95_500.0, positions=[
            {"symbol": "QQQ", "qty": 100, "avg_cost": 480.0, "market_value": 47_500.0,
             "stop": 470.0, "target": 500.0},
            {"symbol": "SMH", "qty": 40, "avg_cost": 300.0, "market_value": 11_800.0,
             "stop": 290.0, "target": 320.0},
        ])

    return {
        "run_id": f"drill-{scene}",
        "now": NOW.isoformat(),
        "state": state,
        "quotes": quotes,
        "opening_range_bars": bars,
        "daily_bars": {sym: _daily_bars(px, 0.015 if scene == "approve" else 0.004)
                       for sym, px in BASE.items()},
        "spy_daily_closes": _uptrend(500.0, 0.9),
        "vix": 15.0,
        "sector_daily_closes": {sym: _uptrend(px * 0.9, px * 0.002)
                                for sym, px in BASE.items() if sym != "SPY"},
        "events": {},
        "allow_short": False,
    }


def main(argv: list[str]) -> int:
    scene = argv[1] if len(argv) > 1 else "approve"
    if scene not in SCENES:
        raise SystemExit(f"usage: drill.py [{'|'.join(SCENES)}] [--input] [--stage N]")
    snap = snapshot(scene)
    if "--input" in argv:
        json.dump(snap, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    limits = config.limits()
    stage = None
    if "--stage" in argv:
        stage = int(argv[argv.index("--stage") + 1])
        limits = {**limits, "autonomy": {**limits["autonomy"], "stage": stage}}

    sys.stderr.write(f"DRILL · {SCENES[scene]} · simulated snapshot, not market data")
    sys.stderr.write(f" · autonomy stage {stage} override\n" if stage else " · live config\n")
    plan = plan_mod.build(snap, limits, config.calendar(), DRILL_ACCOUNT)
    json.dump(plan, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
