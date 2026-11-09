#!/usr/bin/env python3
"""sync-picasso-tokens.py — keep tokens.css honest about what it takes from Picasso.

tokens.css is two files wearing one coat. Most of it is transcribed from
Picasso — the gray ramp, the spacing scale, the radii, shadows 0-5, the type
scale — and the rest is Operationalize's own, because Picasso is Toptal's
company system and will never ship an Operationalize side nav or top bar.
Every line already says which it is:

    --color-gray-50: #FCFCFC;         /* picasso */
    --color-gray-700: #5F636A;        /* extension */

Only the first kind can drift, and it drifts silently: Picasso ships a new
value, nobody re-transcribes it, and a prototype quietly renders a colour the
product stopped using months ago. That is what happened to gray-100.

Picasso publishes those values as a Tailwind preset on public npm, so they
never had to be copied by hand in the first place. This compares the two and,
with --fix, rewrites the ones that disagree. It changes nothing else: the
/* extension */ lines, the commented-out ramps and all the prose around them
are left byte-for-byte alone, because they have no upstream to be wrong about.

    python3 tools/sync-picasso-tokens.py            # report
    python3 tools/sync-picasso-tokens.py --check    # exit 1 if anything drifted
    python3 tools/sync-picasso-tokens.py --fix      # rewrite drifted values
    python3 tools/sync-picasso-tokens.py --update   # re-vendor from npm

The vendored copy is data/picasso-tokens.json, so the day-to-day run needs no
network and no node_modules — this repo has neither a package.json nor an npm
install step, and adding one to check 41 numbers would cost more than it saves.
--update is the only command that reaches out, and it records the version it
took, so a bump is a reviewable diff rather than a silent change.

Four things it reports:

    drift        tagged /* picasso */, value disagrees          --fix rewrites
    unverified   tagged /* picasso */, this preset has no such    report only
    extended     tagged /* picasso + ... */, deliberately ours    informational
    missing      this preset publishes it, tokens.css has none    report only

Only drift fails --check. "unverified" is not an accusation: Picasso is several
packages and this one carries the Tailwind theme, so z-indices, input metrics
and the grid widths are real Picasso values from elsewhere in it that simply
cannot be checked from here. Adding a missing token is a design decision, not a
sync, so it is never done for you either.
"""

import argparse
import json
import pathlib
import re
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
TOKENS_CSS = ROOT / "tokens.css"
VENDORED = ROOT / "data" / "picasso-tokens.json"

PACKAGE = "@toptal/picasso-tailwind"

# Published by the preset and deliberately absent from tokens.css. Each one is
# argued in a comment there; this repeats the reason so the report stays short
# and the decision stays visible instead of being rediscovered every run.
DELIBERATE_OMISSIONS = dict(
    [("shadow-%d" % n,
      "Material UI v4 elevation; Picasso's own source marks 6-24 for deprecation")
     for n in range(6, 25)]
    + [("font-weight-thin",
        "Proxima ships no 100 face, so a browser would synthesise it"),
       ("font-weight-light",
        "Proxima ships no 300 face, so a browser would synthesise it")]
)

# Where each group of the preset's `theme` lands in tokens.css. A group absent
# from here is one designmd expresses some other way — `screens`, for one,
# lives in the media queries of components.css rather than as a token.
GROUPS = [
    ("colors", "color-"),
    ("spacing", "spacing-"),
    ("borderRadius", "radius-"),
    ("boxShadow", "shadow-"),
    ("fontSize", "text-"),
    ("fontWeight", "font-weight-"),
    ("screens", "breakpoint-"),
    ("borderWidth", "border-width-"),
]

# A line's trailing comment decides how it is treated.
#   /* picasso */        or  /* picasso - 14px, default body */   → checked
#   /* picasso + ... */                                           → extended
#   /* extension */                                               → ignored
DECL = re.compile(
    r"^(?P<indent>\s*)--(?P<name>[\w-]+)\s*:\s*(?P<value>[^;]+);"
    r"(?P<gap>\s*)(?P<comment>/\*.*)?$"
)
PICASSO_TAG = re.compile(
    r"^/\*\s*picasso\s*(?P<mod>[-+])?\s*(?P<note>.*?)\s*(?:\*/)?\s*$")


# ----------------------------------------------------------------- the preset

def _block(src, key, start=0):
    """The {...} body following `key:`, brace-matched so nesting survives."""
    i = src.find(key + ": {", start)
    if i < 0:
        return None
    i = src.index("{", i)
    depth, j = 0, i
    while j < len(src):
        if src[j] == "{":
            depth += 1
        elif src[j] == "}":
            depth -= 1
            if depth == 0:
                return src[i + 1:j]
        j += 1
    return None


