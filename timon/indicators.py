"""Pure-Python indicators. Inputs are plain lists so agents can pass MCP data as JSON."""

from __future__ import annotations

from typing import Sequence


def sma(values: Sequence[float], n: int) -> float | None:
    if n <= 0 or len(values) < n:
        return None
    return sum(values[-n:]) / n


def ema(values: Sequence[float], n: int) -> float | None:
    if n <= 0 or len(values) < n:
        return None
    k = 2 / (n + 1)
    e = sum(values[:n]) / n
    for v in values[n:]:
        e = v * k + e * (1 - k)
    return e


def atr(bars: Sequence[dict], n: int = 14) -> float | None:
    """bars: [{high, low, close}, ...] oldest first."""
    if len(bars) < n + 1:
        return None
    trs = []
    for prev, cur in zip(bars[:-1], bars[1:]):
        trs.append(max(cur["high"] - cur["low"],
                       abs(cur["high"] - prev["close"]),
                       abs(cur["low"] - prev["close"])))
    return sum(trs[-n:]) / n


def opening_range(bars: Sequence[dict]) -> dict | None:
    """bars: intraday bars inside the opening-range window. Returns high/low/volume."""
    if not bars:
        return None
    return {
        "high": max(b["high"] for b in bars),
        "low": min(b["low"] for b in bars),
        "volume": sum(b.get("volume", 0) for b in bars),
    }


def pct_change(values: Sequence[float], n: int) -> float | None:
    if len(values) <= n or values[-n - 1] == 0:
        return None
    return (values[-1] / values[-n - 1] - 1) * 100
