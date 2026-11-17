"""Opening-range breakout (ORB) signal, gated by regime.

Produces a *proposal* only. The risk gate decides; the executor acts.
`shadow=True` ignores the regime — used for the logged-only baseline branch.
"""

from __future__ import annotations


def orb_signal(symbol: str, regime: str, orange: dict, last: float, atr: float | None,
               target_r: float = 2.0, stop_atr_multiple: float = 1.0,
               allow_short: bool = False, shadow: bool = False) -> dict:
    hi, lo = orange["high"], orange["low"]
    base = {"symbol": symbol, "regime": regime, "strategy": "ORB-shadow" if shadow else "ORB",
            "last": last, "or_high": hi, "or_low": lo, "atr": atr}

    long_break = last > hi
    short_break = last < lo

    if not (long_break or short_break):
        return {**base, "action": "HOLD", "reason": f"no breakout: {lo:.2f} <= {last:.2f} <= {hi:.2f}"}

    side = "BUY" if long_break else "SELL_SHORT"

    if not shadow:
        if regime == "CHOP" and side == "SELL_SHORT":
            return {**base, "action": "HOLD", "reason": "CHOP: no shorts"}
        if regime == "RISK_ON" and side == "SELL_SHORT":
            return {**base, "action": "HOLD", "reason": "downside break against RISK_ON regime"}
        if regime == "RISK_OFF" and side == "BUY":
            return {**base, "action": "HOLD", "reason": "upside break against RISK_OFF regime"}
        if side == "SELL_SHORT" and not allow_short:
            return {**base, "action": "HOLD", "reason": "shorts disabled"}

    range_stop = lo if side == "BUY" else hi
    atr_stop = None if atr is None else (last - stop_atr_multiple * atr if side == "BUY"
                                         else last + stop_atr_multiple * atr)
    if atr_stop is None:
        stop = range_stop
    else:
        stop = max(range_stop, atr_stop) if side == "BUY" else min(range_stop, atr_stop)  # tighter

    risk_per_share = abs(last - stop)
    if risk_per_share <= 0:
        return {**base, "action": "HOLD", "reason": "zero stop distance"}
    target = last + target_r * risk_per_share if side == "BUY" else last - target_r * risk_per_share

    return {**base, "action": "PROPOSE", "side": side, "entry": round(last, 2),
            "stop": round(stop, 2), "target": round(target, 2),
            "reason": f"{'upside' if side == 'BUY' else 'downside'} break of opening range "
                      f"in {regime}; stop {'range' if stop == range_stop else 'ATR'}-based"}
