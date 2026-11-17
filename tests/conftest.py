import copy
from datetime import datetime

import pytest

from timon import clock, config

ET = clock.ET


@pytest.fixture
def limits():
    return copy.deepcopy(config.limits())


@pytest.fixture
def cal():
    return config.calendar()


@pytest.fixture
def acct():
    return {"competition_account_id": "COMP123", "trd_env": "SIMULATE"}


def et(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=ET)


@pytest.fixture
def now():
    return et("2026-11-19T10:30")


@pytest.fixture
def state(now):
    return {"account_id": "COMP123", "trd_env": "SIMULATE", "equity": 100000.0,
            "start_of_day_equity": 100000.0, "peak_equity": 100000.0, "positions": [],
            "orders_today": 0, "entries_today": 0, "consecutive_losses": 0,
            "last_check": now.isoformat()}


@pytest.fixture
def proposal(now):
    return {"symbol": "QQQ", "side": "BUY", "entry": 500.0, "stop": 497.5, "target": 505.0,
            "regime": "RISK_ON", "quote_time": now.isoformat()}


def closes(start: float, step: float, n: int = 60):
    return [start + i * step for i in range(n)]
