# Demo video — script

**Length 3:30. 1920 × 1080 at 30 fps.** Seven scenes. Every clip carries a label that says what it is.

## Rules

1. **Every number in this script is a `{placeholder}`.** Nothing here is a result. The final build fills them from `logs/decisions.jsonl` and `python -m timon metrics`, or the line is cut.
2. **Every clip is labelled**, top-left, for its whole duration:

   | Label | Means |
   |---|---|
   | `LIVE · COMPETITION ACCOUNT` | recorded during a real paper-trading session |
   | `REPLAY · RECORDED {date}` | recorded earlier, played back unchanged |
   | `SIMULATED DRILL · MARKET CLOSED` | the engine run on a hand-written snapshot, 26 Nov |
   | `DIAGRAM · {file}` | drawn, not filmed |
   | `2× SPEED` | added to any clip that is sped up |

   A clip with no label is a bug. If footage for a scene does not exist by 27 Nov, the scene is cut and the runtime is re-timed — never filled with something that looks live but is not.
3. **Burned-in captions**: one line, bottom centre, 34 px SF Pro Text / Inter Medium, white on `rgba(20,22,26,0.82)`, 16 px radius, 96 px from the bottom edge, 120 px from either side. Maximum 46 characters. No caption lasts under 1.8 s. No two captions stack.
4. **No music with a beat you can cut to.** One quiet bed at −28 LUFS or nothing. No whooshes, no clicks, no typing sounds.
5. **No stock footage, no AI b-roll, no logos of anything except Moomoo and Qoder where they appear in a real screenshot.**

Timeline:

| Time | Scene | Length |
|---|---|---|
| 0:00 | 1. Title | 0:15 |
| 0:15 | 2. Problem | 0:20 |
| 0:35 | 3. Architecture | 0:25 |
| 1:00 | 4. One live cycle | 0:40 |
| 1:40 | 5. Safety | 1:00 |
| 2:40 | 6. Evidence | 0:30 |
| 3:10 | 7. Reuse and six guarantees | 0:20 |

Safety is 60 s of 210 s — a little over a quarter of the runtime, and the longest single scene. That is the point of the video.

---

## 1 · Title — 0:00 to 0:15

**Picture.** Light canvas `#f2f4f8`. The wheel mark draws itself over 900 ms (three strokes, then three rim dots, then the accent hub). Wordmark fades in. Nothing else moves. At 0:12 a hairline appears under the wordmark with one line of text.

**Label.** none.

**Captions**

| In | Out | Caption |
|---|---|---|
| 0:02 | 0:07 | Timón — the helm, not the oracle |
| 0:07 | 0:12 | An AI trading team that shows its work |
| 0:12 | 0:15 | Paper trading only. Results at the end. |

**Note.** "Paper trading only" appears at 0:12 on purpose: the first claim in the video is a limit, not a promise.

---

## 2 · Problem — 0:15 to 0:35

**Picture.** Three statements type on, one at a time, left-aligned on the canvas. No icons, no illustrations. The third is set in the accent.

**Label.** `DIAGRAM · video/build/scene-problem`

**Captions** (these are also the on-screen statements, one per beat)

| In | Out | Caption |
|---|---|---|
| 0:16 | 0:21 | Most trading agents hide the decision |
| 0:21 | 0:27 | They agree with each other, then buy |
| 0:27 | 0:33 | Agreement is not evidence |
| 0:33 | 0:35 | So the decisions here are made in Python |

**Note.** Beats 1–3 are the failure the judges named in the brief. Beat 4 is the response, and it hands straight to the architecture.

---

## 3 · Architecture — 0:35 to 1:00

**Picture.** `brand/diagrams/a-architecture` animates in four groups: the QCA panel, the row of agents, the Moomoo column, then the bottom band. Arrows draw in the order a cycle runs. The engine card is the only accent; it pulses once at 0:52.

**Label.** `DIAGRAM · brand/diagrams/a-architecture`

**Captions**

