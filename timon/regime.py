"""Daily market regime: RISK_ON / RISK_OFF / CHOP.

Rules (deterministic, explainable):
  RISK_ON  : SPY above 20 and 50 SMA, 20 > 50, VIX < vix_risk_off, breadth >= 50%
  RISK_OFF : SPY below 50 SMA, or VIX >= vix_risk_off
  CHOP     : everything else, or missing data (fail closed)
"""

from __future__ import annotations

from .indicators import sma

VIX_RISK_OFF = 25.0
BREADTH_MIN = 50.0


def classify(spy_closes: list[float], vix: float | None, breadth_pct: float | None) -> dict:
    s20, s50 = sma(spy_closes, 20), sma(spy_closes, 50)
    evidence: list[str] = []

    if s20 is None or s50 is None or not spy_closes:
        return {"regime": "CHOP", "evidence": ["insufficient SPY history (need 50 closes) — fail closed"],
                "inputs": {"closes": len(spy_closes)}}

    px = spy_closes[-1]
    evidence.append(f"SPY {px:.2f} vs SMA20 {s20:.2f} / SMA50 {s50:.2f}")
    if vix is not None:
        evidence.append(f"VIX {vix:.2f} (risk-off at {VIX_RISK_OFF})")
    if breadth_pct is not None:
        evidence.append(f"breadth {breadth_pct:.0f}% of sector ETFs above 20 SMA")

    if px < s50 or (vix is not None and vix >= VIX_RISK_OFF):
        regime = "RISK_OFF"
    elif (px > s20 > s50 and vix is not None and vix < VIX_RISK_OFF
          and breadth_pct is not None and breadth_pct >= BREADTH_MIN):
        regime = "RISK_ON"
    else:
        regime = "CHOP"
        if vix is None or breadth_pct is None:
            evidence.append("VIX or breadth missing — cannot confirm RISK_ON")

    return {"regime": regime, "evidence": evidence,
            "inputs": {"spy": px, "sma20": round(s20, 4), "sma50": round(s50, 4),
                       "vix": vix, "breadth_pct": breadth_pct}}


def breadth(sector_closes: dict[str, list[float]], n: int = 20) -> float | None:
    """% of sector ETFs whose last close is above their n-day SMA."""
    flags = []
    for closes in sector_closes.values():
        s = sma(closes, n)
        if s is not None:
            flags.append(closes[-1] > s)
    if not flags:
        return None
    return 100.0 * sum(flags) / len(flags)
