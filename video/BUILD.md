# Build — assemble the video after 27 Nov

Nothing here runs before the competition ends. This is the order of work for 28–29 Nov, with the exact commands, so the build is a checklist rather than a session of improvisation.

## What exists before you start

| Input | Made by | Scene |
|---|---|---|
| `video/footage/*.mov` | SHOTLIST.md rows 4–22 | 4, 5, 6 |
| `video/build/metrics.json` | `.venv/bin/python -m timon metrics --daily logs/returns.json` | 6 |
| `video/build/verify.json` | `.venv/bin/python -m timon verify` | 6 |
| `video/build/commits.txt` | `git log --pretty='%h %s'` | 4, 6 |
| `video/build/baseline.json` | the `shadow` records, summarised | 6 |

`logs/returns.json` is a bare JSON array of daily percentage returns, for example `[0.42, -0.18, 0.07]`. `metrics` takes a list, not an object, and needs at least two values before it will report a Sharpe. If there are fewer than two trading days, the caption says so instead.

```bash
.venv/bin/python -m timon metrics --daily logs/returns.json > video/build/metrics.json
.venv/bin/python -m timon verify > video/build/verify.json
git log --pretty='%h %s' > video/build/commits.txt
```

## Tools

| Need | Tool | Already installed |
|---|---|---|
| Render HTML to PNG | headless Chrome | yes |
| Cut, scale, label, concat | `ffmpeg` + `ffprobe` | yes |
| Fill the placeholders | Python 3 | yes |

No npm, no Remotion, no After Effects. Every artefact is text or a PNG, so the whole video rebuilds from the repo.

## Shape of the build

Animated scenes are **HTML pages rendered to stills**, not a video engine. One page per beat, 1920 × 1080, using `brand/tokens.css`. ffmpeg puts the beats together with short crossfades. This keeps the design language exact (the same tokens as the dashboard) and makes the whole thing reproducible: change a sentence, re-render one PNG, re-assemble.

```
video/build/
  scenes/         one .html per beat, 1920x1080
  labels/         one .png per label, baked once, reused by every footage clip
  frames/         rendered PNGs (generated)
  data.js         generated from metrics.json / verify.json / commits.txt / baseline.json
  beats.tsv       name <tab> seconds <tab> source
  render.sh       scenes/*.html -> frames/*.png
  assemble.py     beats.tsv + footage -> one ffmpeg command per segment, then concat
  fill.py         the four input files -> data.js
  timon-demo.mp4  output
```

### 1 · Placeholders

Scene pages carry no numbers. Each one has `<span data-k="sharpe"></span>`, and `data.js` fills them:

```bash
.venv/bin/python video/build/fill.py        # writes video/build/data.js
```

`fill.py` refuses to run if any placeholder remains unbound, and prints the list. A missing metric becomes the string `n/a`, which is honest and allowed on screen — every caption with a number has an `n/a` variant in SCRIPT.md.

### 2 · Labels

Six labels, baked as transparent PNGs once, at 1920 × 1080, the text sitting at 56 px from the top-left:

```
LIVE · COMPETITION ACCOUNT
REPLAY · RECORDED {date}
SIMULATED DRILL · MARKET CLOSED
DIAGRAM · {file}
2× SPEED
```

The two with `{date}` and `{file}` are rendered per clip by the assembler. The label is an overlay, never burned into footage, so the raw take stays clean.

### 3 · Still scenes

```bash
video/build/render.sh          # Chrome, 1920x1080, one PNG per scene, ~0.4 s each
```

Scenes 1, 2, 3, 7 and every caption card are stills. The motion in scene 1 (the mark drawing itself) is three stills at 300 ms each, which is enough at this scale and costs nothing to redo.

Scene 3 uses `brand/diagrams/a-architecture.png` cropped to 1920 × 1080 — the diagram is drawn at 3200 × 1800, so the crop keeps it sharp. Do not re-draw it for the video; if the diagram changes, re-render the SVG and re-crop.

