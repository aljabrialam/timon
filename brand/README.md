# Timón brand

Everything here is plain SVG and CSS. No build step, no npm, no binary source files — if a file cannot be read and diffed as text, it does not belong in this folder.

```
brand/
  README.md              this file
  tokens.css             colours, type scale, verdict palette (light + dark)
  render-diagrams.sh     SVG -> PNG at 2x, via headless Chrome
  logo/
    option-a-hairline-{light,dark}.svg    "Merge"
    option-b-anchor-{light,dark}.svg      "Fork"
    option-c-signal-{light,dark}.svg      "Minimal"
    options-preview.html / .png           the three side by side
  diagrams/
    a-architecture.{svg,png}   the system, once
    b-cycle.{svg,png}          what happens in one run
    c-verdicts.{svg,png}       the four outcomes
    d-autonomy.{svg,png}       the three stages
    e-git.{svg,png}            git commands mapped to trading
```

PNG files are generated. Edit the SVG, run `./brand/render-diagrams.sh`, commit both.

## Logo

**Status: three options, waiting for the pick.** Nothing is finalised until one is chosen — no favicon, no social card, no deck header, no README lockup.

All three start from the same idea: a ship's wheel where part of the wheel is a git graph. The wheel is Timón (the helm); the branch and the commit dots are the ledger. They differ only in how much git they show.

| Option | File prefix | Idea | Reads at 32 px |
|---|---|---|---|
| A | `option-a-hairline` | Merge: three spokes, three rim dots, one branch that leaves the wheel and merges back | busy |
| B | `option-b-anchor` | Fork: the top spoke splits into two branch ends | ok |
| C | `option-c-signal` | Minimal: three spokes, three rim dots, no outside branch | best |

The recommendation is **C**. It keeps the metaphor of a wheel with commit dots at the rim, and at 32 px it is still three strokes and three dots rather than a smudge. A is the most literal git drawing and the weakest icon; B sits between them.

### Lockups

| Use | How |
|---|---|
| Horizontal lockup | The full SVG as drawn: mark at 36,36, wordmark starting at x=76. Wordmark is 33 px, weight 600, tracking −0.8, and keeps the accent on the **ó**. |
| Mark only | Same file, `viewBox="0 0 72 72"`. Do not redraw the mark on its own grid. |
| Favicon | The mark, square, 32 px. One colour only: ink on light, white on dark. No accent hub at this size. |

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