| In | Out | Caption |
|---|---|---|
| 0:36 | 0:42 | One schedule, four agents, one engine |
| 0:42 | 0:48 | The engine sizes, gates and writes the plan |
| 0:48 | 0:53 | Agents read data and place what it approved |
| 0:53 | 0:58 | The vault holds one credential: Moomoo MCP |
| 0:58 | 1:00 | Nothing here can reach a live account |

---

## 4 · One live cycle — 1:00 to 1:40

**Picture.** Three panels, cut between them, never split-screen:
1. the QCA session for one run, sped to 2× — the coordinator handing off, researcher writing `state/snapshot.json`, engine output scrolling;
2. Slack: `@Timon status` and the reply — session, kill switch, ledger integrity;
3. a terminal: `verify`, then `git log --oneline -3`.

**Label.** `LIVE · COMPETITION ACCOUNT` + `2× SPEED` for panel 1. If the account is still not trading on the day this is built, the panel is replaced by `REPLAY · RECORDED {date}` footage of the same three panels, or the scene is cut.

**Captions**

| In | Out | Caption |
|---|---|---|
| 1:01 | 1:06 | One cycle, from schedule to commit |
| 1:06 | 1:12 | Researcher reads. It never places an order |
| 1:12 | 1:18 | Engine turns the snapshot into a plan |
| 1:18 | 1:24 | Auditor may tighten a verdict, never loosen |
| 1:24 | 1:30 | Executor acts on the plan, in SIMULATE only |
| 1:30 | 1:36 | Then: ledger line, commit, push |
| 1:36 | 1:40 | The dashboard reads the repo, not the broker |

**Note.** The clip must show a real run of the real system. A run on a drill snapshot belongs in scene 5, labelled as a drill.

---

## 5 · Safety — 1:40 to 2:40

Six beats, about 10 s each. All recorded on **26 Nov** (market closed) as labelled drills, except the last beat, which is captured live on **27 Nov**.

### 5a · Kill switch: drawdown — 1:40 to 1:50

**Picture.** Terminal. `.venv/bin/python video/drill/drill.py flatten`. The JSON scrolls to `kill.action: FLATTEN_AND_DISABLE` and two exit intents, one per open position.

**Label.** `SIMULATED DRILL · MARKET CLOSED`

**Captions**

| In | Out | Caption |
|---|---|---|
| 1:41 | 1:45 | Equity −{drawdown}% from the peak |
| 1:45 | 1:50 | Flatten everything, disable new orders |

### 5b · Stale quote — 1:50 to 2:00

**Picture.** `.venv/bin/python video/drill/drill.py stale`. Scroll to the SPY verdict: `BLOCK`, and the failing check `quote_fresh`.

**Label.** `SIMULATED DRILL · MARKET CLOSED`

**Captions**

| In | Out | Caption |
|---|---|---|
| 1:51 | 1:55 | The quote is {age} seconds old |
| 1:55 | 2:00 | The gate refuses to size it. No order. |

### 5c · Stops are checked, not resting — 2:00 to 2:10

**Picture.** `.venv/bin/python video/drill/drill.py stop`. Scroll to `exits`: QQQ through its stop, and the entry that came after it in the same plan.

**Label.** `SIMULATED DRILL · MARKET CLOSED`

**Captions**

| In | Out | Caption |
|---|---|---|
| 2:01 | 2:05 | The paper API has no resting stop orders |
| 2:05 | 2:10 | So every cycle checks, and exits come first |

### 5d · Daily halt — 2:10 to 2:20

**Picture.** `.venv/bin/python video/drill/drill.py halt`. `kill.action: HALT_NEW`, note "no new entries", zero verdicts.

**Label.** `SIMULATED DRILL · MARKET CLOSED`

**Captions**

| In | Out | Caption |
|---|---|---|
| 2:11 | 2:15 | The day is down past the halt line |
| 2:15 | 2:20 | No new entries. Exits still run. |

### 5e · Earned autonomy — 2:20 to 2:32