### 4 · Footage

Each take is trimmed to its caption, scaled without cropping, and padded with the canvas colour if it is not exactly 1920 × 1080. Nothing is upscaled beyond 1.0×.

```bash
# trim, scale, pad, label — one segment per row of beats.tsv
ffmpeg -i video/footage/2026-11-26-drill-stale-1.mov \
  -ss 00:00:04.0 -to 00:00:14.0 \
  -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0xf2f4f8,fps=30" \
  -i video/build/labels/drill.png -filter_complex "[0:v][1:v]overlay=0:0" \
  -an -c:v libx264 -crf 18 -pix_fmt yuv420p video/build/segments/05b.mp4
```

The `2× SPEED` label is added only together with `setpts=0.5*PTS`.

### 5 · Assemble

`beats.tsv` is the edit decision list — the whole video is this file:

```
# name          seconds  source
01-title        15       still:scenes/01-title.html
02-problem      6        still:scenes/02a.html
02-problem-b    6        still:scenes/02b.html
02-problem-c    6        still:scenes/02c.html
02-problem-d    2        still:scenes/02d.html
03-arch         25       still:scenes/03-arch.html
04-cycle        10       clip:footage/2026-11-18-qca-run-1.mov@00:00:12
...
05f-flatten     8        clip:footage/2026-11-27-flatten-1.mov@00:00:03
06-evidence     30       clip:footage/2026-11-25-dashboard-1.mov@00:00:00
07-six          20       still:scenes/07-six.html
```

```bash
.venv/bin/python video/build/assemble.py     # per-segment ffmpeg, then concat
ffprobe -v error -show_entries format=duration -of csv=p=0 video/build/timon-demo.mp4
```

Rules the assembler enforces and fails on:

- total duration ≤ 3:30 (hard stop; a video over 4:00 risks being cut by a judge);
- every `clip:` segment has a label PNG;
- every segment is 1920 × 1080, 30 fps, yuv420p;
- no segment shorter than 1.8 s, so no caption flashes;
- the six safety beats together are between 50 s and 70 s.

### 6 · Sound

One quiet bed at −28 LUFS, fading out over the last 2 s, or no audio at all. No hits on cuts. If a bed is used, the loudness target is checked once:

```bash
ffmpeg -i video/build/timon-demo.mp4 -af loudnorm=print_format=json -f null - 2>&1 | tail -20
```

### 7 · The social cut

30 s, same footage, different edit: title 3 s, architecture 6 s, the stale-quote drill 5 s, evidence 8 s, six guarantees 8 s. Filled placeholders only — the social cut never carries a number the long cut does not.

```bash
video/build/timon-demo-30s.mp4   # 1920x1080, same codec settings
```

Optionally a 1080 × 1920 vertical version for a phone: re-crop the stills, re-frame the footage to the centre 9:16, keep captions inside the middle 80 %.

## Order of work

1. `fill.py` → check every placeholder resolves; if one does not, the scene is cut now, not after assembly.
2. Render stills, look at three of them at 100 % — type size and margins, not content.
3. Assemble with **every** footage segment, including the ones you expect to drop.
4. **Show the rough cut.** Whole thing, once, no commentary. Note every place the eye drifts.
5. Fix, re-assemble, check the assembler's hard rules, ship.

The rough cut is a deliverable, not a checkpoint to skip. If the safety section does not feel like the centre of the video, the edit is wrong, not the script.

## What must be true when it exports

- Duration between 3:15 and 3:30.
- Every clip labelled for its whole duration.
- Every number traceable to `video/build/*.json` or `commits.txt`.
- No live account, no password, no token, no full account number anywhere in frame.
- `ffprobe` reports H.264, yuv420p, 30 fps, 1920 × 1080, stereo or silent.
- The file plays from a clean machine with no codec pack.