def _entries(block, indent=6):
    """`key: 'value'` pairs at exactly this depth, skipping nested blocks.

    The depth matters: `colors` holds flat entries at six spaces and whole
    ramps at six whose shades sit at eight, so a looser match reads
    `blue: { 100: '#EDF1FD' }` as a top-level colour called `100`.
    """
    out = []
    pattern = r"^ {%d}'?([\w.-]+)'?\s*:\s*(.+?),?\s*$" % indent
    for m in re.finditer(pattern, block, re.M):
        key, raw = m.group(1), m.group(2).strip().rstrip(",")
        if raw.startswith("{"):
            continue
        if raw.startswith("["):
            # fontSize: ['0.875rem', { lineHeight: '1.375rem' }] — take the size
            first = re.match(r"\[\s*'([^']+)'", raw)
            if first:
                out.append((key, first.group(1)))
            continue
        lit = re.match(r"'([^']*)'$", raw)
        if lit:
            out.append((key, lit.group(1)))
    return out


def parse_preset(src):
    """The preset's theme, flattened to designmd's token names."""
    theme = _block(src, "theme")
    if theme is None:
        raise SystemExit("could not find `theme` in the preset")

    tokens = {}
    for key, prefix in GROUPS:
        block = _block(theme, key)
        if block is None:
            continue
        if key == "colors":
            # Two shapes side by side: flat (white) and ramps (blue: { 500: … }).
            for name, value in _entries(block, indent=6):
                if value.startswith("#"):
                    tokens[prefix + name] = value
            for m in re.finditer(r"^ {6}(\w+): \{$", block, re.M):
                hue = m.group(1)
                ramp = _block(block, hue, m.start())
                if ramp is None:
                    continue
                for shade, value in _entries(ramp, indent=8):
                    tokens["%s%s-%s" % (prefix, hue, shade)] = value
        else:
            for name, value in _entries(block, indent=6):
                # Tailwind's DEFAULT is the bare token: borderWidth.DEFAULT is
                # --border-width, not --border-width-DEFAULT.
                token = prefix.rstrip("-") if name == "DEFAULT" else prefix + name
                tokens[token] = value

        if key == "fontSize":
            # fontSize: { md: ['0.875rem', { lineHeight: '1.375rem' }] } — the
            # second half is a token of its own in tokens.css.
            for m in re.finditer(
                    r"^ {6}'?([\w-]+)'?: \[\s*'[^']+',\s*\{\s*lineHeight: '([^']+)'",
                    block, re.M):
                tokens["text-%s--line-height" % m.group(1)] = m.group(2)

    family = _block(theme, "fontFamily")
    if family:
        for stack_name in ("sans", "mono"):
            m = re.search(r"%s:\s*\[(.*?)\]" % stack_name, family, re.S)
            if not m:
                continue
            # tokens.css quotes only the names that need it, as CSS requires.
            parts = [p if re.match(r"^[\w-]+$", p) else "'%s'" % p
                     for p in re.findall(r"'([^']+)'", m.group(1))]
            tokens["font-%s" % stack_name] = ", ".join(parts)
    return tokens


def vendor_from_npm(version):
    """npm pack the preset into a scratch dir, parse it, write data/."""
    spec = "%s@%s" % (PACKAGE, version) if version else PACKAGE
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        try:
            out = subprocess.run(
                ["npm", "pack", spec, "--silent", "--pack-destination", str(tmp)],
                capture_output=True, text=True, check=True, timeout=120,
            )
        except FileNotFoundError:
            raise SystemExit("--update needs npm on PATH")
        except subprocess.CalledProcessError as exc:
            raise SystemExit("npm pack failed:\n%s" % (exc.stderr or exc.stdout))

        tarballs = sorted(tmp.glob("*.tgz"))
        if not tarballs:
            raise SystemExit("npm pack produced nothing (said: %s)" % out.stdout.strip())

        dest = tmp / "x"
        with tarfile.open(tarballs[0]) as tf:
            # Only the one file is wanted, and only from inside package/.
            members = [m for m in tf.getmembers()
                       if m.isfile() and m.name == "package/src/index.js"]
            if not members:
                raise SystemExit("the tarball has no package/src/index.js")
            tf.extract(members[0], dest)
        src = (dest / "package" / "src" / "index.js").read_text(encoding="utf-8")

    resolved = re.search(r"-(\d+\.\d+\.\d+[\w.-]*)\.tgz$", tarballs[0].name)
    payload = {
        "package": PACKAGE,
        "version": resolved.group(1) if resolved else (version or "unknown"),
        "fetched": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "note": "Generated by tools/sync-picasso-tokens.py --update. Do not edit.",
        "tokens": dict(sorted(parse_preset(src).items())),
    }
    VENDORED.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


# ------------------------------------------------------------------ comparing

def equivalent(a, b):
    """CSS-equal values that are spelled differently are not drift."""
    a, b = a.strip(), b.strip()
    if a.lower() == b.lower():
        return True
    zero = {"0", "0px", "0rem", "0%"}
    if a in zero and b in zero:
        return True
    # rgba(0,0,0, 0.08) vs rgba(0, 0, 0, 0.08) — spacing inside a value is noise
    return re.sub(r"\s+", "", a).lower() == re.sub(r"\s+", "", b).lower()


