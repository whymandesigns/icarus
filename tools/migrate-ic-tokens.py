#!/usr/bin/env python3
"""migrate-ic-tokens.py — move a frozen prototype onto the current vocabulary.

Sixteen prototypes were baked against an older token set whose names all began
`--ic-`. Their own styles still reference it, so inline.py refuses them: it
would swap the system block underneath and leave every reference unresolved.
Nothing the kit does — a breakpoint, a component, a fix — can reach them.

This is not a rename. Some roles the system deliberately re-valued, and a few
it dropped entirely; data/ic-token-map.json classifies all three cases. Only
the prototype's OWN <style> is rewritten. The baked system block is left for
inline.py, which is the next step:

    python3 tools/migrate-ic-tokens.py ../features/foo/index.html
    python3 inline.py ../features/foo/index.html
    python3 lint.py   ../features/foo/index.html
"""
import argparse, json, pathlib, re, sys, collections

HERE = pathlib.Path(__file__).resolve().parent.parent
MARK = "/* === tokens.css === */"


def own_style_spans(html):
    """(start, end) of every <style> block that is not the baked system.

    The marker has to OPEN the block, the way inline.py's own pattern requires.
    Testing `MARK in block` instead silently skipped any prototype whose own
    stylesheet merely mentions the marker in a comment — which is exactly what
    a block explaining "inline.py only rewrites the block starting with
    /* === tokens.css === */" does. Those files then under-migrated and
    inline.py went on refusing them with no sign of why.
    """
    return [(m.start(1), m.end(1))
            for m in re.finditer(r"<style[^>]*>(.*?)</style>", html, re.S)
            if not m.group(1).lstrip().startswith(MARK)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    m = json.loads((HERE / "data" / "ic-token-map.json").read_text())
    table = dict(m["same"])
    table.update({k: v[0] for k, v in m["shifts"].items()})
    shifts = set(m["shifts"])

    worst = 0
    for raw in args.paths:
        path = pathlib.Path(raw)
        html = path.read_text(errors="replace")
        spans = own_style_spans(html)

        changed = collections.Counter()
        stranded = collections.Counter()

        # A style="" attribute is markup, never the baked CSS, so it is always
        # the prototype's own and is rewritten wherever it sits. inline.py
        # counts these too, and will keep refusing the file while they remain.
        spans = sorted(spans + [(m.start(1), m.end(1)) for m in
                                re.finditer(r'style="([^"]*)"', html)
                                if "--ic-" in m.group(1)])

        out, cursor = [], 0
        for start, end in spans:
            out.append(html[cursor:start])
            block = html[start:end]

            def sub(mo):
                tok = mo.group(1)
                if tok in table:
                    changed[tok] += 1
                    return f"var({table[tok]}"
                stranded[tok] += 1
                return mo.group(0)

            out.append(re.sub(r"var\(\s*(--ic-[\w-]+)", sub, block))
            cursor = end
        out.append(html[cursor:])
        new = "".join(out)

        moved = sum(changed.values())
        print(f"\n{path}")
        if not moved and not stranded:
            print("  nothing to do — already on the current vocabulary")
            continue
        print(f"  {moved} reference(s) rewritten across {len(changed)} token(s)")
        for tok, n in changed.most_common():
            flag = "  ← VALUE CHANGES" if tok in shifts else ""
            print(f"     {tok:<26} x{n:<4} → {table[tok]}{flag}")
        if stranded:
            worst = 1
            print(f"  {sum(stranded.values())} reference(s) LEFT ALONE — no current token "
                  f"holds the role:")
            for tok, n in stranded.most_common():
                print(f"     {tok:<26} x{n}")
            print("  inline.py will keep refusing this file until these are decided.")
        if not args.dry_run and moved:
            path.write_text(new)
            print("  written.")
    return worst


if __name__ == "__main__":
    sys.exit(main())
