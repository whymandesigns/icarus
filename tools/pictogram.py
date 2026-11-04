#!/usr/bin/env python3
"""Pictogram workspace tool for designmd — explore, check and approve line-art pictograms.

The skill that drives it is .claude/skills/pictogram/SKILL.md; the workspace is pictograms/.

  pictogram.py list                         names of the existing set
  pictogram.py show <name>                  print one existing pictogram's SVG
  pictogram.py board                        rebuild pictograms/index.html
  pictogram.py approve <file.svg> [--as n]  lint, then move an exploration into approved/
  pictogram.py import <figma.svg> [--out x] normalise a Figma library export for designmd
  pictogram.py lint <file.svg>...           check new drawings against the style rules
  pictogram.py sheet [file.svg...] --out x  comparison sheet: existing set + candidates

The existing set is read from designmd/example.html (#pictograms), so it never drifts.
"""
import argparse
import html
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

DEFAULT_DESIGNMD = Path(__file__).resolve().parents[1]   # designmd/
NS = "{http://www.w3.org/2000/svg}"
SIZES = (64, 128)
ALLOWED_TAGS = {"svg", "g", "path", "rect", "circle", "ellipse", "line", "polyline", "polygon"}
REQUIRED_STROKE = {
    "stroke-width": ("1", "without it .pictogram CSS renders the line at 1.5px"),
    "stroke-linecap": ("butt", ".pictogram CSS otherwise rounds the ends"),
    "stroke-linejoin": ("miter", ".pictogram CSS otherwise rounds the corners"),
    "stroke-miterlimit": ("10", "the set's corner limit"),
    "vector-effect": ("non-scaling-stroke", "keeps the line weight when shown at another size"),
}


def same(a, b):
    try:
        return float(a) == float(b)
    except (TypeError, ValueError):
        return a == b
BANNED_ATTRS = {"transform", "filter", "mask", "clip-path", "style", "class"}
MAX_DOT = 4.0  # largest solid full-opacity fill allowed (a "pg-solid" dot)


# --------------------------------------------------------------------- existing set
def existing(designmd: Path):
    src = (designmd / "example.html").read_text()
    start = src.find('id="pictograms"')
    if start < 0:
        sys.exit(f"no #pictograms section in {designmd / 'example.html'}")
    block = src[start:src.find("</section>", start)]
    found = re.findall(
        r'<span class="pictogram[^"]*">(<svg.*?</svg>)</span>\s*'
        r'<span class="pictogram-card-name">([^<]*)</span>', block, re.S)
    return {name.strip(): svg for svg, name in found}


# --------------------------------------------------------------------- path geometry
NUM = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
CMD = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]")
ARGS = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7, "Z": 0}


def _tokens(d):
    """Commands and numbers. Arc flags are single 0/1 digits and may be written
    without separators (`a10 10 0 1020 0`, as SVGO and Figma emit)."""
    i, out, cmd, argn = 0, [], None, 0
    while i < len(d):
        c = d[i]
        if c in " ,\t\n\r":
            i += 1
        elif CMD.match(c):
            out.append(c); cmd, argn = c.upper(), 0; i += 1
        elif cmd == "A" and argn % 7 in (3, 4) and c in "01":
            out.append(c); argn += 1; i += 1
        else:
            m = NUM.match(d, i)
            if not m:
                raise ValueError(f"unexpected {c!r} in path data")
            out.append(m.group()); argn += 1; i = m.end()
    return out


def _bez(pts, n=16):
    """Sample a quadratic/cubic Bezier given its control points."""
    out = []
    for k in range(1, n + 1):
        t, q = k / n, list(pts)
        while len(q) > 1:
            q = [(a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t) for a, b in zip(q, q[1:])]
        out.append(q[0])
    return out


