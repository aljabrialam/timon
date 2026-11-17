import json

from timon import journal, regime, signals
from timon.indicators import atr, ema, opening_range, sma
from conftest import closes


def test_hash_chain_detects_tampering(tmp_path):
    p = tmp_path / "d.jsonl"
    for i in range(3):
        journal.append(p, {"type": "note", "i": i})
    assert journal.verify(p) == {"ok": True, "entries": 3, "broken_at": None}
    lines = p.read_text().splitlines()
    rec = json.loads(lines[1]); rec["i"] = 99
    lines[1] = json.dumps(rec)
    p.write_text("\n".join(lines) + "\n")
    assert journal.verify(p)["broken_at"] == 2


def test_metrics_expectancy_and_sharpe():
    recs = [{"type": "close", "pnl": 100, "r_multiple": 1}] * 9 + [{"type": "close", "pnl": -1200, "r_multiple": -12}]
    m = journal.metrics(recs, [0.2, -0.1, 0.3, 0.1])
    assert m["trades"] == 10 and m["expectancy_usd"] == -30.0  # the briefing's 90%-win-rate example
    assert m["sharpe_annualised"] is not None


def test_indicators():
    assert sma([1, 2, 3, 4], 2) == 3.5
    assert ema([1] * 10, 5) == 1
    bars = [{"high": 11, "low": 9, "close": 10}] * 16
    assert atr(bars, 14) == 2
    assert opening_range([{"high": 5, "low": 3, "volume": 10}, {"high": 6, "low": 4, "volume": 5}]) == \
        {"high": 6, "low": 3, "volume": 15}


def test_regime_risk_on_off_chop():
    up = closes(400, 1)
    assert regime.classify(up, 15, 70)["regime"] == "RISK_ON"
    assert regime.classify(up, 30, 70)["regime"] == "RISK_OFF"
    assert regime.classify(closes(460, -1), 15, 70)["regime"] == "RISK_OFF"
    assert regime.classify(up, None, 70)["regime"] == "CHOP"  # missing VIX -> fail closed
    assert regime.classify(up[:10], 15, 70)["regime"] == "CHOP"


def test_orb_signal_respects_regime():
    orng = {"high": 101, "low": 99}
    s = signals.orb_signal("SPY", "RISK_ON", orng, 101.5, 1.0)
    assert s["action"] == "PROPOSE" and s["side"] == "BUY" and s["stop"] == 100.5  # ATR stop tighter
    assert s["target"] == 103.5
    assert signals.orb_signal("SPY", "RISK_OFF", orng, 101.5, 1.0)["action"] == "HOLD"
    assert signals.orb_signal("SPY", "RISK_ON", orng, 98.5, 1.0)["action"] == "HOLD"
    assert signals.orb_signal("SPY", "RISK_ON", orng, 98.5, 1.0, shadow=True)["action"] == "PROPOSE"
    assert signals.orb_signal("SPY", "RISK_ON", orng, 100.0, 1.0)["action"] == "HOLD"
