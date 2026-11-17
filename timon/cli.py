"""Timón CLI — every agent action goes through here so it is deterministic and logged.

Usage (JSON in, JSON out):
  python -m timon session [--now ISO]
  python -m timon plan snapshot.json [--no-log]
  python -m timon gate proposal.json state.json [--now ISO]
  python -m timon killswitch state.json [--now ISO]
  python -m timon log TYPE record.json          # TYPE: fill | close | note | approval | error
  python -m timon verify
  python -m timon metrics [--daily daily_returns.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import clock, config, journal, killswitch, plan as plan_mod, risk

LEDGER = config.ROOT / "logs" / "decisions.jsonl"


def _load(p: str) -> dict:
    return json.load(sys.stdin) if p == "-" else json.loads(Path(p).read_text())


def _now(s: str | None) -> datetime:
    return datetime.fromisoformat(s) if s else datetime.now(timezone.utc)


def _out(obj) -> None:
    json.dump(obj, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


def log_plan(p: dict, ledger: Path = LEDGER) -> None:
    rid, ts = p["run_id"], p["now"]
    base = {"run_id": rid, "ts": ts}
    journal.append(ledger, {**base, "type": "cycle", "session": p["session"]["session"],
                            "session_reason": p["session"]["reason"], "kill": p["kill"],
                            "regime": (p["regime"] or {}).get("regime")})
    for e in p["exits"]:
        journal.append(ledger, {**base, "type": "exit_intent", **e})
    for v in p["verdicts"]:
        journal.append(ledger, {**base, "type": "verdict", "symbol": v["symbol"], "verdict": v["verdict"],
                                "qty": v["qty"], "risk_usd": v["risk_usd"], "reasons": v["reasons"],
                                "failed_checks": [c["name"] for c in v["checks"] if not c["passed"]]})
    for s in p["shadow"]:
        if s.get("action") == "PROPOSE":
            journal.append(ledger, {**base, "type": "shadow", "symbol": s["symbol"], "side": s["side"],
                                    "entry": s["entry"], "stop": s["stop"], "target": s["target"]})


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="timon")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("session"); s.add_argument("--now")
    s = sub.add_parser("plan"); s.add_argument("snapshot"); s.add_argument("--no-log", action="store_true")
    s = sub.add_parser("gate"); s.add_argument("proposal"); s.add_argument("state"); s.add_argument("--now")
    s = sub.add_parser("killswitch"); s.add_argument("state"); s.add_argument("--now")
    s = sub.add_parser("log"); s.add_argument("type"); s.add_argument("record")
    sub.add_parser("verify")
    s = sub.add_parser("metrics"); s.add_argument("--daily")

    a = ap.parse_args(argv)
    limits, cal, acct = config.limits(), config.calendar(), config.account()

    if a.cmd == "session":
        _out(clock.session_info(_now(a.now), cal, limits).to_dict())
    elif a.cmd == "plan":
        p = plan_mod.build(_load(a.snapshot), limits, cal, acct)
        if not a.no_log:
            log_plan(p)
        _out(p)
    elif a.cmd == "gate":
        now = _now(a.now)
        sess = clock.session_info(now, cal, limits).to_dict()
        _out(risk.gate(_load(a.proposal), _load(a.state), acct, limits, sess, now).to_dict())
    elif a.cmd == "killswitch":
        now = _now(a.now)
        sess = clock.session_info(now, cal, limits).to_dict()
        _out(killswitch.evaluate(_load(a.state), limits, sess, now))
    elif a.cmd == "log":
        _out(journal.append(LEDGER, {"type": a.type, **_load(a.record)}))
    elif a.cmd == "verify":
        res = journal.verify(LEDGER)
        _out(res)
        return 0 if res["ok"] else 1
    elif a.cmd == "metrics":
        daily = _load(a.daily) if a.daily else None
        _out(journal.metrics(journal.read(LEDGER), daily))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