def _arc(p0, rx, ry, phi, large, sweep, p1, n=24):
    """Sample an elliptical arc (SVG endpoint parameterisation, spec F.6.5)."""
    if p0 == p1:
        return []
    rx, ry = abs(rx), abs(ry)
    if rx == 0 or ry == 0:
        return [p1]
    cp, sp = math.cos(math.radians(phi)), math.sin(math.radians(phi))
    dx, dy = (p0[0] - p1[0]) / 2, (p0[1] - p1[1]) / 2
    x1, y1 = cp * dx + sp * dy, -sp * dx + cp * dy
    lam = x1 ** 2 / rx ** 2 + y1 ** 2 / ry ** 2
    if lam > 1:
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num = rx ** 2 * ry ** 2 - rx ** 2 * y1 ** 2 - ry ** 2 * x1 ** 2
    den = rx ** 2 * y1 ** 2 + ry ** 2 * x1 ** 2
    co = math.sqrt(max(0.0, num / den)) * (-1 if large == sweep else 1)
    cx1, cy1 = co * rx * y1 / ry, -co * ry * x1 / rx
    cx = cp * cx1 - sp * cy1 + (p0[0] + p1[0]) / 2
    cy = sp * cx1 + cp * cy1 + (p0[1] + p1[1]) / 2
    ang = lambda ux, uy: math.atan2(uy, ux)
    t1 = ang((x1 - cx1) / rx, (y1 - cy1) / ry)
    dt = ang((-x1 - cx1) / rx, (-y1 - cy1) / ry) - t1
    if sweep and dt < 0: dt += 2 * math.pi
    if not sweep and dt > 0: dt -= 2 * math.pi
    out = []
    for k in range(1, n + 1):
        t = t1 + dt * k / n
        ex, ey = rx * math.cos(t), ry * math.sin(t)
        out.append((cp * ex - sp * ey + cx, sp * ex + cp * ey + cy))
    return out


def segments(d):
    """Yield (cmd, start, end, points-on-curve) in absolute coordinates."""
    toks = _tokens(d)
    i, cmd = 0, None
    cur = start = (0.0, 0.0)
    last_ctrl = None
    while i < len(toks):
        if CMD.match(toks[i]):
            cmd = toks[i]; i += 1
            if cmd in "Zz":
                yield "Z", cur, start, [start]
                cur, last_ctrl = start, None
                continue
        if cmd is None:
            raise ValueError("path data does not start with a command")
        C, rel = cmd.upper(), cmd.islower()
        n = ARGS[C]
        try:
            v = [float(t) for t in toks[i:i + n]]
        except ValueError:
            raise ValueError(f"malformed {cmd} command")
        if len(v) < n:
            raise ValueError(f"truncated {cmd} command")
        i += n
        ox, oy = cur if rel else (0.0, 0.0)
        P = lambda k: (v[k] + ox, v[k + 1] + oy)
        ctrl = None
        if C == "H":
            end = (v[0] + (cur[0] if rel else 0), cur[1]); pts = [end]
        elif C == "V":
            end = (cur[0], v[0] + (cur[1] if rel else 0)); pts = [end]
        elif C in "ML":
            end = P(0); pts = [end]
        elif C == "C":
            ctrl, end = P(2), P(4); pts = _bez([cur, P(0), ctrl, end])
        elif C == "S":
            c1 = (2 * cur[0] - last_ctrl[0], 2 * cur[1] - last_ctrl[1]) if last_ctrl else cur
            ctrl, end = P(0), P(2); pts = _bez([cur, c1, ctrl, end])
        elif C == "Q":
            ctrl, end = P(0), P(2); pts = _bez([cur, ctrl, end])
        elif C == "T":
            ctrl = (2 * cur[0] - last_ctrl[0], 2 * cur[1] - last_ctrl[1]) if last_ctrl else cur
            end = P(0); pts = _bez([cur, ctrl, end])
        else:  # A
            end = P(5); pts = _arc(cur, v[0], v[1], v[2], bool(v[3]), bool(v[4]), end)
        yield C, cur, end, pts
        cur, last_ctrl = end, ctrl
        if C == "M":
            start = end
            cmd = "l" if rel else "L"  # implicit lineto after moveto


