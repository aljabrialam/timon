# Shot list — everything to capture, 18–27 November

One row is one recording. If a row cannot be recorded, the scene it feeds is cut — the video never substitutes something else and keeps the caption.

## Before the first recording

| Check | How |
|---|---|
| Competition account is configured | `config/account.yaml` has a non-empty `competition_account_id`, and `state/state.json` carries the same id |
| The engine accepts an order | a drill run reports `account_match: passed` — if it fails, no live footage exists yet and scene 4 cannot be shot |
| Screen resolution | 1920 × 1080 minimum, menu bar hidden, notifications off, one window per take |
| Terminal | SF Mono or Menlo 16 px, light background, 70 % opacity, no transparency |
| Dashboard | light theme at 1440 px wide, browser chrome hidden |
| File names | `video/footage/YYYY-MM-DD-<scene>-<n>.mov`, one take each, never re-encoded |
| Labels | every clip starts with its label already visible; the label is part of the take, not added later |

Two things are not implemented yet and must not appear in any clip:

- the Slack bot answers `hello` and `status` only — there is no order-approval path, so no clip may show an approval button;
- the account guard refuses every order while `competition_account_id` is empty.

## 17 Nov (today) — local, nothing live

| # | What to show | Exact command | Label | File |
|---|---|---|---|---|
| 1 | Ledger verifies on an empty ledger | `.venv/bin/python -m timon verify` | `LOCAL · NO TRADES YET` | `2026-11-17-verify-1.mov` |
| 2 | Dashboard, empty state | `.venv/bin/python scripts/export_dashboard.py` then open `https://timon-theta.vercel.app` | `REPLAY · RECORDED 17 NOV` | `2026-11-17-dashboard-empty-1.mov` |
| 3 | Session check, pre-market | `.venv/bin/python -m timon session --now 2026-11-17T13:00:00+00:00` | `LOCAL · 17 NOV` | `2026-11-17-session-1.mov` |

These three are optional B-roll. They show the system is honest about having no trades, which is worth 4 s in scene 6 if the live scenes fall through.

## 18–20 Nov — stage 1, every order needs a human

Record after the US close, from the day's artefacts, so the take cannot be interrupted by a live cycle.

| # | What to show | Exact command or message | Label | File |
|---|---|---|---|---|
| 4 | The day's QCA run, start to finish | QCA console → the day's session → playback at 2× | `LIVE · COMPETITION ACCOUNT` + `2× SPEED` | `2026-11-18-qca-run-1.mov` |
| 5 | The plan the run produced | `python3 -m json.tool state/plan.json` | `LIVE · COMPETITION ACCOUNT` | `2026-11-18-plan-1.mov` |
| 6 | Slack status reply | in `#timon-test`: `@Timon status` | `LIVE · COMPETITION ACCOUNT` | `2026-11-18-slack-status-1.mov` |
| 7 | The run's commit | `git log --oneline -3` then `git show --stat HEAD` | `LIVE · COMPETITION ACCOUNT` | `2026-11-18-commit-1.mov` |
| 8 | Ledger grows, still verifies | `.venv/bin/python -m timon verify` | `LIVE · COMPETITION ACCOUNT` | `2026-11-18-verify-1.mov` |

Repeat 4–8 on 19 and 20 Nov; keep the best take of each. Three days is enough — the video uses one.

## 23–24 Nov — stage 2, small orders without asking

| # | What to show | Exact command or message | Label | File |
|---|---|---|---|---|
| 9 | The first order placed without a human | QCA session playback, stopping on the executor step | `LIVE · COMPETITION ACCOUNT` + `2× SPEED` | `2026-11-23-first-auto-1.mov` |
| 10 | The verdict that allowed it | `python3 -m json.tool state/plan.json` — the `verdicts` block, `"verdict": "APPROVE"` and the risk figure | `LIVE · COMPETITION ACCOUNT` | `2026-11-23-verdict-1.mov` |
| 11 | A fill in the ledger | `.venv/bin/python -m timon log` is *not* used here — read the ledger instead: `tail -n 5 logs/decisions.jsonl` | `LIVE · COMPETITION ACCOUNT` | `2026-11-23-ledger-1.mov` |

## 25–27 Nov — stage 3, unattended inside the limits

