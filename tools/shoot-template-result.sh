#!/usr/bin/env bash
# Re-shoot the "What you get" images on docs/master-prompt.html.
#
# They are screenshots of a REAL scaffold, which is the point — the page shows
# the shell the system ships rather than a drawing of it. The cost is that they
# go stale silently when template/index.html changes. Run this after it does.
#
#   tools/serve.mjs must be up on 5733:  node tools/serve.mjs ../features 5733
#   then, from designmd/:                tools/shoot-template-result.sh
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
FEATURES="${1:-$HERE/../features}"
PORT="${PORT:-5733}"
OUT="$HERE/docs/assets"

CHROME=""
for c in "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
         "/Applications/Chromium.app/Contents/MacOS/Chromium" \
         google-chrome chromium chromium-browser; do
  if [ -x "$c" ] || command -v "$c" >/dev/null 2>&1; then CHROME="$c"; break; fi
done
[ -n "$CHROME" ] || { echo "✗ no headless Chrome found" >&2; exit 1; }

curl -sf -o /dev/null "http://localhost:$PORT/" \
  || { echo "✗ nothing serving on $PORT — start tools/serve.mjs first" >&2; exit 1; }

mkdir -p "$OUT"
trap 'rm -rf "$FEATURES/billing-portal" "$FEATURES/billing-portal-open"' EXIT

# The page's own worked example, scaffolded the way the prompt says to.
python3 "$HERE/tools/new-prototype.py" billing-portal \
  --title "Billing portal" --nav Initiatives --into "$FEATURES" --no-register --force >/dev/null

# 620 tall rather than a full 900: the shell is the subject, not the blank it
# leaves below the card. Shot at the final size on purpose — cropping afterwards
# with `sips --cropToHeightWidth` takes the CENTRE of the image, which quietly
# threw away the top bar and the page head.
"$CHROME" --headless --disable-gpu --hide-scrollbars \
  --window-size=1440,620 --virtual-time-budget=5000 \
  --screenshot="$OUT/template-result.png" "http://localhost:$PORT/billing-portal/" 2>/dev/null

# The off-canvas panel. Headless Chrome cannot click the hamburger, so stage a
# copy with .is-open already on the rail.
mkdir -p "$FEATURES/billing-portal-open"
sed 's|<aside class="sidenav">|<aside class="sidenav is-open">|' \
  "$FEATURES/billing-portal/index.html" > "$FEATURES/billing-portal-open/index.html"

"$CHROME" --headless --disable-gpu --hide-scrollbars \
  --window-size=420,760 --virtual-time-budget=5000 \
  --screenshot="$OUT/template-result-mobile.png" "http://localhost:$PORT/billing-portal-open/" 2>/dev/null

echo "✓ $OUT/template-result.png"
echo "✓ $OUT/template-result-mobile.png"