def bbox(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def element_geometry(el, tag):
    """(points, axis-aligned stroked segments) for one element."""
    g = lambda k, dflt=0.0: float(el.get(k, dflt))
    if tag == "path":
        pts, axis = [], []
        for C, a, b, p in segments(el.get("d", "")):
            pts += p if C == "M" else [a] + p
            if C in "LHVZ" and a != b and (a[0] == b[0] or a[1] == b[1]):
                axis.append((a, b))
        return pts, axis
    if tag == "rect":
        x, y, w, h = g("x"), g("y"), g("width"), g("height")
        c = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
        return c, [(c[k], c[(k + 1) % 4]) for k in range(4)]
    if tag in ("circle", "ellipse"):
        cx, cy = g("cx"), g("cy")
        rx = g("r") if tag == "circle" else g("rx")
        ry = g("r") if tag == "circle" else g("ry")
        return [(cx - rx, cy - ry), (cx + rx, cy + ry)], []
    if tag == "line":
        a, b = (g("x1"), g("y1")), (g("x2"), g("y2"))
        return [a, b], [(a, b)] if (a[0] == b[0] or a[1] == b[1]) else []
    if tag in ("polyline", "polygon"):
        nums = [float(n) for n in re.findall(r"-?\d*\.?\d+", el.get("points", ""))]
        p = list(zip(nums[::2], nums[1::2]))
        segs = list(zip(p, p[1:] + (p[:1] if tag == "polygon" else [])))
        return p, [s for s in segs if s[0][0] == s[1][0] or s[0][1] == s[1][1]]
    return [], []


# --------------------------------------------------------------------- lint
def lint_svg(text, label):
    errors, warnings = {}, {}
    E = lambda m: errors.__setitem__(m, errors.get(m, 0) + 1)
    W = lambda m: warnings.__setitem__(m, warnings.get(m, 0) + 1)
    if re.search(r'(?<!href=")(?<!url\()#[0-9a-fA-F]{3,8}\b|rgba?\(', text):
        E("raw colour found — use currentColor only")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        return {f"not valid XML: {e}": 1}, {}
    if root.tag not in ("svg", NS + "svg"):
        return {"root element is not <svg>": 1}, {}
    vb = (root.get("viewBox") or "").split()
    size = None
    if len(vb) == 4 and vb[:2] == ["0", "0"] and vb[2] == vb[3] and int(float(vb[2])) in SIZES:
        size = int(float(vb[2]))
    else:
        E(f'viewBox must be "0 0 64 64" or "0 0 128 128", got "{root.get("viewBox")}"')
        size = 64
    if root.get("fill", "none") != "none":
        E('<svg> must carry fill="none"')

    strokes = tints = dots = 0
    off_grid = 0
    ext = [size, size, 0, 0]
    for el in root.iter():
        tag = el.tag.replace(NS, "")
        if tag not in ALLOWED_TAGS:
            E(f"<{tag}> is not allowed (only shapes and <g>)")
            continue
        for a in BANNED_ATTRS & set(el.attrib):
            E(f"<{tag}> has {a}= — not allowed")
        if tag in ("svg", "g"):
            for a in ("stroke", "opacity", "stroke-width"):
                if a in el.attrib:
                    E(f"<{tag}> sets {a} — put it on each shape, not the group")
            continue
        stroke, fill = el.get("stroke", "none"), el.get("fill", "none")
        op_attr = "opacity" if "opacity" in el.attrib else "fill-opacity"
        opacity = el.get(op_attr)
        for a, v in (("stroke", stroke), ("fill", fill)):
            if v not in ("none", "currentColor"):
                E(f'<{tag}> {a}="{v}" — use currentColor')
        if el.get("stroke-opacity"):
            E(f"<{tag}> stroke-opacity — strokes are always full strength")
        try:
            pts, axis = element_geometry(el, tag)
        except ValueError as e:
            E(f"<{tag}> bad geometry: {e}")
            continue
        if not pts:
            continue
        x0, y0, x1, y1 = bbox(pts)
        if x0 < -0.01 or y0 < -0.01 or x1 > size + 0.01 or y1 > size + 0.01:
            E(f"<{tag}> extends outside the {size}×{size} grid ({x0:g},{y0:g} → {x1:g},{y1:g})")
        ext[0] = min(ext[0], x0); ext[1] = min(ext[1], y0)
        ext[2] = max(ext[2], x1); ext[3] = max(ext[3], y1)

        if stroke == "currentColor":
            strokes += 1
            for a, (want, why) in REQUIRED_STROKE.items():
                if not same(el.get(a), want):
                    got = f'{a}="{el.get(a)}"' if el.get(a) else "missing"
                    E(f'stroke needs {a}="{want}" ({got}) — {why}')
            if opacity is not None:
                E(f"<{tag}> has both a stroke and opacity — tints are fill-only")
            if fill == "currentColor":
                E(f"<{tag}> is filled and stroked — split into a tint and a stroke")
            for a, b in axis:
                coord = a[0] if a[0] == b[0] else a[1]
                if float(coord).is_integer():
                    off_grid += 1
        elif fill == "currentColor":
            if opacity is not None:
                if not same(opacity, "0.15"):
                    E(f'<{tag}> {op_attr}="{opacity}" — the only tint is 0.15')
                tints += 1
                if (x1 - x0) * (y1 - y0) > 0.5 * size * size:
                    W(f"<{tag}> tint covers over half the canvas — tint a base or panel, "
                      "not the whole drawing")

            else:
                w, h = x1 - x0, y1 - y0
                if w > MAX_DOT or h > MAX_DOT:
                    E(f"<{tag}> is a solid fill {w:g}×{h:g}px — looks like an expanded "
                      "outline; draw it as a 1px stroke (solid fills are dots ≤ 4px)")
                else:
                    dots += 1

    if off_grid:
        W(f"{off_grid} straight stroke segment(s) on whole-pixel coordinates — 1px lines "
          "blur across two pixels; move to .5 unless it's deliberate")
    if ext[2] > ext[0] and max(ext[2] - ext[0], ext[3] - ext[1]) < 0.9 * size:
        W(f"drawing spans {max(ext[2]-ext[0], ext[3]-ext[1]):g}px of {size} — the library "
          "fills the frame edge to edge on its long axis")
    if strokes == 0:
        E("no stroked shapes — the style is line art")
    if tints == 0:
        W("no 0.15 tint — almost every pictogram in the set has one")
    if tints > 3:
        W(f"{tints} tinted shapes — more than 3 starts to read as a fill colour")
    total = strokes + tints + dots
    lo, hi = (3, 25) if size == 64 else (3, 70)
    if not lo <= total <= hi:
        W(f"{total} shapes — the set sits around {lo}–{hi} at {size}")
    return errors, warnings


# --------------------------------------------------------------------- sheet
def grid_size(svg):
    m = re.search(r'viewBox="0 0 (\d+)', svg)
    return int(m.group(1)) if m else 64


def card(name, svg, box=64, muted=False, note=""):
    """One pictogram exactly as a prototype ships it: inside .pictogram.is-filled,
    styled by designmd's own CSS. `box` widens the span for the native-size row."""
    cls = "pictogram is-filled" + (" is-muted" if muted else "")
    style = f' style="width:{box}px;height:{box}px"' if box != 64 else ""
    return (f'<figure><div class="box"><span class="{cls}"{style}>{svg}</span></div>'
            f'<figcaption>{html.escape(name)} <i>{grid_size(svg)}</i>{note}</figcaption></figure>')


NEW = " <b>new</b>"
tag = lambda n: " <i>library ref</i>" if n.startswith("ref-") else NEW


def row(title, cards, hint=""):
    return f"<h2>{title}</h2>" + (f"<p>{hint}</p>" if hint else "") + f"<div class=row>{cards}</div>"


def group(title, items, hint="", note=tag):
    """A titled panel: as shipped, native size (only if something isn't 64), muted."""
    if not items:
        return (f'<section class="group"><h1>{html.escape(title)}</h1>'
                f'<p class="empty">{hint or "Nothing here yet."}</p></section>')
    return "".join([
        f'<section class="group"><h1>{html.escape(title)}</h1>',
        f"<p>{hint}</p>" if hint else "",
        row("As shipped", "".join(card(n, s, note=note(n)) for n, s in items)),
        row("Native size", "".join(card(n, s, grid_size(s), note=note(n)) for n, s in items))
        if any(grid_size(s) != 64 for _, s in items) else "",
        row("Muted (.is-muted)", "".join(card(n, s, muted=True) for n, s in items)),
        "</section>"])


def page(rows, out, designmd, title="Pictogram sheet"):
    css = "\n".join((designmd / f).read_text() for f in ("tokens.css", "semantic.css", "components.css"))
    Path(out).write_text(f"""<!doctype html><meta charset=utf-8><title>{html.escape(title)}</title>
<style>{css}</style>
<style>
body{{font:13px system-ui,sans-serif;margin:24px;color:#333;background:#fff}}
h2{{font-size:13px;font-weight:600;margin:28px 0 4px}}
h1{{font-size:16px;font-weight:600;margin:0}}
.lede{{font-size:13px;color:#555;margin:4px 0 0}}
.group{{margin:28px 0 8px;padding:20px;border:1px solid #dde3f5;border-radius:8px;background:#fafbff}}
.group.approved{{border-color:#b9d9c3;background:#f7fcf8}}
.group h2{{margin-top:16px}} p{{margin:0 0 10px;color:#666;font-size:12px}} p.empty{{margin:8px 0 0}}
.row{{display:flex;flex-wrap:wrap;gap:16px;align-items:flex-start}}
figure{{margin:0;text-align:center}}
figcaption{{margin-top:6px;font-size:11px;color:#555}} figcaption i{{color:#999;font-style:normal}}
.box{{padding:12px;border:1px solid #eee;border-radius:6px;line-height:0;background:#fff}}
b{{color:#204ECF;font-weight:600}}
</style>{''.join(rows)}""")
    print(f"wrote {out}")


def sheet(cands, olds, out, designmd, sections=()):
    rows = [row("Existing set, as shipped", "".join(card(n, s) for n, s in olds.items()),
                "Inside <code>.pictogram.is-filled</code> with designmd's CSS — the real 64px box.")]
    rows += [group(t, items) for t, items in sections]
    if cands:
        refs = [n for n in ("team", "archive", "success", "hierarchy", "target") if n in olds]
        rows += [
            row("Candidates, as shipped", "".join(card(n, s, note=NEW) for n, s in cands),
                "A 128 drawing is shown in the 64 box, as it would be today."),
            row("Beside references", "".join(card(n, olds[n]) for n in refs) +
                "".join(card(n, s, note=NEW) for n, s in cands),
                "Same box, same CSS. Match the density, tint amount and use of the frame — designmd's 13 are heavier (1.5px) by history; library references are the 1px style to match."),
            row("Candidates at native size", "".join(card(n, s, grid_size(s), note=NEW) for n, s in cands)),
            row("Muted (.is-muted)", "".join(card(n, s, muted=True) for n, s in cands)),
        ]
    page(rows, out, designmd)


# --------------------------------------------------------------------- workspace
WORKSPACE = DEFAULT_DESIGNMD / "pictograms"


def svgs(folder):
    return [(f.stem, f.read_text()) for f in sorted(Path(folder).glob("*.svg"))]


def board(root, designmd):
    """Rebuild <root>/index.html: approved first, then one panel per exploration
    (its ref-*.svg files shown as library refs), designmd's 13 last for context."""
    root = Path(root)
    approved = svgs(root / "approved")
    rows = [f'<h1>Pictograms</h1><p class="lede">{len(approved)} approved · '
            "explorations below · built by <code>pictogram.py board</code></p>",
            group("Approved", approved, "Linted and signed off. Prototypes take pictograms from "
                  "<code>designmd/pictograms/approved/</code>.", note=lambda n: "")
            .replace('class="group"', 'class="group approved"', 1)]
    topics = sorted(p for p in (root / "explorations").glob("*") if p.is_dir())
    for t in topics:
        items = svgs(t)
        new = [i for i in items if not i[0].startswith("ref-")]
        refs = [i for i in items if i[0].startswith("ref-")]
        notes = (t / "notes.md")
        hint = html.escape(notes.read_text().strip().splitlines()[0]) if notes.exists() else ""
        rows.append(group(f"Exploring: {t.name.replace('-', ' ')}", new + refs, hint))
    olds = existing(designmd)
    rows.append(row("designmd's 13, for context", "".join(card(n, s) for n, s in olds.items()),
                    "Heavier (1.5px) by history — match the library refs, not these."))
    page(rows, root / "index.html", designmd, "Pictograms")


def approve(src, root, designmd, name=None):
    src, root = Path(src), Path(root)
    if src.stem.startswith("ref-"):
        sys.exit(f"{src.name} is a library reference — references are context, not approvals")
    errs, warns = lint_svg(src.read_text(), src.name)
    if errs:
        print(f"FAIL  {src}")
        for e, n in errs.items():
            print(f"      error  {e}" + (f"  (×{n})" if n > 1 else ""))
        sys.exit("fix the lint errors before approving")
    dest = root / "approved" / f"{name or src.stem}.svg"
    if dest.exists():
        sys.exit(f"{dest} already exists — pass --as <new-name> or remove it first")
    dest.parent.mkdir(parents=True, exist_ok=True)
    src.rename(dest)
    print(f"approved  {src} → {dest}")
    board(root, designmd)


# --------------------------------------------------------------------- import
LIVE_STROKE = {"stroke-width": "1", "stroke-linecap": "butt", "stroke-linejoin": "miter",
               "stroke-miterlimit": "10", "vector-effect": "non-scaling-stroke"}


def import_svg(text):
    """Turn a Figma export (Blue or White variant) into designmd form: currentColor,
    no clip group or defs, no fixed size, live strokes pinned to 1px/butt/miter so the
    .pictogram CSS can't re-weight them."""
    ET.register_namespace("", NS[1:-1])
    root = ET.fromstring(text)
    for k in ("width", "height"):
        root.attrib.pop(k, None)
    root.set("fill", "none")
    # unwrap clip-path groups, drop defs
    for parent in list(root.iter()):
        for i, child in enumerate(list(parent)):
            tag = child.tag.replace(NS, "")
            if tag == "defs":
                parent.remove(child)
            elif tag == "g" and child.get("clip-path"):
                idx = list(parent).index(child)
                parent.remove(child)
                for j, gc in enumerate(list(child)):
                    parent.insert(idx + j, gc)
    for el in root.iter():
        for a in ("fill", "stroke"):
            v = el.get(a)
            if v and v != "none" and el is not root:
                el.set(a, "currentColor")
        if el.get("stroke") == "currentColor":
            for k, v in LIVE_STROKE.items():
                el.attrib.setdefault(k, v)
            el.set("stroke-width", "1")
        el.attrib.pop("clip-path", None)
    out = ET.tostring(root, encoding="unicode")
    return re.sub(r">\s+<", "><", out).strip()


# --------------------------------------------------------------------- cli
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--designmd", type=Path, default=DEFAULT_DESIGNMD)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    s = sub.add_parser("show"); s.add_argument("name")
    l = sub.add_parser("lint"); l.add_argument("files", nargs="+", type=Path)
    bd = sub.add_parser("board"); bd.add_argument("--root", type=Path, default=WORKSPACE)
    ap_ = sub.add_parser("approve"); ap_.add_argument("src", type=Path)
    ap_.add_argument("--as", dest="name"); ap_.add_argument("--root", type=Path, default=WORKSPACE)
    im = sub.add_parser("import"); im.add_argument("src", type=Path)
    im.add_argument("--out", type=Path, help="write here instead of stdout")
    sh = sub.add_parser("sheet"); sh.add_argument("files", nargs="*", type=Path)
    sh.add_argument("--out", required=True)
    sh.add_argument("--section", nargs="+", action="append", default=[], metavar=("TITLE", "FILE"),
                    help="a titled group of its own: --section 'RoB meetings' a.svg b.svg (repeatable)")
    a = ap.parse_args()

    if a.cmd == "list":
        print("\n".join(existing(a.designmd)))
    elif a.cmd == "show":
        olds = existing(a.designmd)
        if a.name not in olds:
            sys.exit(f"no pictogram '{a.name}'. Known: {', '.join(olds)}")
        print(olds[a.name])
    elif a.cmd == "lint":
        failed = False
        for f in a.files:
            errs, warns = lint_svg(f.read_text(), f.name)
            status = "FAIL" if errs else "ok"
            print(f"{status:4}  {f}")
            fmt = lambda m, n: f"{m}  (×{n})" if n > 1 else m
            for e, n in errs.items(): print(f"      error  {fmt(e, n)}")
            for w, n in warns.items(): print(f"      warn   {fmt(w, n)}")
            failed |= bool(errs)
        sys.exit(1 if failed else 0)
    elif a.cmd == "board":
        board(a.root, a.designmd)
    elif a.cmd == "approve":
        approve(a.src, a.root, a.designmd, a.name)
    elif a.cmd == "import":
        svg = import_svg(a.src.read_text())
        if a.out:
            a.out.parent.mkdir(parents=True, exist_ok=True)
            a.out.write_text(svg + "\n"); print(f"wrote {a.out}")
        else:
            print(svg)
    elif a.cmd == "sheet":
        cands = [(f.stem, f.read_text()) for f in a.files]
        secs = [(t, [(Path(f).stem, Path(f).read_text()) for f in fs]) for t, *fs in a.section]
        sheet(cands, existing(a.designmd), a.out, a.designmd, secs)


if __name__ == "__main__":
    main()
