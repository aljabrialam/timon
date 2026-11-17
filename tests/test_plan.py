import json
import subprocess
import sys
from pathlib import Path

from timon import plan

ROOT = Path(__file__).resolve().parent.parent


def snapshot():
    out = subprocess.run([sys.executable, str(ROOT / "examples/make_snapshot.py")],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def test_plan_end_to_end(limits, cal, acct):
    limits["autonomy"]["stage"] = 3
    p = plan.build(snapshot(), limits, cal, acct)
    assert p["kill"]["action"] == "NONE"
    assert p["regime"]["regime"] == "RISK_ON"
    syms = {o["symbol"] for o in p["orders"]}
    assert {"QQQ", "XLK"} <= syms          # breakouts in RISK_ON
    assert "SMH" not in syms               # news veto
    smh = next(v for v in p["verdicts"] if v["symbol"] == "SMH")
    assert smh["verdict"] == "BLOCK"
    assert all(o["qty"] > 0 and o["stop"] < o["limit"] < o["target"] for o in p["orders"])
    assert p["state_updates"]["last_check"]


def test_stage1_routes_everything_to_human(limits, cal, acct):
    p = plan.build(snapshot(), limits, cal, acct)
    assert p["orders"] == [] and len(p["escalations"]) >= 2


def test_unconfigured_account_blocks_all(limits, cal):
    limits["autonomy"]["stage"] = 3
    p = plan.build(snapshot(), limits, cal, {"competition_account_id": "", "trd_env": "SIMULATE"})
    assert p["orders"] == [] and all(v["verdict"] == "BLOCK" for v in p["verdicts"])


def test_flatten_path_skips_entries(limits, cal, acct):
    s = snapshot()
    s["state"]["peak_equity"] = 106000.0  # 5.7% drawdown
    s["state"]["positions"] = [{"symbol": "SPY", "qty": 20, "stop": 590, "target": 620}]
    p = plan.build(s, limits, cal, acct)
    assert p["kill"]["action"] == "FLATTEN_AND_DISABLE"
    assert p["exits"][0]["symbol"] == "SPY" and p["orders"] == []
    assert p["state_updates"]["disabled"] is True


def test_cli_session_and_verify(tmp_path):
    r = subprocess.run([sys.executable, "-m", "timon", "session", "--now", "2026-11-19T10:30:00-05:00"],
                       cwd=ROOT, capture_output=True, text=True, check=True)
    assert json.loads(r.stdout)["can_enter"] is True
