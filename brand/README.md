# Timón brand

Everything here is plain SVG and CSS. No build step, no npm, no binary source files — if a file cannot be read and diffed as text, it does not belong in this folder.

```
brand/
  README.md              this file
  tokens.css             colours, type scale, verdict palette (light + dark)
  render-diagrams.sh     SVG -> PNG at 2x, via headless Chrome
  render-logo.sh         logo PNGs, transparent, at 2x / 32 / 64 px
  logo/
    timon-lockup-{light,dark}.svg      mark + wordmark, 248x72
    timon-mark-{light,dark}.svg        mark only, 64x64
    timon-favicon-{light,dark}.svg     one colour, 32x32
  diagrams/
    a-architecture.{svg,png}   the system, once
    b-cycle.{svg,png}          what happens in one run
    c-verdicts.{svg,png}       the four outcomes
    d-autonomy.{svg,png}       the three stages
    e-git.{svg,png}            git commands mapped to trading
```

PNG files are generated. Edit the SVG, run `./brand/render-diagrams.sh` or `./brand/render-logo.sh`, commit both.

## Logo

**Chosen: C, Minimal.** A (Merge) drew a branch leaving the wheel and merging back; B (Fork) split the top spoke. Both lost detail at icon sizes — A becomes a smudge, B is neither a wheel nor a fork. C keeps three spokes and three rivets, which is the least a helm needs to stay a helm. A and B live in git history, not in this folder.

The mark is a ship's wheel where the three spokes end in commit dots. The wheel is Timón; the dots are the ledger.

### Files

| Use | File | Notes |
|---|---|---|
| Horizontal lockup | `timon-lockup-{light,dark}.svg` | 248 × 72. Mark centred at 36,36; wordmark at x=76, 33 px, weight 600, tracking −0.8, accent kept on the **ó**. |
| Mark only | `timon-mark-{light,dark}.svg` | 64 × 64. Same geometry, shifted 2 units up and cropped to `viewBox="12 12 48 48"` so the ink is centred with 3 units of air. Keeps the accent hub. |
| Favicon | `timon-favicon-{light,dark}.svg` | 32 × 32, drawn on its own grid: rim, three spokes, three handles, one colour, no rivets and no hub. At 32 px the rivets merge into the rim and the hub turns the spokes into a star, so both are dropped and the handles carry the wheel reading. |

Rendered PNGs, transparent background:

| File | Pixels |
|---|---|
| `timon-lockup-{light,dark}-2x.png` | 496 × 144 |
| `timon-mark-{light,dark}-2x.png` | 128 × 128 |
| `timon-favicon-{light,dark}-32.png` | 32 × 32 |
| `timon-favicon-{light,dark}-64.png` | 64 × 64 |

The wordmark is live text, rendered through `system-ui` — SF Pro on macOS, Segoe UI on Windows, Inter where installed. Slides, the video and the GitHub README should use the PNG: a logo that reflows with the viewer's fonts is not a logo. Do not convert the wordmark to outlines; SF is not licensed for that and the PNG already solves it.

Never typeset "Timón" without the accent. Never set it in all caps. Never re-space the letters. Never put the mark inside a rounded square, circle or badge — the wheel is already round and a second ring fights it.

Clear space on every side: half the wheel radius (about 18 px at full size). Minimum sizes: lockup 96 px wide, mark 16 px, favicon 16 px.

## Palette

One accent, four verdict colours, everything else neutral. `brand/tokens.css` is the source of truth.

| Token | Light | Dark | Use |
|---|---|---|---|
| `--canvas` | `#f2f4f8` | `#14161a` | page background |
| `--card` | `#ffffff` | `#1b1e24` | cards, panels |
| `--line` | `#dfe3eb` | `#2a2e36` | hairlines, card borders |
| `--ink` | `#191b21` | `#f5f6f8` | headings, primary text |
| `--ink-2` | `#4c515c` | `#c9ced8` | body copy |
| `--muted` | `#6b707c` | `#a2a8b4` | secondary text |
| `--faint` | `#9aa0ac` | `#7c828e` | captions, annotations |
| `--accent` | `#cf5a32` | `#e07a55` | one thing per screen |
| `--accent-ink` | `#a8431f` | `#f2a184` | accent text on light |
| `--accent-soft` | `#f8e7e0` | `#3a241d` | accent tint behind text |

