#!/usr/bin/env python3
"""
Upsert hand-fixed SVG icons into the sprite + index.

Use when an exported icon looks wrong and you drop a corrected .svg in (e.g.
~/Downloads/Pictos/bar-chart.svg). Each file's name (minus .svg) is the slug —
`bar-chart.svg` → `<symbol id="i-bar-chart">`. Colours are normalised to
currentColor, defs/clip-paths/sizes are stripped, and the matching <symbol> is
replaced (or inserted) in BOTH icons.svg and example.html's inline sprite, with
icons.index.json kept in sync.

    python3 tools/import_icons.py ~/Downloads/Pictos            # whole folder
    python3 tools/import_icons.py a.svg b.svg                   # specific files
"""
import sys, re, json, glob
from pathlib import Path

DM = Path(__file__).resolve().parent.parent

def normalise(svg, slug):
    vb = re.search(r'viewBox="([^"]+)"', svg)
    viewbox = vb.group(1) if vb else "0 0 24 24"
    inner = re.sub(r'^.*?<svg[^>]*>', '', svg, count=1, flags=re.S)
    inner = re.sub(r'</svg>\s*$', '', inner, flags=re.S)
    inner = re.sub(r'<defs>.*?</defs>', '', inner, flags=re.S)
    inner = re.sub(r'\s*clip-path="url\(#[^)]*\)"', '', inner)
    inner = re.sub(r'\s*id="[^"]*"', '', inner)                       # strip layer ids
    inner = re.sub(r'(fill|stroke)="(?!none")(#[0-9a-fA-F]{3,8}|black|rgb\([^)]*\))"',
                   r'\1="currentColor"', inner, flags=re.I)
    inner = re.sub(r'>\s+<', '><', inner)
    inner = re.sub(r'\s+', ' ', inner).strip()
    return f'<symbol id="i-{slug}" viewBox="{viewbox}">{inner}</symbol>', viewbox

def upsert(path, sym, slug):
    s = path.read_text()
    pat = re.compile(r'<symbol id="i-' + re.escape(slug) + r'"[^>]*>.*?</symbol>', re.S)
    if pat.search(s):
        s2 = pat.sub(lambda _: sym, s, count=1); action = "replaced"
    else:  # insert before the sprite's closing </svg> (right after its last </symbol>)
        s2, n = re.subn(r'(</symbol>)(\s*</svg>)', lambda m: m.group(1) + '\n  ' + sym + m.group(2), s, count=1)
        action = "inserted" if n else "NO SPRITE FOUND"
    path.write_text(s2)
    return action

def collect(args):
    files = []
    for a in args:
        p = Path(a).expanduser()
        files += sorted(glob.glob(str(p / '*.svg'))) if p.is_dir() else [str(p)]
    return files

def main():
    files = collect(sys.argv[1:])
    if not files:
        print("usage: import_icons.py <svg-or-dir> ..."); return
    idx = json.loads((DM / 'icons.index.json').read_text())
    by = {i['slug']: i for i in idx['icons']}
    for f in files:
        slug = Path(f).stem.lower()
        sym, vb = normalise(Path(f).read_text(), slug)
        a1 = upsert(DM / 'icons.svg', sym, slug)
        a2 = upsert(DM / 'example.html', sym, slug)
        if slug in by:
            by[slug]['viewBox'] = vb
        else:
            e = {'slug': slug, 'name': slug.replace('-', ' ').title(), 'section': 'Custom', 'viewBox': vb}
            idx['icons'].append(e); by[slug] = e
        print(f"  {slug}: icons.svg {a1} · example.html {a2}")
    idx['icons'].sort(key=lambda i: i['slug']); idx['count'] = len(idx['icons'])
    (DM / 'icons.index.json').write_text(json.dumps(idx, indent=1) + "\n")
    print(f"index count: {idx['count']}")

if __name__ == '__main__':
    main()
