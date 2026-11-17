#!/usr/bin/env bash
# Render brand/diagrams/*.svg to PNG at 2x (3200x1800) with headless Chrome.
set -euo pipefail
cd "$(dirname "$0")/.."

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT="brand/diagrams"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

for svg in "$OUT"/*.svg; do
  name="$(basename "$svg" .svg)"
  {
    printf '<!doctype html><meta charset="utf-8">'
    printf '<style>html,body{margin:0;padding:0;background:#f6f7fa}svg{display:block}</style>'
    cat "$svg"
  } > "$TMP/$name.html"
  "$CHROME" --headless --disable-gpu --hide-scrollbars \
    --force-device-scale-factor=2 --window-size=1600,900 \
    --default-background-color=00000000 \
    --screenshot="$PWD/$OUT/$name.png" "file://$TMP/$name.html" >/dev/null 2>&1
  printf '%s -> %s\n' "$svg" "$OUT/$name.png"
done