def scan(css_lines, published):
    """Walk tokens.css once, classifying every line that claims Picasso."""
    drift, unverified, extended, seen = [], [], [], set()
    for n, line in enumerate(css_lines):
        m = DECL.match(line.rstrip("\n"))
        if not m or not m.group("comment"):
            continue
        tag = PICASSO_TAG.match(m.group("comment").strip())
        if not tag:
            continue

        name, value = m.group("name"), m.group("value").strip()
        seen.add(name)
        if tag.group("mod") == "+":
            extended.append((n, name, value, tag.group("note")))
            continue
        if name not in published:
            unverified.append((n, name, value))
        elif not equivalent(value, published[name]):
            drift.append((n, name, value, published[name]))

    missing = sorted(k for k in published
                     if k not in seen and k not in DELIBERATE_OMISSIONS)
    return drift, unverified, extended, missing


def rewrite(line, new_value):
    """Swap a declaration's value, keeping the comment in its column."""
    m = DECL.match(line.rstrip("\n"))
    head = "%s--%s: %s;" % (m.group("indent"), m.group("name"), new_value)
    comment = m.group("comment")
    if not comment:
        return head + "\n"
    column = len(m.group("indent")) + len("--%s: %s;" % (m.group("name"), m.group("value"))) \
        + len(m.group("gap"))
    pad = max(1, column - len(head))
    return head + " " * pad + comment + "\n"


# ----------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(
        description="Check tokens.css against the published Picasso token preset.")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if any /* picasso */ token has drifted")
    ap.add_argument("--fix", action="store_true",
                    help="rewrite drifted values in tokens.css")
    ap.add_argument("--update", action="store_true",
                    help="re-vendor data/picasso-tokens.json from npm")
    ap.add_argument("--version", metavar="X.Y.Z",
                    help="the version --update takes (default: the pinned one)")
    args = ap.parse_args()

    if args.fix and args.check:
        raise SystemExit("--fix and --check do opposite things; pick one")

    if args.update:
        pinned = None
        if VENDORED.exists():
            pinned = json.loads(VENDORED.read_text(encoding="utf-8")).get("version")
        payload = vendor_from_npm(args.version or pinned)
        print("vendored %s@%s — %d tokens → %s"
              % (PACKAGE, payload["version"], len(payload["tokens"]),
                 VENDORED.relative_to(ROOT)))
        if not (args.check or args.fix):
            return 0

    if not VENDORED.exists():
        raise SystemExit("no %s yet — run with --update first"
                         % VENDORED.relative_to(ROOT))

    vendored = json.loads(VENDORED.read_text(encoding="utf-8"))
    published = vendored["tokens"]
    lines = TOKENS_CSS.read_text(encoding="utf-8").splitlines(keepends=True)
    drift, unverified, extended, missing = scan(lines, published)

    checked = len(published) - len(missing)
    print("tokens.css vs %s@%s (vendored %s)"
          % (PACKAGE, vendored["version"], vendored.get("fetched", "?")))
    print("  %d of %d published tokens are transcribed here" % (checked, len(published)))

    if drift:
        print("\n  DRIFT — transcribed from Picasso, no longer matches it:")
        for n, name, have, want in drift:
            print("    tokens.css:%-4d --%-22s is %-12s Picasso says %s"
                  % (n + 1, name, have, want))
    if unverified:
        print("\n  NOT IN THIS PRESET — %d token(s) tagged /* picasso */ that %s"
              % (len(unverified), PACKAGE))
        print("    does not publish. Picasso is several packages; these come from"
              " elsewhere in it")
        print("    (the MUI theme, mostly), so they are correct but unchecked here"
              " — not mislabelled.")
        for n, name, have in unverified:
            print("    tokens.css:%-4d --%-22s = %s" % (n + 1, name, have))
    if extended:
        print("\n  EXTENDED — ours on purpose, never rewritten:")
        for n, name, have, note in extended:
            print("    tokens.css:%-4d --%-22s %s" % (n + 1, name, note or ""))
    if missing:
        print("\n  NOT TRANSCRIBED — this preset publishes these, tokens.css has no"
              " line for them:")
        for name in missing:
            print("    --%-22s %s" % (name, published[name]))

    dropped = sorted(k for k in published if k in DELIBERATE_OMISSIONS)
    if dropped:
        reasons = {}
        for k in dropped:
            reasons.setdefault(DELIBERATE_OMISSIONS[k], []).append(k)
        print("\n  LEFT OUT ON PURPOSE — %d published token(s), argued in tokens.css:"
              % len(dropped))
        for reason, names in sorted(reasons.items()):
            shown = ", ".join("--" + n for n in names[:3])
            if len(names) > 3:
                shown += ", +%d more" % (len(names) - 3)
            print("    %s" % shown)
            print("      %s" % reason)

    if args.fix and drift:
        for n, name, _have, want in drift:
            lines[n] = rewrite(lines[n], want)
        TOKENS_CSS.write_text("".join(lines), encoding="utf-8")
        print("\n  fixed %d value(s) in tokens.css — re-run tools/build-packages.py"
              % len(drift))
        return 0

    if not drift:
        print("\n  no drift.")
    elif args.check:
        print("\n  %d token(s) drifted — run with --fix" % len(drift))
        return 1
    else:
        print("\n  %d token(s) drifted — run with --fix" % len(drift))
    return 0


if __name__ == "__main__":
    sys.exit(main())
