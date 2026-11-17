"""Generate a SYNTHETIC snapshot for dry runs. Not market data.

This is the exact shape the Researcher agent must build from the Moomoo MCP.
Usage: python examples/make_snapshot.py > examples/snapshot.json
"""

import json
import sys


def ramp(start, step, n):
    return [round(start + i * step, 2) for i in range(n)]


def bars(closes, spread=1.0):
    return [{"high": c + spread, "low": c - spread, "close": c} for c in closes]


syms = ["SPY", "QQQ", "IWM", "XLK", "XLF", "XLE", "XLV", "XLY", "SMH"]
base = {"SPY": 600, "QQQ": 520, "IWM": 230, "XLK": 250, "XLF": 52, "XLE": 90, "XLV": 145, "XLY": 220, "SMH": 280}
now = "2026-11-19T10:35:00-05:00"

snap = {
    "run_id": "dryrun-0001",
    "now": now,
    "allow_short": False,
    "state": {
        "account_id": "COMP123", "trd_env": "SIMULATE",
        "equity": 100000.0, "start_of_day_equity": 100000.0, "peak_equity": 100000.0,
        "positions": [], "orders_today": 0, "entries_today": 0, "consecutive_losses": 0,
        "last_check": "2026-11-19T10:30:00-05:00",
    },
    "spy_daily_closes": ramp(560, 0.8, 60),
    "vix": 16.2,
    "sector_daily_closes": {s: ramp(base[s] * 0.9, base[s] * 0.002, 60) for s in syms[3:]},
    "daily_bars": {s: bars(ramp(base[s] * 0.95, base[s] * 0.001, 30), base[s] * 0.006) for s in syms},
    "opening_range_bars": {s: [{"high": base[s] * 1.002, "low": base[s] * 0.998, "volume": 1_000_000}] for s in syms},
    "quotes": {s: {"last": round(base[s] * (1.004 if s in ("QQQ", "SMH", "XLK") else 1.0), 2),
                   "time": "2026-11-19T10:34:30-05:00", "market_cap": None, "avg_volume": None}
               for s in syms},
    "events": {"SMH": {"earnings_within_days": None, "news_veto": True,
                       "news_veto_reason": "semis: NVDA reports after close today"}},
}
json.dump(snap, sys.stdout, indent=2)
