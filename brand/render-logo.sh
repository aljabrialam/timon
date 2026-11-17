#!/usr/bin/env bash
# Render brand/logo/*.svg to PNG with headless Chrome, transparent background.
# Lockups and marks at 2x; favicons at 32 and 64 px, the sizes a browser asks for.
set -euo pipefail
cd "$(dirname "$0")/.."

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT="brand/logo"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

render() { # svg, scale, css-width, css-height, output
  local svg="$1" scale="$2" w="$3" h="$4" out="$5"
  local name
  name="$(basename "$svg" .svg)"
  {
    printf '<!doctype html><meta charset="utf-8">'
    printf '<style>html,body{margin:0;padding:0;background:transparent}svg{display:block}</style>'
    cat "$svg"
  } > "$TMP/$name.html"
  "$CHROME" --headless --disable-gpu --hide-scrollbars \
    --force-device-scale-factor="$scale" --window-size="$w,$h" \
    --default-background-color=00000000 \
    --screenshot="$PWD/$out" "file://$TMP/$name.html" >/dev/null 2>&1
  printf '%s -> %s\n' "$svg" "$out"
}

for theme in light dark; do
  render "$OUT/timon-lockup-$theme.svg" 2 248 72 "$OUT/timon-lockup-$theme-2x.png"
  render "$OUT/timon-mark-$theme.svg" 2 64 64 "$OUT/timon-mark-$theme-2x.png"
  render "$OUT/timon-favicon-$theme.svg" 1 32 32 "$OUT/timon-favicon-$theme-32.png"
  render "$OUT/timon-favicon-$theme.svg" 2 32 32 "$OUT/timon-favicon-$theme-64.png"
done
