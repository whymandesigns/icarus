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
  local breakpoint    a @media/@container in the page's own CSS that styles a
                      shell class, or a width-driven matchMedia in its script.
                      The shell responds at one edge and it is the kit's —
                      a second one here is what makes two screens disagree
                      about a phone. Compact is a user choice, never a width.
  incomplete shell    a .sidenav inside .app-shell with no .topbar-menu, or
                      nothing wired to open it. Below 1024px the rail is
                      off-canvas and the hamburger is the only way back to it.
  raw primitive       var(--color-blue-500) where a semantic alias belongs.
                      Re-pointing a theme cannot reach it.
  raw hex             a colour written past the token layer entirely.
  raw spacing         a px value in a style= attribute that a token already has.
  dead token          var(--x) naming a token nothing defines. A retired token
                      stays in tokens.css as a comment, so it still reads as
                      present — and CSS drops the whole declaration.

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

# A prototype that predates the current system and is knowingly not on it yet.
# Its errors are still printed — they are real — but they do not fail the run,
# so a sweep over the whole folder stays meaningful: anything WITHOUT this
# marker has to pass. The list can only shrink. Removing the marker is how a
# prototype says it has been migrated, and --strict ignores markers entirely.
#
#   <!-- designmd:legacy — frozen on the --ic-* vocabulary; see AGENTS.md -->
LEGACY_MARKER = re.compile(r"<!--\s*designmd:legacy\b([^>]*)-->")

# Spacing steps a token already covers, so a raw px value is a choice to drift.
SPACING_PX = {"0": "0", "4": "1", "8": "2", "12": "3", "16": "4",
              "24": "6", "32": "8", "40": "10", "48": "12"}

# The product chrome. A prototype may use these; it may not re-decide how they
# behave at a width — that is components.css's single 1024px edge to move.
SHELL_CLASS = r"\.(?:topbar|sidenav|app-shell|page-head)[\w-]*(?![\w-])"

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


def at_rules(css):
    """Yield (kind, prelude, body, start) for each @media/@container rule.

    Brace-matched rather than regex-matched: these blocks hold whole rules, so
    the first } closes their first selector and not the block.
    """
    for m in re.finditer(r"@(media|container)([^{]*)\{", css):
        depth, i = 1, m.end()
        while i < len(css) and depth:
            depth += {"{": 1, "}": -1}.get(css[i], 0)
            i += 1
        yield m.group(1), m.group(2).strip(), css[m.end():i - 1], m.start()


def line_of(text, index):
    return text.count("\n", 0, index) + 1


def blank(pattern, text, flags=re.S):
    """Remove a region but keep the line count.

    Deleting it outright shifts every line number after it, so a finding in an
    inlined prototype — where the baked CSS and the sprite are thousands of
    lines — points at a line that holds something else entirely.
    """
    return re.sub(pattern, lambda m: "\n" * m.group(0).count("\n"), text, flags=flags)


# What inline.py injects: the review bar's CSS and JS, the plugin launcher and
# the icon sprite. It is designmd's own tooling, identical in every baked file
# and not the prototype's to fix, so it is excluded from every scan below.
TOOLING_REGIONS = [
    r"<!-- === review\.css === -->.*?<!-- === /review\.css === -->",
    r"<!-- === review\.js === -->.*?<!-- === /review\.js === -->",
    r"<!-- === icons\.svg === -->.*?<!-- === /icons\.svg === -->",
]


