from timon import clock
from timon.killswitch import evaluate, manage_positions
from conftest import et


def ks(state, limits, cal, now):
    return evaluate(state, limits, clock.session_info(now, cal, limits).to_dict(), now)


def test_all_clear(state, limits, cal, now):
    assert ks(state, limits, cal, now)["action"] == "NONE"


def test_daily_loss_halts(state, limits, cal, now):
    state["equity"] = 98400.0
    assert ks(state, limits, cal, now)["action"] == "HALT_NEW"


def test_drawdown_flattens_and_disables(state, limits, cal, now):
    state.update(peak_equity=104500.0, equity=100000.0, start_of_day_equity=100000.0)
    assert ks(state, limits, cal, now)["action"] == "FLATTEN_AND_DISABLE"


def test_eod_flattens_open_positions(state, limits, cal):
    state["positions"] = [{"symbol": "SPY", "qty": 10}]
    now = et("2026-11-19T15:51")
    state["last_check"] = now.isoformat()
    assert ks(state, limits, cal, now)["action"] == "FLATTEN_ALL"


def test_missed_check_flattens(state, limits, cal, now):
    state["positions"] = [{"symbol": "SPY", "qty": 10}]
    state["last_check"] = et("2026-11-19T10:10").isoformat()
    r = ks(state, limits, cal, now)
    assert r["action"] == "FLATTEN_ALL" and "unprotected" in " ".join(r["reasons"])


def test_final_day_flatten(state, limits, cal):
    state["positions"] = [{"symbol": "SPY", "qty": 10}]
    now = et("2026-11-27T12:50")
    state["last_check"] = now.isoformat()
    assert ks(state, limits, cal, now)["action"] == "FLATTEN_ALL"


def test_stop_and_target_and_missing_quote():
    pos = [{"symbol": "SPY", "qty": 10, "stop": 99, "target": 104},
           {"symbol": "QQQ", "qty": -5, "stop": 505, "target": 490},
           {"symbol": "IWM", "qty": 3, "stop": 200, "target": 210}]
    exits = {e["symbol"]: e for e in manage_positions(pos, {"SPY": 98.9, "QQQ": 489.5})}
    assert "stop hit" in exits["SPY"]["reason"] and exits["SPY"]["side"] == "SELL"
    assert "target hit" in exits["QQQ"]["reason"] and exits["QQQ"]["side"] == "BUY_TO_COVER"
    assert "fail closed" in exits["IWM"]["reason"]
