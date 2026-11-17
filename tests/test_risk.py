from timon import clock
from timon.risk import gate


def run(proposal, state, acct, limits, cal, now):
    sess = clock.session_info(now, cal, limits).to_dict()
    return gate(proposal, state, acct, limits, sess, now)


def failed(v):
    return {c.name for c in v.checks if not c.passed}


def test_stage1_escalates_valid_trade(proposal, state, acct, limits, cal, now):
    v = run(proposal, state, acct, limits, cal, now)
    assert v.verdict == "ESCALATE" and v.qty > 0


def test_stage3_approves_and_sizes_by_risk(proposal, state, acct, limits, cal, now):
    limits["autonomy"]["stage"] = 3
    v = run(proposal, state, acct, limits, cal, now)
    # 0.5% of 100k = 500 risk / 2.5 per share = 200 sh, but notional cap 20% = 40 sh -> SHRINK
    assert v.verdict == "SHRINK" and v.qty == 40
    assert "notional cap" in " ".join(v.reasons)


def test_risk_bound_when_stop_wide(proposal, state, acct, limits, cal, now):
    limits["autonomy"]["stage"] = 3
    proposal.update(entry=500.0, stop=480.0)  # 20/share -> 25 sh by risk
    v = run(proposal, state, acct, limits, cal, now)
    assert v.verdict == "APPROVE" and v.qty == 25  # risk binds: 500 / 20 = 25; gap 1500 / 60 = 25


def test_empty_account_id_blocks(proposal, state, limits, cal, now):
    v = run(proposal, state, {"competition_account_id": "", "trd_env": "SIMULATE"}, limits, cal, now)
    assert v.verdict == "BLOCK" and "account_configured" in failed(v)


def test_wrong_account_blocks(proposal, state, acct, limits, cal, now):
    state["account_id"] = "OTHER"
    assert "account_match" in failed(run(proposal, state, acct, limits, cal, now))


def test_live_env_blocks(proposal, state, acct, limits, cal, now):
    state["trd_env"] = "REAL"
    assert "simulate_env" in failed(run(proposal, state, acct, limits, cal, now))


def test_stale_quote_blocks(proposal, state, acct, limits, cal, now):
    proposal["quote_time"] = "2026-11-19T10:20:00-05:00"
    v = run(proposal, state, acct, limits, cal, now)
    assert v.verdict == "BLOCK" and "quote_fresh" in failed(v)


def test_outside_universe_blocks(proposal, state, acct, limits, cal, now):
    proposal["symbol"] = "GME"
    assert "in_universe" in failed(run(proposal, state, acct, limits, cal, now))


def test_earnings_blocks(proposal, state, acct, limits, cal, now):
    proposal["earnings_within_days"] = 0
    assert "no_earnings" in failed(run(proposal, state, acct, limits, cal, now))


def test_news_veto_blocks(proposal, state, acct, limits, cal, now):
    proposal.update(news_veto=True, news_veto_reason="CPI release 08:30")
    v = run(proposal, state, acct, limits, cal, now)
    assert v.verdict == "BLOCK" and "CPI" in " ".join(v.reasons)


def test_halted_and_disabled_block(proposal, state, acct, limits, cal, now):
    state["halted_today"] = True
    assert "not_halted_today" in failed(run(proposal, state, acct, limits, cal, now))
    state.update(halted_today=False, disabled=True)
    assert "executor_enabled" in failed(run(proposal, state, acct, limits, cal, now))


def test_duplicate_blocks(proposal, state, acct, limits, cal, now):
    state["positions"] = [{"symbol": "QQQ", "qty": 10, "market_value": 5000}]
    assert "no_duplicate" in failed(run(proposal, state, acct, limits, cal, now))


def test_entry_cap_blocks(proposal, state, acct, limits, cal, now):
    state["entries_today"] = 4
    assert "entries_per_day" in failed(run(proposal, state, acct, limits, cal, now))


def test_outside_session_blocks(proposal, state, acct, limits, cal):
    from conftest import et
    v = run(proposal, state, acct, limits, cal, et("2026-11-19T15:55"))
    assert "session_allows_entry" in failed(v)


def test_invalid_stop_side_blocks(proposal, state, acct, limits, cal, now):
    proposal["stop"] = 505.0  # stop above entry on a long
    assert "proposal_valid" in failed(run(proposal, state, acct, limits, cal, now))


def test_gross_exposure_shrinks_in_risk_off(proposal, state, acct, limits, cal, now):
    limits["autonomy"]["stage"] = 3
    proposal.update(regime="RISK_OFF", side="SELL_SHORT", entry=500.0, stop=502.5)
    state["positions"] = [{"symbol": "SPY", "qty": -40, "market_value": 25000}]
    v = run(proposal, state, acct, limits, cal, now)
    # RISK_OFF gross cap 30k, 25k used -> 5k room -> 10 sh
    assert v.qty == 10 and "gross exposure" in " ".join(v.reasons)


def test_chop_and_loss_streak_reduce_risk(proposal, state, acct, limits, cal, now):
    limits["autonomy"]["stage"] = 3
    proposal.update(regime="CHOP", entry=500.0, stop=480.0)
    state["consecutive_losses"] = 4
    v = run(proposal, state, acct, limits, cal, now)
    # 0.5% * 0.5 * 0.5 = 0.125% = 125 / 20 = 6 sh
    assert v.qty == 6 and v.verdict == "SHRINK"


def test_stage2_auto_approves_small_risk(proposal, state, acct, limits, cal, now):
    limits["autonomy"]["stage"] = 2
    proposal.update(entry=500.0, stop=480.0)  # 25 sh x 20 = 500 = 0.5% > 0.25% -> escalate
    assert run(proposal, state, acct, limits, cal, now).verdict == "ESCALATE"
    limits["sizing"]["gap_loss_cap_pct"] = 0.5  # 8 sh x 20 = 160 = 0.16%
    assert run(proposal, state, acct, limits, cal, now).verdict in ("APPROVE", "SHRINK")