| # | What to show | Exact command or message | Label | File |
|---|---|---|---|---|
| 12 | An unattended cycle, no human in it | QCA session playback at 2× | `LIVE · COMPETITION ACCOUNT` + `2× SPEED` | `2026-11-25-unattended-1.mov` |
| 13 | The dashboard after a few sessions | `.venv/bin/python scripts/export_dashboard.py`, then the live URL, scrolled top to bottom | `REPLAY · RECORDED 25 NOV` | `2026-11-25-dashboard-1.mov` |
| 14 | Metrics for the evidence scene | `.venv/bin/python -m timon metrics --daily logs/returns.json` | `LIVE · COMPETITION ACCOUNT` | `2026-11-25-metrics-1.mov` |
| 15 | Final flatten, 12:45 ET, 27 Nov | watch the 12:45 ET cycle in QCA; then `@Timon status` in `#timon-test`; then `git log --oneline -2` | `LIVE · COMPETITION ACCOUNT · 27 NOV` | `2026-11-27-flatten-1.mov` |
| 16 | Regular close, 13:00 ET | the session check after the bell: `.venv/bin/python -m timon session --now 2026-11-27T18:05:00+00:00` | `LIVE · COMPETITION ACCOUNT · 27 NOV` | `2026-11-27-close-1.mov` |

Rows 12–16 are the only live footage of stage 3. If the account is still blocked, rows 4–16 do not exist; scenes 4 and 5f are cut and the video becomes a 2:30 cut of scenes 1–3, 5a–5e and 6–7.

## 26 Nov — market closed, every safety drill

All five drills run the real engine on a hand-written snapshot. The runner prints its own drill banner to stderr, so the console line in the clip already says it is a drill.

`drill.py` imports the engine's own `plan.build` instead of calling `python -m timon plan`, for two reasons that both matter on camera: `python -m timon plan` deliberately refuses to size an order while `competition_account_id` is empty, and a drill must never append its verdicts to `logs/decisions.jsonl`. The runner passes a drill account id (`DRILL-0000`) and writes nothing. `examples/snapshot.json` remains the schema reference the researcher builds against.

| # | What to show | Exact command | Label | File |
|---|---|---|---|---|
| 17 | Drawdown kill switch | `.venv/bin/python video/drill/drill.py flatten` | `SIMULATED DRILL · MARKET CLOSED` | `2026-11-26-drill-flatten-1.mov` |
| 18 | Stale quote blocked | `.venv/bin/python video/drill/drill.py stale` | `SIMULATED DRILL · MARKET CLOSED` | `2026-11-26-drill-stale-1.mov` |
| 19 | Stop checked, exits before entries | `.venv/bin/python video/drill/drill.py stop` | `SIMULATED DRILL · MARKET CLOSED` | `2026-11-26-drill-stop-1.mov` |
| 20 | Daily halt | `.venv/bin/python video/drill/drill.py halt` | `SIMULATED DRILL · MARKET CLOSED` | `2026-11-26-drill-halt-1.mov` |
| 21 | Stage 1 escalates, stage 3 approves — same snapshot | `.venv/bin/python video/drill/drill.py approve` then `.venv/bin/python video/drill/drill.py approve --stage 3` | `SIMULATED DRILL · MARKET CLOSED` | `2026-11-26-drill-autonomy-1.mov` |
| 22 | The input behind the drills, for one honest second | `.venv/bin/python video/drill/drill.py approve --input \| head -30` | `SIMULATED DRILL · MARKET CLOSED` | `2026-11-26-drill-input-1.mov` |

Each take: scroll slowly enough to read, stop on the field the caption names, and hold for two seconds before stopping the recorder.

The exact fields each caption points at:

| Drill | Stop on |
|---|---|
| `flatten` | `"action": "FLATTEN_AND_DISABLE"` and the two `exits` |
| `stale` | the SPY verdict `"verdict": "BLOCK"` and `"quote_fresh"` in the failing checks |
| `stop` | `"reason": "stop hit: ..."` in `exits`, then the `orders` block below it |
| `halt` | `"action": "HALT_NEW"` and `"note": "no new entries: ..."` |
| `approve` | `"verdict": "ESCALATE"` at stage 1, then `"verdict": "APPROVE"` with `--stage 3` |

## 27–29 Nov — build inputs, not footage

| # | What | Command |
|---|---|---|
| 23 | Final metrics for the placeholders | `.venv/bin/python -m timon metrics --daily logs/returns.json > video/build/metrics.json` |
| 24 | Ledger line count for `{entries}` | `.venv/bin/python -m timon verify > video/build/verify.json` |
| 25 | Commit list for `{commits}` | `git log --pretty='%h %s' > video/build/commits.txt` |
| 26 | Baseline comparison for scene 6 | the `shadow` records in `logs/decisions.jsonl`, summarised into `video/build/baseline.json` |

## Editorial rules

- **Never trim a label off.** If the label is in the first frames and the cut removes it, re-take.
- **Never speed a clip without the `2× SPEED` label.** Applies to QCA playback and to the dashboard scroll.
- **Never show a figure that is not in `video/build/`.** If it is not in one of those files, the caption says the number is unavailable.
- **Never show tokens, account passwords, the vault, or the full account number.** Crop the account id to its last four digits.
- **One take per row.** Re-takes get a new number; the best take is chosen at assembly, and the rest are kept.
