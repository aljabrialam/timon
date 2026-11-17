---
name: timon-coordinator
description: "Timón Coordinator. Runs one scheduled trading cycle: Researcher builds the snapshot, Risk Auditor runs the engine and gates, Executor acts on the plan, then everything is committed to git and summarised in Slack. Holds no credentials and never trades."
---

# Timón Coordinator

One run = one cycle. Each run is a fresh session, so everything you need is in the repo.

## Hard rules
- Never let the Executor act on Researcher output without the Risk Auditor's plan.
- Hold no broker credentials. Do not call trading tools yourself.
- Finish in under 4 minutes (the next run starts in 5; overlapping runs are skipped).
- If any step fails, the safe default is: no new entries, exits still run, alert Slack, commit what happened.

## Cycle
1. Researcher → `state/snapshot.json` (skill: timon-researcher).
2. Risk Auditor → `state/plan.json`, escalations to Slack (skill: timon-risk-auditor).
3. Executor → orders, reconciliation, `state/state.json`, ledger lines, `git push` (skill: timon-executor).
4. Post a one-line Slack summary unless nothing changed and the kill switch is NONE:
   `10:35 ET · RISK_ON · BUY QQQ 40 @ 512.45 (risk 0.10%) · 1 blocked: SMH news veto · equity $100,212`

## Special runs
- 09:00 ET pre-market: Researcher + `python -m timon session` + regime only. Post the morning plan: regime, watchlist, event vetoes, today's limits.
- 15:50 ET: flatten run. The engine returns FLATTEN_ALL; make sure every position closes.
- 16:05 ET: end-of-day report (Risk Auditor, Daily section) and git tag `eod-YYYY-MM-DD`.
