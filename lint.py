#!/usr/bin/env python3
"""lint.py — check a prototype against the kit before it ships.

Documentation asks a model to be good. A check only asks it to be correctable,
which is the difference between a system that works for one careful author and
one that works for any tool pointed at it.

What it catches, in the order the failures actually happen:

  invented class      a class no stylesheet defines — it renders as nothing
  showcase class      a class example.html styles in its own <style> block.
                      These look exactly like kit classes when markup is
                      copied out of the showcase; .btn-cta-icon is the one a
                      cold-start test walked into.
  dead icon           <use href="#i-…"> naming a symbol the sprite lacks.
                      Renders blank, silently.
  retired Phosphor    <i class="ph …">. The pack is gone; nothing renders.
  raw primitive       var(--color-blue-500) where a semantic alias belongs.
                      Re-pointing a theme cannot reach it.
  raw hex             a colour written past the token layer entirely.
  raw spacing         a px value in a style= attribute that a token already has.

    python3 lint.py ../features/my-feature/index.html
    python3 lint.py ../features/*/index.html --quiet

Exit status is 1 if any error was found; warnings alone exit 0.
"""

import argparse
import json
import pathlib
import re
import sys
from urllib.parse import unquote, urlparse

HERE = pathlib.Path(__file__).resolve().parent

# inline.py stamps this marker when it bakes the stylesheets in. A baked file
# legitimately carries the whole system in a <style> block, so the checks that
# look for hand-authored CSS have to stand down.
INLINED_MARKER = "/* === tokens.css === */"

# Spacing steps a token already covers, so a raw px value is a choice to drift.
SPACING_PX = {"0": "0", "4": "1", "8": "2", "12": "3", "16": "4",
              "24": "6", "32": "8", "40": "10", "48": "12"}

# Classes that are legitimately not in the kit: state hooks a prototype sets
# itself, and the author tooling inline.py bakes in.
ALLOWED_PREFIXES = ("cm-", "md-", "js-", "pg-", "ic-review", "annot-")


class Finding:
    def __init__(self, level, line, code, message):
        self.level, self.line, self.code, self.message = level, line, code, message


def load_kit():
    path = HERE / "dist" / "kit.json"
    if not path.exists():
        sys.exit("dist/kit.json is missing — run: python3 tools/build-packages.py")
    kit = json.loads(path.read_text())
    classes = {c for group in kit["classes"].values() for c in group}
    # Hooks carry no CSS but are how the delegated script finds its targets.
    classes |= set(kit.get("behaviourHooks", []))
    return kit, classes, set(kit["showcaseOnly"]), set(kit.get("tooling", []))


def load_icons():
    sprite = HERE / "icons.svg"
    if not sprite.exists():
        return None
    return set(re.findall(r'<symbol[^>]*id="([^"]+)"', sprite.read_text()))


def semantic_tokens():
    """Aliases a prototype may reference, from semantic.css plus the scales."""
    out = set()
    for name in ("semantic.css", "tokens.css"):
        text = re.sub(r"/\*.*?\*/", "", (HERE / name).read_text(), flags=re.S)
        out |= set(re.findall(r"(--[\w-]+)\s*:", text))
    return out


def primitives():
    """Palette ramps a prototype should never reach for directly."""
    text = re.sub(r"/\*.*?\*/", "", (HERE / "tokens.css").read_text(), flags=re.S)
    names = set(re.findall(r"(--color-[\w-]+)\s*:", text))
    # A ramp step ends in a number (--color-blue-500); the role aliases in
    # semantic.css do not, which is what separates the two layers by name.
    return {n for n in names if re.search(r"-\d+(-hover|-active)?$", n)}


def line_of(text, index):
    return text.count("\n", 0, index) + 1


