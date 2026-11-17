"""Append-only, hash-chained decision ledger + performance metrics.

Each line in logs/decisions.jsonl carries `prev_hash` and `hash`
(sha256 of prev_hash + canonical JSON). Git adds a second chain on top.
`verify()` proves no line was edited or removed.
"""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path

GENESIS = "0" * 64


def _canon(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _last_hash(path: Path) -> tuple[str, int]:
    if not path.exists():
        return GENESIS, 0
    last, n = GENESIS, 0
    with path.open() as f:
        for line in f:
            if line.strip():
                last, n = json.loads(line)["hash"], n + 1
    return last, n


def append(path: Path, record: dict) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    prev, n = _last_hash(path)
    body = {**record}
    body.setdefault("ts", datetime.now(timezone.utc).isoformat())
    body["seq"] = n + 1
    body["prev_hash"] = prev
    body["hash"] = hashlib.sha256((prev + _canon(body)).encode()).hexdigest()
    with path.open("a") as f:
        f.write(_canon(body) + "\n")
    return body


def verify(path: Path) -> dict:
    prev, n = GENESIS, 0
    if not path.exists():
        return {"ok": True, "entries": 0, "broken_at": None}
    with path.open() as f:
        for line in f:
            if not line.strip():
                continue
            n += 1
            rec = json.loads(line)
            h = rec.pop("hash")
            if rec.get("prev_hash") != prev or hashlib.sha256((prev + _canon(rec)).encode()).hexdigest() != h:
                return {"ok": False, "entries": n, "broken_at": n}
            prev = h
    return {"ok": True, "entries": n, "broken_at": None}


def read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.open() if l.strip()]


def metrics(records: list[dict], daily_returns_pct: list[float] | None = None) -> dict:
    """Trade stats from records with type == 'close' (fields: pnl, r_multiple)."""
    closes = [r for r in records if r.get("type") == "close" and r.get("pnl") is not None]
    wins = [r["pnl"] for r in closes if r["pnl"] > 0]
    losses = [r["pnl"] for r in closes if r["pnl"] <= 0]
    n = len(closes)
    win_rate = len(wins) / n if n else 0.0
    avg_win = statistics.mean(wins) if wins else 0.0
    avg_loss = abs(statistics.mean(losses)) if losses else 0.0
    rs = [r["r_multiple"] for r in closes if r.get("r_multiple") is not None]

    verdicts: dict[str, int] = {}
    for r in records:
        if r.get("type") == "verdict":
            verdicts[r.get("verdict", "?")] = verdicts.get(r.get("verdict", "?"), 0) + 1

    sharpe = None
    if daily_returns_pct and len(daily_returns_pct) >= 2:
        sd = statistics.stdev(daily_returns_pct)
        if sd > 0:
            sharpe = statistics.mean(daily_returns_pct) / sd * math.sqrt(252)

    return {
        "trades": n, "win_rate": round(win_rate, 4),
        "avg_win": round(avg_win, 2), "avg_loss": round(avg_loss, 2),
        "expectancy_usd": round(win_rate * avg_win - (1 - win_rate) * avg_loss, 2) if n else 0.0,
        "avg_r": round(statistics.mean(rs), 3) if rs else None,
        "total_pnl": round(sum(r["pnl"] for r in closes), 2),
        "verdicts": verdicts,
        "sharpe_annualised": round(sharpe, 3) if sharpe is not None else None,
    }
