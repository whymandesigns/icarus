#!/usr/bin/env python3
"""
Export the Icarus custom icon pack from Figma into a single inline SVG sprite.

Phase 2 of the Phosphor → Figma-icons migration. Reads the keep-list produced
during discovery (icon-export-manifest.json — 320 icons, the whole Iconography
pack minus Country Flags / Verticals / Social Media / Managed Delivery / Finance
/ Ecommerce) and writes designmd/icons.svg — a hidden <svg> sprite of
<symbol id="i-{slug}"> entries, colours normalised to currentColor so they are
theme-aware, matching the existing #i-* convention.

USAGE (needs your own Figma personal access token — it is read from the
environment and never stored):

    export FIGMA_TOKEN=figd_xxx          # https://www.figma.com/settings → Personal access tokens
    python3 designmd/tools/export_icons.py

Output: designmd/icons.svg  (+ prints any nodes Figma failed to render).
The token is only sent to api.figma.com over HTTPS; it is not written anywhere.
"""
import json, os, re, sys, time, urllib.request, urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
DESIGNMD = HERE.parent
MANIFEST = DESIGNMD / "icon-export-manifest.json"
OUT = DESIGNMD / "icons.svg"
API = "https://api.figma.com"
BATCH = 80  # Figma allows many ids per images call; keep batches modest

def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr); sys.exit(1)

def api_get(url, token):
    req = urllib.request.Request(url, headers={"X-Figma-Token": token})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def fetch_bytes(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read().decode("utf-8")

def normalise(svg, slug):
    """Turn a raw Figma SVG export into a reusable <symbol>. Returns (symbol, viewBox)."""
    # viewBox: keep the one Figma emits; fall back to 0 0 24 24
    vb = re.search(r'viewBox="([^"]+)"', svg)
    viewbox = vb.group(1) if vb else "0 0 24 24"
    # inner markup = everything between the outer <svg ...> and </svg>
    inner = re.sub(r'^.*?<svg[^>]*>', '', svg, count=1, flags=re.S)
    inner = re.sub(r'</svg>\s*$', '', inner, flags=re.S)
    # drop <defs>/clipPath (Figma often wraps in a clip that assumes fixed size)
    inner = re.sub(r'<defs>.*?</defs>', '', inner, flags=re.S)
    inner = re.sub(r'\s*clip-path="url\(#[^)]*\)"', '', inner)
    # theme-aware: any concrete fill/stroke colour -> currentColor (leave "none")
    inner = re.sub(r'(fill|stroke)="(?!none")(#[0-9a-fA-F]{3,8}|black|rgb\([^)]*\))"',
                   r'\1="currentColor"', inner)
    inner = re.sub(r'\s+', ' ', inner).strip()
    return f'<symbol id="i-{slug}" viewBox="{viewbox}">{inner}</symbol>', viewbox

def main():
    token = os.environ.get("FIGMA_TOKEN")
    if not token:
        die("Set FIGMA_TOKEN (Figma personal access token) in your environment first.")
    man = json.loads(MANIFEST.read_text())
    file_key = man["fileKey"]
    icons = man["icons"]
    print(f"Exporting {len(icons)} icons from {file_key} …")

    # 1) resolve node -> svg url in batches
    node_url = {}
    nodes = [ic["node"] for ic in icons]
    for i in range(0, len(nodes), BATCH):
        chunk = nodes[i:i+BATCH]
        q = urllib.parse.urlencode({"ids": ",".join(chunk), "format": "svg"})
        data = api_get(f"{API}/v1/images/{file_key}?{q}", token)
        if data.get("err"):
            die(f"Figma images API error: {data['err']}")
        node_url.update({k: v for k, v in (data.get("images") or {}).items() if v})
        print(f"  resolved {len(node_url)}/{len(nodes)}")
        time.sleep(0.3)

    # 2) download + normalise; collect sprite symbols + index entries
    print(f"Downloading {len(node_url)} SVGs (this is the slow part — let it finish) …")
    symbols, index, missing = [], [], []
    for n, ic in enumerate(icons, 1):
        url = node_url.get(ic["node"])
        if not url:
            missing.append(ic["slug"]); continue
        try:
            sym, viewbox = normalise(fetch_bytes(url), ic["slug"])
            symbols.append(sym)
            index.append({"slug": ic["slug"], "name": ic["name"],
                          "section": ic.get("section"), "viewBox": viewbox})
        except Exception as e:
            missing.append(f'{ic["slug"]} ({e})')
        if n % 40 == 0 or n == len(icons):
            print(f"  downloaded {n}/{len(icons)}")

    sprite = ('<svg xmlns="http://www.w3.org/2000/svg" aria-hidden="true" '
              'style="position:absolute;width:0;height:0;overflow:hidden">\n  '
              + "\n  ".join(symbols) + "\n</svg>\n")
    OUT.write_text(sprite)
    (DESIGNMD / "icons.index.json").write_text(
        json.dumps({"source": "Figma · Iconography (custom pack)", "fileKey": file_key,
                    "count": len(index), "icons": index}, indent=1) + "\n")
    print(f"\nWrote {OUT}  ({len(symbols)} symbols)")
    print(f"Wrote {DESIGNMD / 'icons.index.json'}  ({len(index)} entries)")
    if missing:
        print(f"WARNING: {len(missing)} not exported: {', '.join(missing)}")
    print("\n✅ DONE — both files written. Safe to close now.")

if __name__ == "__main__":
    main()