def lint(path, kit_classes, showcase, tooling, icons, prims):
    html = path.read_text()
    inlined = INLINED_MARKER in html
    found = []

    # The file's own <style> blocks: classes defined here are prototype-scoped.
    # Take every block EXCEPT the one inline.py baked the system into. Reading
    # only what follows that block misses a prototype's own CSS when it sits
    # above it, which is the usual order — and then reports classes as invented
    # while the file styles them a few hundred lines up.
    blocks = re.findall(r"<style[^>]*>(.*?)</style>", html, re.S)
    own_style = "".join(b for b in blocks if INLINED_MARKER not in b)

    # A class the file's own script selects on is a behaviour hook, not an
    # invented class — the same thing .dropdown-trigger is for the kit. It
    # carries no CSS on purpose, and reporting it as undefined sends a reader
    # looking for missing styles instead of leaving it alone.
    own_script = "".join(re.findall(r"<script[^>]*>(.*?)</script>", html, re.S))
    hooks = set()
    for m in re.finditer(r"(?:querySelector(?:All)?|closest|matches)\(\s*['\"]([^'\"]+)", own_script):
        hooks |= set(re.findall(r"\.([a-z][\w-]*)", m.group(1)))
    for m in re.finditer(r"classList\.\w+\(\s*['\"]([\w-]+)", own_script):
        hooks.add(m.group(1))
    own_classes = set(re.findall(r"\.([a-z][\w-]*)", re.sub(r"/\*.*?\*/", "", own_style, flags=re.S)))

    markup = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.S)
    # An HTML comment is not markup either. a page may document markup in a comment, and a
    # <link> or a class inside one is being shown, not used — reading them live reports stylesheets that are
    # not loaded and classes that are not on the page.
    markup = re.sub(r"<!--.*?-->", "", markup, flags=re.S)


    # A prototype may keep its CSS in a sibling file rather than a <style>
    # block — features/docs/ does. Reading only <style> flags every one of
    # its classes as invented. While we are here, a <link> is worth checking
    # in its own right: a relative href that resolves to nothing leaves the
    # page unstyled with no error, and an http one breaks the promise that a
    # shipped prototype has no external dependencies.
    for m in re.finditer(r'<link[^>]*rel="stylesheet"[^>]*href="([^"]+)"', markup):
        href = m.group(1)
        ln = line_of(markup, m.start())
        if href.startswith(("http://", "https://", "//")):
            found.append(Finding("error", ln, "external-css",
                f"{href} is fetched at runtime — a prototype ships self-contained"))
            continue
        if href.startswith("file://"):
            # An absolute file:// URL is a real local path, not a relative one.
            # Resolving it against the page's folder invents a missing file.
            target = pathlib.Path(unquote(urlparse(href).path))
        else:
            target = (path.parent / href).resolve()
        if not target.exists():
            found.append(Finding("error", ln, "dead-stylesheet",
                f"{href} does not exist — everything it styles renders unstyled"))
            continue
        if target.suffix == ".css" and HERE not in target.parents:
            sheet = re.sub(r"/\*.*?\*/", "", target.read_text(), flags=re.S)
            own_classes |= set(re.findall(r"\.([a-z][\w-]*)", sheet))

    # Scan markup only. A <style> block's own comments quote example markup —
    # components.css documents the breadcrumb as
    # `<span class="breadcrumb is-current">` — and once inline.py bakes the
    # stylesheets in, those comments are inside the file. Reading them as
    # markup invents classes like .current and .null that nobody wrote.
    # A bare `ph` is Phosphor's base class — but it is also a perfectly
    # ordinary name for a placeholder, which is what planning-voyage and
    # action-trace use it as. Only read it as Phosphor when the file shows
    # the pack elsewhere: a ph-* class in markup, or the CDN stylesheet.
    uses_phosphor = bool(re.search(r'class="[^"]*\bph-[\w-]+', markup)) or "phosphor-icons" in html

    # --- classes used in markup
    for m in re.finditer(r'class="([^"]*)"', markup):
        # Markup built in JS carries template expressions inside the attribute —
        # class="sheet-opt${o === current ? ' is-active' : ''}". Splitting that
        # on whitespace invents classes out of the expression's own identifiers.
        value = re.sub(r"\$\{[^{}]*\}", " ", m.group(1))
        for cls in value.split():
            if not re.fullmatch(r"[a-z][\w-]*", cls):
                continue
            if cls in kit_classes or cls in tooling or cls.startswith(ALLOWED_PREFIXES):
                continue
            ln = line_of(markup, m.start())
            if re.fullmatch(r"ph-[\w-]+", cls) or (cls == "ph" and uses_phosphor):
                # Not an invented class: these resolve against the Phosphor
                # CDN stylesheet some prototypes still link, so they render —
                # off an external dependency, from a pack the system retired.
                found.append(Finding("error", ln, "phosphor-class",
                    f".{cls} is Phosphor — retired, and it only renders while the CDN stylesheet loads"))
            elif cls in showcase:
                found.append(Finding("error", ln, "showcase-class",
                    f".{cls} is example.html's own chrome, not a kit class — it has no styles outside the showcase"))
            elif cls in hooks:
                found.append(Finding("warn", ln, "js-hook",
                    f".{cls} carries no CSS — this file's script selects on it"))
            elif cls in own_classes:
                found.append(Finding("warn", ln, "local-class",
                    f".{cls} is defined in this file — add it to components.css so the next screen inherits it"))
            else:
                found.append(Finding("error", ln, "unknown-class",
                    f".{cls} is not defined anywhere — it renders as nothing"))

    # --- one primary call to action per page
    # Green is both the primary CTA and the success colour, so a second one
    # means neither reads as the action. .topbar-cta is exempt only when it is
    # the page's single primary: it belongs to the collapsed layout, and
    # nothing hides .page-head-actions there, so a page carrying both shows
    # two at once below 768px.
    primary = re.findall(r'class="([^"]*\bbtn-primary\b[^"]*)"', markup)
    if len(primary) > 1:
        found.append(Finding("error", line_of(markup, markup.find("btn-primary")), "two-primary",
            f"{len(primary)} .btn-primary on one page — every CTA but the most important is .btn-secondary"))

    # --- icon references
    # A prototype may ship symbols of its own alongside the sprite — product
    # marks, illustrations — so the file's own <symbol> ids count as defined.
    if icons:
        local = set(re.findall(r'<symbol[^>]*id="([^"]+)"', html))
        known = icons | local
        for m in re.finditer(r'<use[^>]*href="#([\w-]+)"', markup):
            if m.group(1) not in known:
                found.append(Finding("error", line_of(markup, m.start()), "dead-icon",
                    f"#{m.group(1)} is not in icons.svg — the glyph renders blank"))

    # --- retired Phosphor
    for m in re.finditer(r'<i[^>]*class="[^"]*\bph\b', markup):
        found.append(Finding("error", line_of(markup, m.start()), "phosphor",
            "Phosphor is retired — use <svg class=\"icon\"><use href=\"#i-{slug}\"/></svg>"))

    # --- primitives referenced past the semantic layer
    for m in re.finditer(r"var\(\s*(--color-[\w-]+)", markup):
        if m.group(1) in prims:
            found.append(Finding("warn", line_of(markup, m.start()), "raw-primitive",
                f"{m.group(1)} is a palette primitive — reference a semantic alias so themes can re-point it"))

    # --- raw colour, past the token layer entirely
    scope = markup
    for m in re.finditer(r'style="[^"]*?(#[0-9a-fA-F]{3,8})\b', scope):
        found.append(Finding("error", line_of(scope, m.start()), "raw-hex",
            f"{m.group(1)} is a raw colour — use a semantic token"))

    # --- raw spacing where a token exists
    for m in re.finditer(r'style="([^"]*)"', markup):
        for prop, value in re.findall(r"(gap|margin|padding)(?:-\w+)?:\s*([^;\"]+)", m.group(1)):
            if "var(" in value:
                continue
            for px in re.findall(r"(\d+)px", value):
                if px in SPACING_PX:
                    found.append(Finding("warn", line_of(markup, m.start()), "raw-spacing",
                        f"{prop}: {px}px — use var(--spacing-{SPACING_PX[px]})"))

    return found, inlined


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--quiet", action="store_true", help="errors only")
    args = ap.parse_args()

    kit, classes, showcase, tooling = load_kit()
    icons, prims = load_icons(), primitives()

    total_err = total_warn = 0
    for raw in args.paths:
        path = pathlib.Path(raw)
        if not path.exists():
            print(f"{raw}: no such file", file=sys.stderr)
            total_err += 1
            continue

        found, inlined = lint(path, classes, showcase, tooling, icons, prims)
        # One complaint per distinct problem. A class used ninety times is one
        # thing to fix, and counting it ninety times buries the other eighty-
        # nine problems in the file.
        distinct, keys = [], set()
        for f in found:
            key = (f.code, f.message)
            if key not in keys:
                keys.add(key)
                distinct.append(f)
        found = distinct
        errors = [f for f in found if f.level == "error"]
        warns = [f for f in found if f.level == "warn"]
        total_err += len(errors)
        total_warn += len(warns)

        shown = errors if args.quiet else errors + warns
        state = "inlined" if inlined else "linked"
        if not shown:
            print(f"✓ {path}  ({state}) — clean")
            continue

        print(f"\n{path}  ({state})  {len(errors)} error(s), {len(warns)} warning(s)")
        seen = set()
        for f in sorted(shown, key=lambda f: (f.line, f.code)):
            # One line per distinct complaint; a repeated class is noise.
            key = (f.code, f.message)
            if key in seen:
                continue
            seen.add(key)
            mark = "✗" if f.level == "error" else "!"
            print(f"  {mark} {path.name}:{f.line}  [{f.code}] {f.message}")

    print(f"\n{total_err} error(s), {total_warn} warning(s)")
    return 1 if total_err else 0


if __name__ == "__main__":
    sys.exit(main())
