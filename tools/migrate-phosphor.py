#!/usr/bin/env python3
"""migrate-phosphor.py — move a prototype off the retired Phosphor pack.

Thirteen prototypes still draw their icons as <i class="ph ph-{glyph}">. The
pack is gone and no page here loads its stylesheet any more, so every one of
those elements renders as NOTHING — a blank gap where an icon should be. This
is not drift: it is 1,078 icons missing on screen.

The replacement is the kit's own sprite:

    <i class="ph ph-trash btn-icon"></i>
    <svg class="icon btn-icon"><use href="#i-trash"/></svg>

`.icon` is sized in em (components.css), exactly as the Phosphor <i> was, so
every `font-size:` rule a page already carries keeps working untouched.

data/phosphor-map.json holds the 92 glyph decisions. Names were NOT matched by
string similarity — each candidate was rendered at 26px with the kit's own
fill:none and looked at, which is how i-brochure turned out to be the open book
and i-estimated-delivery the chequered flag.

    python3 tools/migrate-phosphor.py ../features/foo/index.html
    python3 inline.py ../features/foo/index.html     # re-bake: the sprite subset changes
    python3 lint.py   ../features/foo/index.html

CSS selectors are rewritten too: `.x .ph` -> `.x .icon`. A `.ph-{glyph}`
selector is rewritten to `.icon` and REPORTED, because the glyph name was
carrying the distinction and `.icon` cannot — if two icons share that scope,
the rule now hits both and a human has to re-aim it.
"""
import argparse, json, pathlib, re, sys, collections

HERE = pathlib.Path(__file__).resolve().parent.parent
MARK = "/* === tokens.css === */"

# <i ...>...</i> or <i ... /> carrying `ph-{glyph}` among its classes.
ICON = re.compile(
    r'<i\b([^>]*?)\bclass=(["\'])([^"\']*?)\2([^>]*?)\s*/?>(?:\s*</i>)?',
    re.S)
PH_GLYPH = re.compile(r'\bph-([\w-]+)\b')
# A selector-position `.ph` — not `.ph-foo` (handled separately) and not
# `.photo`, which \b alone would NOT protect against but (?!-) plus the word
# boundary does: `\b` fails before `o`.
SEL_PH = re.compile(r'\.ph\b(?!-)')
SEL_PH_GLYPH = re.compile(r'\.ph-([\w-]+)\b')


def style_spans(html):
    """(start, end) of every <style> block that is not the baked system."""
    return [(m.start(1), m.end(1))
            for m in re.finditer(r"<style[^>]*>(.*?)</style>", html, re.S)
            if not m.group(1)[:80].lstrip().startswith(MARK)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    m = json.loads((HERE / "data" / "phosphor-map.json").read_text())
    table = dict(m["exact"])
    table.update({k: v[0] for k, v in m["chosen"].items()})

    worst = 0
    for raw in args.paths:
        path = pathlib.Path(raw)
        html = path.read_text(errors="replace")
        used = collections.Counter()
        stranded = collections.Counter()
        css_scoped = []

        def swap(mo):
            before, _q, cls, after = mo.group(1), mo.group(2), mo.group(3), mo.group(4)
            g = PH_GLYPH.search(cls)
            if not g:
                return mo.group(0)
            glyph = g.group(1)
            if glyph not in table:
                stranded[glyph] += 1
                return mo.group(0)
            used[glyph] += 1
            # Everything that is not `ph` or `ph-*` is the page's own class and
            # has to survive — .btn-icon, .dropdown-item-check, .alert-icon.
            keep = [c for c in cls.split()
                    if c != "ph" and not c.startswith("ph-")]
            attrs = (before + after).strip()
            attrs = (" " + attrs) if attrs else ""
            return (f'<svg class="{" ".join(["icon"] + keep)}"{attrs}>'
                    f'<use href="#{table[glyph]}"/></svg>')

        new = ICON.sub(swap, html)

        # --- CSS, in the page's own <style> blocks only
        out, cursor = [], 0
        for start, end in style_spans(new):
            out.append(new[cursor:start])
            block = new[start:end]
            for mo in SEL_PH_GLYPH.finditer(block):
                ln = block.count("\n", 0, mo.start())
                line = block.split("\n")[ln].strip()
                css_scoped.append(line[:110])
            block = SEL_PH_GLYPH.sub(".icon", block)
            block = SEL_PH.sub(".icon", block)
            out.append(block)
            cursor = end
        out.append(new[cursor:])
        new = "".join(out)

        total = sum(used.values())
        print(f"\n{path}")
        if not total and not stranded:
            print("  nothing to do — no Phosphor left")
            continue
        print(f"  {total} icon(s) replaced across {len(used)} glyph(s)")
        for g, n in used.most_common():
            print(f"     ph-{g:<24} x{n:<4} → #{table[g]}")
        if css_scoped:
            print(f"  {len(css_scoped)} CSS rule(s) keyed on a GLYPH NAME, now `.icon` "
                  f"— check each still aims at one icon:")
            for line in css_scoped:
                print(f"     {line}")
        if stranded:
            worst = 1
            print(f"  {sum(stranded.values())} LEFT ALONE — not in the map:")
            for g, n in stranded.most_common():
                print(f"     ph-{g:<24} x{n}")
        if not args.dry_run and total:
            path.write_text(new)
            print("  written.")
    return worst


if __name__ == "__main__":
    sys.exit(main())