**Picture.** Two terminal runs in sequence, same snapshot: stage 1 → `ESCALATE`, then `--stage 3` → `APPROVE`. Scroll to the `reasons` line: "autonomy stage 1: every order needs approval". Then a Slack `@Timon status` reply, to show the channel in use — not an approval, because the bot has no order path yet.

**Label.** `SIMULATED DRILL · MARKET CLOSED` (both runs; the stage-3 line is a config override, and the caption says so)

**Captions**

| In | Out | Caption |
|---|---|---|
| 2:21 | 2:26 | Stage 1: every sized order waits for a human |
| 2:26 | 2:32 | The same snapshot later: {stage} trades alone |

### 5f · Flat by the bell — 2:32 to 2:40

**Picture.** 27 Nov, live: the last cycle before the hard flatten at 12:45 ET. Slack shows the flatten and the run's commit.

**Label.** `LIVE · COMPETITION ACCOUNT · 27 NOV`

**Captions**

| In | Out | Caption |
|---|---|---|
| 2:33 | 2:38 | {flatten_et} ET: everything is flat, on purpose |
| 2:38 | 2:40 | Nothing is carried overnight |

---

## 6 · Evidence — 2:40 to 3:10

**Picture.** No talking heads. Screen only, in this order:
1. `https://timon-theta.vercel.app` scrolled top to bottom at 1.2× — figures, curve, verdicts, limits;
2. terminal: `python -m timon verify` → `"ok": true, "entries": {n}`;
3. terminal: `python -m timon metrics --daily logs/returns.json`;
4. `git log --oneline -8` — one line per cycle.

**Label.** `REPLAY · RECORDED {date}` for the dashboard; `LIVE · COMPETITION ACCOUNT` for the terminal if it is the same session as 4.

**Captions**

| In | Out | Caption |
|---|---|---|
| 2:41 | 2:46 | {cycles} cycles, {orders} orders, all logged |
| 2:46 | 2:51 | {trades} trades. Win rate {win_rate}%. |
| 2:51 | 2:56 | Expectancy {expectancy} per trade |
| 2:56 | 3:01 | Sharpe {sharpe} against {benchmark} |
| 3:01 | 3:06 | The ledger verifies: {entries} entries, unbroken |
| 3:06 | 3:10 | Every figure here is reproducible from the repo |

**Note.** If a metric is null or missing, the caption is replaced by `Not enough trades to report — {reason}`. A video that admits this scores better than one that hides it.

---

## 7 · Reuse and six guarantees — 3:10 to 3:30

**Picture.** Repo tree scrolls once (about 2 s), then the six guarantees appear as a list, one per 1.4 s, each with a two-word label in the accent. No checkmarks. No badges.

**Label.** `REPO · github.com/aljabrialam/timon`

**The six guarantees** (on screen, then read as captions)

| # | On screen | Caption |
|---|---|---|
| 1 | SIMULATE only | The account is checked before every order |
| 2 | Flat every day | Nothing survives the close |
| 3 | Engine decides | Sizing and verdicts are Python with tests |
| 4 | Stops checked each cycle | The paper API has no resting stops |
| 5 | Fail closed | Missing or stale data means no trade |
| 6 | Every decision committed | The ledger is hash-chained |

**Closing caption** (2 s, black card, white text):

> {cycles} cycles. {trades} trades. One ledger anyone can check.

Then the repo URL for 2 s and out. No logo animation at the end; the mark is already the first frame.

---

## What this video does not claim

- It does not claim a live brokerage account. The Moomoo account is paper (SIMULATE), and the video says so in the first 15 s and again at 2:38.
- It does not claim returns that are not in the ledger. Every figure is either a placeholder filled from the repo, or the caption says the number is not available.
- It does not present a drill as a live run. The drill scenes are on 26 Nov, market closed, with the label on screen for the whole clip.
- It does not claim the agents decide. The engine decides; the video says so at 0:33 and 1:12.