def lint(path, kit_classes, showcase, tooling, icons, prims, semantic):
    html = path.read_text()
    inlined = INLINED_MARKER in html
    quarantined = LEGACY_MARKER.search(html)
    found = []

    # The file's own <style> blocks: classes defined here are prototype-scoped.
    # Take every block EXCEPT the one inline.py baked the system into. Reading
    # only what follows that block misses a prototype's own CSS when it sits
    # above it, which is the usual order — and then reports classes as invented
    # while the file styles them a few hundred lines up.
    without_tooling = html
    for region in TOOLING_REGIONS:
        without_tooling = blank(region, without_tooling)
    all_style_blocks = re.findall(r"<style[^>]*>(.*?)</style>", without_tooling, re.S)
    # The marker has to OPEN the block, as inline.py's own pattern requires.
    # Testing `marker in block` instead dropped any prototype stylesheet that
    # merely mentions the marker in a comment — and a block explaining "inline.py
    # only rewrites the block starting with /* === tokens.css === */" does
    # exactly that. Every class it defined was then reported as undefined.
    own_style_blocks = [(m.start(1), m.group(1))
                        for m in re.finditer(r"<style[^>]*>(.*?)</style>", without_tooling, re.S)
                        if not m.group(1).lstrip().startswith(INLINED_MARKER)]
    own_style = "".join(b for _, b in own_style_blocks)

    # A class the file's own script selects on is a behaviour hook, not an
    # invented class — the same thing .dropdown-trigger is for the kit. It
    # carries no CSS on purpose, and reporting it as undefined sends a reader
    # looking for missing styles instead of leaving it alone.
    own_script_blocks = [(m.start(1), m.group(1))
                         for m in re.finditer(r"<script[^>]*>(.*?)</script>", without_tooling, re.S)]
    own_script = "".join(b for _, b in own_script_blocks)
    hooks = set()
    for m in re.finditer(r"(?:querySelector(?:All)?|closest|matches)\(\s*['\"]([^'\"]+)", own_script):
        hooks |= set(re.findall(r"\.([a-z][\w-]*)", m.group(1)))
    for m in re.finditer(r"classList\.\w+\(\s*['\"]([\w-]+)", own_script):
        hooks.add(m.group(1))
    own_classes = set(re.findall(r"\.([a-z][\w-]*)", re.sub(r"/\*.*?\*/", "", own_style, flags=re.S)))

    markup = html
    for region in TOOLING_REGIONS:
        markup = blank(region, markup)
    markup = blank(r"<style[^>]*>.*?</style>", markup)
    # An HTML comment is not markup either. a page may document markup in a comment, and a
    # <link> or a class inside one is being shown, not used — reading them live reports stylesheets that are
    # not loaded and classes that are not on the page.
    markup = blank(r"<!--.*?-->", markup)


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
    # means neither reads as the action.
    #
    # .topbar-cta does not count. It is the collapsed layout's primary, and the
    # kit hides .page-head at the same 1024px edge that reveals it, so the two
    # are never on screen together — the rule is about what the eye sees, not
    # what the file contains. (Before that breakpoint existed they could both
    # show, and this exemption would have been wrong.) A second .topbar-cta is
    # still an error: those WOULD share the bar.
    # Markup only, with <script> taken out. A class attribute inside a template
    # string is not on the page — it is what some transient surface will build
    # when it opens: a popover's confirm, a modal's save. Those are each the
    # primary action OF THAT SURFACE, and the surface is never on screen beside
    # the page's own CTA, so counting them here reports a clash that no one can
    # see. (onboarding had two: a date popover's "Set" and a link editor's
    # "Save", in a page with no static .btn-primary at all.) The cost is that a
    # page head rendered entirely in JS escapes the tally, which is the right
    # way round — this rule is about what the eye sees.
    on_page_markup = blank(r"<script[^>]*>.*?</script>", markup)
    primary = re.findall(r'class="([^"]*\bbtn-primary\b[^"]*)"', on_page_markup)
    in_bar = [c for c in primary if re.search(r'\btopbar-cta\b', c)]
    on_page = [c for c in primary if c not in in_bar]
    if len(on_page) > 1:
        found.append(Finding("error", line_of(on_page_markup, on_page_markup.find("btn-primary")), "two-primary",
            f"{len(on_page)} .btn-primary on one page — every CTA but the most important is .btn-secondary"))
    if len(in_bar) > 1:
        found.append(Finding("error", line_of(on_page_markup, on_page_markup.find("topbar-cta")), "two-primary",
            f"{len(in_bar)} .btn-primary.topbar-cta — the collapsed bar has room for one action"))

    # --- var() pointing at a token nothing defines
    #
    # The quietest failure in the system. A retired token leaves its name in
    # tokens.css as a comment, so it reads as present; CSS then drops the whole
    # declaration, and a gradient, a colour or a shadow is simply absent. It
    # cost one migration a hero panel, which the screenshot caught and nothing
    # else would have. A var() with a fallback still renders, so only a bare
    # reference is an error.
    def defined_in(css):
        # Comments out first. A retired token lives on as `/* --x: v; */`, and
        # counting that as a definition is the very bug this rule is for.
        return set(re.findall(r"(--[\w-]+)\s*:",
                              re.sub(r"/\*.*?\*/", "", css, flags=re.S)))

    local_tokens = defined_in(own_style)
    if inlined:
        # A baked file carries the whole system in its own <style>, so the
        # vocabulary to check against is what IT defines, not what this
        # checkout does — they are the same thing once it is freshly baked.
        for b in all_style_blocks:
            local_tokens |= defined_in(b)
    scopes = [(css, without_tooling, off) for off, css in own_style_blocks]
    scopes += [(m.group(1), markup, m.start(1))
               for m in re.finditer(r'style="([^"]*)"', markup)]
    seen_dead = set()
    for text, frame, offset in scopes:
        for m in re.finditer(r"var\(\s*(--[\w-]+)\s*\)", text):
            name = m.group(1)
            if name in prims or name in semantic or name in local_tokens:
                continue
            if name in seen_dead:
                continue
            seen_dead.add(name)
            ln = line_of(frame, offset + m.start())
            found.append(Finding("error", ln, "dead-token",
                f"{name} is not defined anywhere — CSS drops the whole declaration, "
                "so whatever it styles is simply absent"))

    # --- the shell responds at one edge, and the page does not participate
    #
    # Below 1024px three things fire together: the bar collapses, the rail
    # goes off-canvas, the page head stands down. A page-local breakpoint on a
    # shell class re-decides one of those alone, and two screens built a month
    # apart then disagree about what a phone looks like. The fix is always the
    # same — move the rule into components.css, where every screen inherits it.
    #
    # Scoped to shell classes on purpose. A prototype laying its own content
    # out at its own widths is doing nothing wrong; re-deciding the chrome is.
    for offset, css in own_style_blocks:
        for kind, prelude, body, start in at_rules(css):
            # Width only. A preference query — prefers-reduced-motion, forced-
            # colors — is not a breakpoint and is the page's to answer.
            if "width" not in prelude:
                continue
            # A kit class only. A page's own .sidenav-panel is its invention,
            # already reported as local-class — it is not the shell moving.
            names = re.findall(SHELL_CLASS, re.sub(r"/\*.*?\*/", "", body, flags=re.S))
            hit = next((n for n in names if n[1:] in kit_classes), None)
            if not hit:
                continue
            found.append(Finding("error", line_of(without_tooling, offset + start),
                "local-breakpoint",
                f"@{kind} {prelude} styles {hit} — the shell already responds at "
                "1024px in components.css, and a second edge here is what makes two screens "
                "disagree"))

    # The same drift written in JS. .is-compact is the one worth naming: it is
    # the 62px icon rail, a way to buy horizontal space when the user asks for
    # it with the chevron. Below 1024px the rail is a panel floating over the
    # content, which is not short of room — so the kit widens it back to 236px
    # and four prototypes fought that with a matchMedia of their own.
    for offset, js in own_script_blocks:
        queries = list(re.finditer(r"matchMedia\(\s*['\"]\(([^'\"]*width[^'\"]*)\)", js))
        if not queries:
            continue
        ln = line_of(without_tooling, offset + queries[0].start())
        # The tell is a FORCED toggle: toggle('is-compact', expr). The
        # chevron's own toggle takes no second argument — this one is handed a
        # media query's .matches, which is a width overruling a user's choice.
        forced = re.search(r"classList\.toggle\(\s*['\"]is-compact['\"]\s*,\s*([^)]*)\)", js)
        if forced and ".matches" in forced.group(1):
            found.append(Finding("error", ln, "local-breakpoint",
                "matchMedia drives .is-compact — compact is a user choice, never a width. "
                "Below 1024px the kit widens the rail back to 236px, because a panel over the "
                "content is not short of space"))
            continue
        off_edge = {m.group(1) for m in queries
                    if not re.search(r"max-width:\s*1024px|min-width:\s*1025px", m.group(1))}
        if off_edge and re.search(r"['\"][^'\"]*" + SHELL_CLASS, js):
            found.append(Finding("error", ln, "local-breakpoint",
                f"matchMedia ({'), ('.join(sorted(off_edge))}) drives a shell class — the shell "
                "collapses at 1024px, and a second edge here splits the two apart"))

    # --- the off-canvas rail needs the hamburger that opens it
    #
    # Below 1024px .app-shell > .sidenav leaves the flow and slides over the
    # content. It is hidden, not deleted — and .topbar-menu is wired to nothing
    # by default, so a page missing either the button or the handler has a
    # navigation no one can reach on a phone. The three pieces only work as a
    # set, and template/index.html ships all three.
    nav = re.search(r'class="[^"]*\bsidenav(?![\w-])', markup)
    if nav and re.search(r'class="[^"]*\bapp-shell(?![\w-])', markup):
        ln = line_of(markup, nav.start())
        if not re.search(r'class="[^"]*\btopbar-menu(?![\w-])', markup):
            found.append(Finding("error", ln, "shell-incomplete",
                ".sidenav with no .topbar-menu — below 1024px the rail is off-canvas and that "
                "hamburger is the only way back to it"))
        if not re.search(r"classList\.\w+\(\s*['\"]is-open", own_script):
            found.append(Finding("error", ln, "shell-incomplete",
                "nothing toggles .is-open on the .sidenav — below 1024px the rail slides "
                "off-canvas and never comes back"))

    # --- icon references
    # A prototype may ship symbols of its own alongside the sprite — product
    # marks, illustrations — so the file's own <symbol> ids count as defined.
    if icons:
        local = set(re.findall(r'<symbol[^>]*id="([^"]+)"', html))
        # A baked file carries its own sprite, and inline.py narrows that to the
        # symbols the page names — so the file itself is the truth about what
        # will render. Checking against the full icons.svg instead would pass a
        # reference the baked sprite does not contain, which draws nothing.
        known = local if (inlined and local) else icons | local
        for m in re.finditer(r'<use[^>]*href="#([\w-]+)"', markup):
            name = m.group(1)
            if name in known:
                continue
            if inlined and icons and name in icons:
                # It exists in the system, just not in THIS file's sprite:
                # inline.py narrows the sprite to the icons the page names.
                msg = (f"#{name} is in icons.svg but not in this file's sprite — "
                       "inline.py ships only the icons the page names, so re-bake "
                       "after adding one")
            else:
                msg = f"#{name} is not in icons.svg — the glyph renders blank"
            found.append(Finding("error", line_of(markup, m.start()), "dead-icon", msg))

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

    return found, inlined, quarantined


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--quiet", action="store_true", help="errors only")
    ap.add_argument("--strict", action="store_true",
                    help="ignore designmd:legacy markers — every file must pass")
    args = ap.parse_args()

    kit, classes, showcase, tooling = load_kit()
    icons, prims = load_icons(), primitives()
    semantic = semantic_tokens()

    total_err = total_warn = total_quar = 0
    for raw in args.paths:
        path = pathlib.Path(raw)
        if not path.exists():
            print(f"{raw}: no such file", file=sys.stderr)
            total_err += 1
            continue

        found, inlined, quarantined = lint(path, classes, showcase, tooling, icons, prims, semantic)
        if quarantined and args.strict:
            quarantined = None
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
        if quarantined:
            total_quar += len(errors)
        else:
            total_err += len(errors)
        total_warn += len(warns)

        shown = errors if args.quiet else errors + warns
        state = "inlined" if inlined else "linked"
        if quarantined:
            state += ", legacy"
        if not shown:
            print(f"✓ {path}  ({state}) — clean")
            continue

        print(f"\n{path}  ({state})  {len(errors)} error(s), {len(warns)} warning(s)")
        if quarantined:
            why = quarantined.group(1).strip(" —-") or "no reason given"
            print(f"  ‣ quarantined, so these do not fail the run: {why}")
        seen = set()
        for f in sorted(shown, key=lambda f: (f.line, f.code)):
            # One line per distinct complaint; a repeated class is noise.
            key = (f.code, f.message)
            if key in seen:
                continue
            seen.add(key)
            mark = "✗" if f.level == "error" else "!"
            print(f"  {mark} {path.name}:{f.line}  [{f.code}] {f.message}")

    tail = f", {total_quar} in quarantined file(s)" if total_quar else ""
    print(f"\n{total_err} error(s), {total_warn} warning(s){tail}")
    return 1 if total_err else 0


if __name__ == "__main__":
    sys.exit(main())