The accent is a position marker, not decoration. It marks the human decision point (the engine card, the risk gate, stage 3) or the single figure that matters on a slide. Two accents on one screen means neither is one.

### Verdict colours

Semantic only. They never appear as general styling, never as chart series, never as decoration.

| Verdict | Token | Light | Meaning |
|---|---|---|---|
| APPROVE | `--approve` | `#1f7a55` | trade as planned, size unchanged |
| SHRINK | `--shrink` | `#8a5a1e` | trade smaller, stop unchanged |
| ESCALATE | `--escalate` | `#2f6fb3` | no order, owner decides in Slack |
| BLOCK | `--block` | `#b0453c` | no trade, reason written to the ledger |

Each has a `-soft` tint for pills and row backgrounds. Text on a soft tint uses the solid colour, never white.

## Type

System sans first: `-apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", Inter, "Helvetica Neue", Arial, sans-serif`. Numerals are tabular wherever a figure changes between renders (dashboard, tables, ledgers). Mono is `"SF Mono", ui-monospace, Menlo, Consolas, monospace` and is reserved for identifiers: commands, paths, verdict names, tickers.

| Token | Size / line | Weight | Tracking | Slides | Dashboard | Captions |
|---|---|---|---|---|---|---|
| `--t-display` | 64 / 1.05 | 600 | −0.035em | title slide only | — | — |
| `--t-h1` | 44 / 1.1 | 600 | −0.025em | section opener | figure value | — |
| `--t-h2` | 30 / 1.2 | 600 | −0.02em | slide heading | — | — |
| `--t-h3` | 22 / 1.25 | 600 | −0.015em | sub-heading | card title | — |
| `--t-body` | 17 / 1.5 | 400 | 0 | body | — | — |
| `--t-small` | 14 / 1.45 | 400 | 0 | captions under diagrams | body | — |
| `--t-caption` | 12 / 1.35 | 400 | 0 | labels, footnotes | labels | labels only |
| `--t-mono` | 14 / 1.4 | 400 | 0 | commands | tickers, ids | — |

Dashboard overrides, because it is denser: card title 21/28, body 14/21, label 10/14, figure 44/44. The dashboard also uses a 10 px uppercase label with 0.1em tracking for section heads; that label is not part of the slide scale and does not appear on slides.

Video caption size is specified in `video/SCRIPT.md`; this table covers slides, the dashboard and still graphics only.

## Diagrams

Canvas is 1600 × 900, exported at 2x (3200 × 1800), which is legible when scaled to 1080p. Background `#f6f7fa`. Text sizes run 10.5–34 px in SVG units, so nothing falls below 14 px on a 1080p screen.

Rules that apply to every diagram:
- One accent element per diagram, and it is the decision point, not the title.
- Arrows are 1.4 px, `#8a909c`, with a small open head. Dashed lines mean a credential path, never a normal flow.
- Every diagram carries a one-line footer that states the constraint it is drawing (SIMULATE only, exits before entries, never loosen).
- No numbers unless they come from `config/` or the ledger. No placeholder figures that could be mistaken for results.
- If a diagram needs a legend longer than one line, the diagram is wrong.

To regenerate:

```bash
./brand/render-diagrams.sh
```

## Never

No gradients. No glows, bloom or blur. No drop shadows beyond a 1 px border. No stock imagery, no robots, no neural-network illustrations, no glowing nodes. No emoji. No second accent. No coloured text on coloured fills. No all-caps body copy. No invented numbers, ever — if a figure is unknown, the slide says so or leaves the space empty.
