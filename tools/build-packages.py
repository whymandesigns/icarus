#!/usr/bin/env python3
"""build-packages.py — emit every downstream package from the three stylesheets.

designmd has two consumers that each need a different shape of the same system:

    Claude Code    reads the repo directly, but needs a machine-readable
                   inventory so it never invents a class or copies a
                   showcase-only one out of example.html.

    Claude Design  reads a Design System artifact, which wants tokens as
                   typed lists and the CSS as one bundle.

Both were hand-built once and drifted apart: the artifact published on
2026-10-23 still spoke the --ic- vocabulary months after the repo dropped it.
Generating both from one run is the only thing that stops that happening again.

    python3 tools/build-packages.py            # writes dist/
    python3 tools/build-packages.py --check    # verify dist/ matches source

Outputs (designmd/dist/):
    kit.json       every component class, grouped, with the showcase-only
                   classes listed separately so a linter can reject them
    tokens.json    the artifact's token schema, values resolved
    bundle.css     components.css + the bridge the artifact page can't generate
"""

import argparse
import json
import pathlib
import re
import sys
from collections import OrderedDict

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
DIST = ROOT / "dist"

# Families the artifact page can read, in the order it shows them. Motion is
# absent on purpose: the schema has no shape for it, so duration/ease/animate
# travel in bundle.css instead and are documented in prose.
FAMILY_BY_PREFIX = [
    ("color-", "color"),
    ("spacing-", "spacing"),
    ("radius-", "radius"),
    ("shadow-", "shadow"),
    ("z-", "zIndex"),
    ("breakpoint-", "breakpoint"),
    ("border-", "border"),
    ("container-", "layout"),
    ("max-width-", "layout"),
    ("min-width-", "layout"),
    ("header-", "layout"),
    ("width-input", "layout"),
    ("height-input", "layout"),
    ("padding-input", "layout"),
]
MOTION_PREFIXES = ("duration-", "ease", "animate-")
TYPE_PREFIXES = ("text-", "font-", "leading-")


# ---------------------------------------------------------------- parsing


def strip_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def parse_declarations(css, block=None):
    """Return [(name, value, trailing_comment)] in source order.

    `block` restricts the scan to one selector's body, which is how the dark
    theme is read separately from :root.
    """
    if block is not None:
        m = re.search(re.escape(block) + r"\s*\{(.*?)\n\}", css, re.S)
        if not m:
            return []
        css = m.group(1)

    out = []
    for line in css.split("\n"):
        # A line may hold a declaration and a trailing /* note */.
        m = re.match(r"\s*(--[\w-]+)\s*:\s*([^;]+);\s*(?:/\*\s*(.*?)\s*\*/)?", line)
        if not m:
            continue
        name, value, comment = m.group(1), m.group(2).strip(), (m.group(3) or "").strip()
        # A declaration commented out in full never matches, because the line
        # starts with /*. One inside a multi-line comment block would, so skip
        # anything whose value still carries comment syntax.
        if "*/" in value or "/*" in value:
            continue
        out.append((name, value, comment))
    return out


def resolve(value, table, seen=None):
    """Expand var() chains to a literal. Unresolvable references come back as-is."""
    seen = seen or set()
    for _ in range(10):
        refs = re.findall(r"var\(\s*(--[\w-]+)\s*(?:,[^)]*)?\)", value)
        if not refs:
            return value.strip()
        for ref in refs:
            if ref in seen or ref not in table:
                return value.strip()
            seen.add(ref)
            value = re.sub(
                r"var\(\s*" + re.escape(ref) + r"\s*(?:,[^)]*)?\)", table[ref], value
            )
    return value.strip()


def family_of(name):
    key = name[2:]
    if key.startswith(TYPE_PREFIXES):
        return "type"
    if key.startswith(MOTION_PREFIXES):
        return "motion"
    for prefix, fam in FAMILY_BY_PREFIX:
        if key.startswith(prefix):
            return fam
    return None


# ------------------------------------------------------------- tokens.json


def usage_for(name, comment, alias_target, family):
    """A usage note for every token, as the artifact's checklist asks.

    The stylesheets already carry the reasoning — `/* picasso */`, or a real
    sentence where someone bothered. Prefer their words; fall back to stating
    the provenance, which is the thing a reader most needs to know.
    """
    note = comment.strip()
    parts = []
    if note and note.lower() not in ("picasso", "extension"):
        parts.append(note[0].upper() + note[1:] if note else note)
        provenance = "picasso" if "picasso" in note.lower() else None
    else:
        provenance = note.lower() or None

    if not parts:
        if provenance == "picasso":
            parts.append(f"Picasso {family} token, name and value verbatim.")
        elif provenance == "extension":
            parts.append("designmd extension — not in Picasso.")
        elif alias_target:
            # A semantic role with no note of its own says the useful thing by
            # naming what it points at, rather than restating its family.
            parts.append("Semantic role.")
        else:
            parts.append(f"{family.capitalize()} token.")

    if alias_target:
        parts.append(f"→ {alias_target[2:]}")
    return " ".join(parts).strip()


def build_tokens_json(primitives, semantic_light, semantic_dark, table):
    families = OrderedDict()

    def add(fam, name, value, usage):
        families.setdefault(fam, []).append(
            {"name": name[2:], "value": value, "usage": usage}
        )

    # --- primitives, in source order
    for name, value, comment in primitives:
        fam = family_of(name)
        if fam in (None, "type", "motion"):
            continue
        add(fam, name, resolve(value, table), usage_for(name, comment, None, fam))

    # --- semantic colour aliases, resolved, with the target recorded in usage
    dark_map = {n: v for n, v, _ in semantic_dark}
    for name, value, comment in semantic_light:
        if not name.startswith("--color-"):
            continue
        target = re.match(r"var\(\s*(--[\w-]+)", value)
        light = resolve(value, table)
        entry = {
            "name": name[2:],
            "usage": usage_for(name, comment, target.group(1) if target else None, "color"),
        }
        if name in dark_map:
            entry["value"] = {"light": light, "dark": resolve(dark_map[name], table)}
        else:
            entry["value"] = light
        families.setdefault("color", []).append(entry)

    # --- type: its own shape
    text_sizes = {
        n: v for n, v, _ in primitives if n.startswith("--text-") and "line-height" not in n
    }
    line_heights = {
        n.replace("--line-height", ""): v
        for n, v, _ in primitives
        if n.endswith("--line-height")
    }
    weights = {n: v for n, v, _ in primitives if n.startswith("--font-weight-")}

    styles = []
    for name, value, comment in semantic_light:
        if not name.startswith("--type-"):
            continue
        # font: <weight> <size>/<line-height> <family>
        m = re.match(r"var\((--font-weight-[\w-]+)\)\s+var\((--text-[\w-]+)\)", value)
        if not m:
            continue
        w_ref, s_ref = m.group(1), m.group(2)
        size = resolve(f"var({s_ref})", table)
        lh = line_heights.get(s_ref)
        style = {
            "name": name[len("--type-"):],
            "fontSize": size,
            "fontWeight": int(re.sub(r"\D", "", weights.get(w_ref, "400")) or 400),
        }
        if lh:
            style["lineHeight"] = resolve(lh, table)
        styles.append(style)

    font_sans = table.get("--font-sans", "")
    font_mono = table.get("--font-mono", "")
    type_block = {
        "fonts": [
            {"family": "Proxima Nova", "file": "fonts/ProximaNova-Regular.woff2", "weight": "400"},
            {"family": "Proxima Nova", "file": "fonts/ProximaNova-Semibold.woff2", "weight": "600"},
        ],
        "families": {"sans": font_sans, "mono": font_mono},
        "groups": [{"name": "Text", "family": "sans", "styles": styles}],
    }

    doc = OrderedDict()
    doc["name"] = "Icarus — designmd"
    doc["version"] = 2
    doc["color"] = {
        "themes": [{"id": "light", "name": "Light"}, {"id": "dark", "name": "Dark"}],
        "tokens": families.pop("color", []),
    }
    doc["type"] = type_block
    for fam in ["spacing", "radius", "shadow", "zIndex", "breakpoint", "border", "layout"]:
        if families.get(fam):
            doc[fam] = {"tokens": families[fam]}
    return doc


# ---------------------------------------------------------------- kit.json


def build_kit_json(components_css, semantic_css, example_html, other_css, design_md):
    """Every class the kit defines, plus the showcase-only ones to reject.

    semantic.css is in here for one class, and it is the one every prototype
    starts with: `.page`, the centred column. It lives there because it is the
    reset's business rather than a component's, and reading only components.css
    leaves the most fundamental layout class looking invented.
    """
    live = strip_comments(components_css) + "\n" + strip_comments(semantic_css)
    script = "".join(re.findall(r"<script>(.*?)</script>", example_html, re.S))

    # Group by the top-level banners components.css already uses. Those are
    # written with a long dash run — /* ---------- Button ---------- */ —
    # which is what separates them from the four-dash sub-headings inside a
    # section, and from ordinary prose comments. A banner may open a comment
    # that runs on over several lines, so the closing */ is not required.
    # A class is filed where it OWNS a rule — where it leads a selector, as
    # `.avatar {` or `.avatar-md,` — not merely where it is first mentioned.
    # Without that, a class named in a descendant selector (`.table .avatar`)
    # gets filed under whichever section happened to reference it first.
    # Ownership follows each selector's SUBJECT — the last compound, since
    # `.badge .icon` is a rule about .icon that merely happens to sit inside a
    # badge. Taking the first class instead files .badge, .tag and .toast under
    # Button, because one shared line near the top reads
    # `.btn .icon, .badge .icon, .tag .icon, .toast .icon { … }`.
    owns, mentions, current = OrderedDict(), OrderedDict(), "misc"
    buf = ""
    for line in (components_css + "\n/* ---------- Layout helpers ---------- */\n" + semantic_css).split("\n"):
        banner = re.match(r"\s*/\*\s*-{6,}\s*(.+?)\s*-{6,}", line)
        if banner:
            current = banner.group(1).strip()
            continue
        clean = strip_comments(line)
        for cls in re.findall(r"\.([a-z][\w-]*)", clean):
            mentions.setdefault(cls, current)

        # Selector lists wrap over several lines, so accumulate until the `{`.
        buf += " " + clean
        if "{" not in clean:
            continue
        selector, _, rest = buf.partition("{")
        buf = "" if "}" in rest else ""
        if "@" in selector:
            continue
        for part in selector.split(","):
            subject = re.split(r"[\s>+~]+", part.strip().rstrip(","))
            subject = [s for s in subject if s]
            if not subject:
                continue
            lead = re.match(r"\.([a-z][\w-]*)", subject[-1])
            if lead:
                owns.setdefault(lead.group(1), current)
    groups = {cls: owns.get(cls, mentions[cls]) for cls in mentions}

    kit = sorted(set(re.findall(r"\.([a-z][\w-]*)", live)))

    # Classes example.html styles in its own <style> block are showcase chrome.
    # They look exactly like kit classes in the markup, which is how a cold
    # model copied .btn-cta-icon into a prototype.
    inline_style = "".join(re.findall(r"<style[^>]*>(.*?)</style>", example_html, re.S))
    showcase = sorted(set(re.findall(r"\.([a-z][\w-]*)", strip_comments(inline_style))) - set(kit))

    tooling = set(re.findall(r"\.([a-z][\w-]*)", strip_comments(other_css))) - set(kit)

    # Some classes carry no CSS at all and are still correct to use: the
    # delegated script in example.html finds its targets by class, and
    # .dropdown-trigger is the one every dropdown needs. Nothing styles it, so
    # a styled-class inventory alone says it does not exist and a reader
    # avoids the very hook the behaviour depends on.
    #
    # Pulled from what the script actually queries, then kept only where the
    # name belongs to a component family the kit already defines — the raw
    # query list is full of fragments like `.th` and `.use` from compound
    # selectors, and of the devtools' own `.map-*` chrome.
    queried = set()
    for pattern in (r"querySelector(?:All)?\(\s*['\"]([^'\"]+)['\"]",
                    r"closest\(\s*['\"]([^'\"]+)['\"]"):
        for sel in re.findall(pattern, script):
            queried |= set(re.findall(r"\.([a-z][\w-]*)", sel))
    families = {c.split("-")[0] for c in kit if "-" in c}
    hooks = sorted(
        c for c in queried - set(kit) - set(showcase)
        if "-" in c and c.split("-")[0] in families
    )

    # Not every component is a class. Tooltips are driven entirely by
    # [data-tooltip], so a reader who sees only the class list concludes the
    # kit has no tooltip and builds one by hand.
    attributes = OrderedDict()
    for attr in sorted(set(re.findall(r"\[(data-[\w-]+)", live))):
        values = sorted(set(re.findall(r"\[" + attr + r'="([^"]+)"\]', live)))
        attributes[attr] = values

    # Attributes the behaviour hangs off are invisible to the CSS scan above:
    # a drawer opens from data-modal-open, which nothing styles. Taking every
    # data-* the script touches would drag in the showcase's own playground
    # controls, so these are the ones design.md documents AND the script or
    # stylesheet actually uses — a name has to be both to count.
    documented = set(re.findall(r"(data-[\w-]+)", design_md))
    used = set(re.findall(r"\[(data-[\w-]+)", script + live)) | set(
        re.findall(r"""['"](data-[\w-]+)['"]""", script))
    for attr in sorted(documented & used):
        attributes.setdefault(attr, [])

    by_group = OrderedDict()
    for cls in kit:
        by_group.setdefault(groups.get(cls, "misc"), []).append(cls)

    return {
        "$comment": "GENERATED by tools/build-packages.py — do not edit by hand.",
        "source": "designmd/components.css",
        "counts": {
            "classes": len(kit),
            "groups": len(by_group),
            "attributes": len(attributes),
            "behaviourHooks": len(hooks),
            "showcaseOnly": len(showcase),
            "tooling": len(tooling),
        },
        "rules": [
            "Use only classes listed in `classes`. If the kit lacks something, say so — do not invent a class.",
            "Never use a class from `showcaseOnly`: those are example.html's own chrome, not part of the kit.",
            "Some components are attribute-driven, not classes — see `attributes`. A tooltip is [data-tooltip], not .tooltip.",
            "`behaviourHooks` carry no CSS but are correct to use — the delegated script finds its targets by them.",
            "Reference semantic tokens (--color-bg, --type-h1), never primitives (--color-blue-500).",
            "Do not author component CSS in a prototype. Add the variant to components.css and re-inline.",
        ],
        "classes": by_group,
        "attributes": attributes,
        "behaviourHooks": hooks,
        "showcaseOnly": showcase,
        "tooling": sorted(tooling),
    }


# -------------------------------------------------------------- bundle.css


def build_bundle_css(tokens_css, semantic_css, components_css):
    """components.css plus what the artifact page cannot generate for itself.

    The page writes its own tokens.css from tokens.json. That covers the token
    families, but NOT: the motion family (the schema has no shape for it), the
    raw type primitives, or the `--type-*` font shorthands, which live in
    semantic.css and never reach tokens.json because the type family is
    expressed there as font styles instead. components.css leans on all three,
    so the bridge supplies exactly those — without the shorthands every piece
    of text in a preview falls back to the browser default.
    """
    keep = []
    for line in tokens_css.split("\n"):
        m = re.match(r"\s*(--[\w-]+)\s*:\s*([^;]+);", line)
        if not m:
            continue
        name = m.group(1)
        if name[2:].startswith(MOTION_PREFIXES) or name[2:].startswith(TYPE_PREFIXES):
            keep.append(f"  {name}: {m.group(2).strip()};")

    for name, value, _ in parse_declarations(semantic_css, ":root"):
        if name.startswith("--type-"):
            keep.append(f"  {name}: {value};")

    keyframes = re.findall(r"(@keyframes\s+[\w-]+\s*\{(?:[^{}]|\{[^{}]*\})*\})", tokens_css)

    bridge = [
        "/* ---------------------------------------------------------------",
        " * Bridge — GENERATED by tools/build-packages.py.",
        " *",
        " * The Design System page generates tokens.css from tokens.json, which",
        " * has no shape for motion and does not carry the raw type primitives.",
        " * components.css uses both, so they are supplied here. Everything else",
        " * comes from the generated tokens.css.",
        " * --------------------------------------------------------------- */",
        ":root {",
        *keep,
        "}",
        "",
        *keyframes,
        "",
    ]
    return "\n".join(bridge) + "\n" + components_css


# ----------------------------------------------------- universal entry points


GENERATED = "<!-- GENERATED by tools/build-packages.py from AGENTS.md — do not edit. -->"


def slice_recipes(recipes_html):
    """The marked blocks of recipes.html, in order.

    An inventory is a dictionary, not a grammar: a reader who has the class
    names still cannot tell that .drawer-overlay wraps .drawer, that a drawer
    borrows the modal's header, or that it opens from data-modal-open. These
    blocks are that grammar, and because they live in a real page that
    lint.py checks, they cannot quietly go stale.
    """
    out = []
    for m in re.finditer(r"<!-- recipe: (.+?) -->\n(.*?)<!-- /recipe -->",
                         recipes_html, re.S):
        body = m.group(2).strip("\n").rstrip()
        out.append((m.group(1).strip(), body))
    return out


def check_recipes(recipes, kit_classes, icon_slugs):
    """Every class and slug a recipe shows must really exist.

    lint.py checks recipes.html as a page, but some blocks are commented
    examples — a page skeleton cannot be live inside itself — and a comment is
    not markup, so the linter rightly skips them. Those are exactly the blocks
    an agent copies verbatim, so they are checked here instead. A recipe that
    teaches a class nothing defines is worse than no recipe.
    """
    problems = []
    for name, body in recipes:
        for m in re.finditer(r'class="([^"$]*)"', body):
            for cls in m.group(1).split():
                if re.fullmatch(r"[a-z][\w-]*", cls) and cls not in kit_classes:
                    problems.append(f"recipe {name!r}: .{cls} is not a kit class")
        for slug in re.findall(r'href="#([\w-]+)"', body):
            if slug not in icon_slugs:
                problems.append(f"recipe {name!r}: #{slug} is not in the sprite")
    return sorted(set(problems))


def build_llms_full(agents_md, kit, tokens, recipes, icon_slugs):
    """AGENTS.md plus the whole inventory, as one file you can paste anywhere.

    Every entry point so far assumes a filesystem. A model working in a chat
    window has none: it cannot open kit.json, so it guesses class names, which
    is the failure this system exists to prevent. This is the answer to "what
    do I paste" — the rules and the complete inventory, around 5k tokens.
    """
    out = [agents_md.rstrip(), "", "---", "",
           "# Recipes",
           "",
           "Minimal correct markup, one block per component. Copy these rather than",
           "inferring structure from class names. Every block is checked by lint.py.",
           ""]
    for name, body in recipes:
        out += [f"## {name}", "", "```html", body, "```", ""]

    out += ["---", "",
            "# Complete inventory",
           "",
           "Generated from the stylesheets. Everything the kit defines is below; if a",
           "name is not here, it does not exist.",
           ""]

    out.append(f"## Classes ({kit['counts']['classes']})")
    out.append("")
    for group, classes in kit["classes"].items():
        out.append(f"**{group}** — " + " · ".join("." + c for c in classes))
        out.append("")

    if kit.get("attributes"):
        out += ["## Attribute-driven components", "",
                "Not every component is a class.", ""]
        for attr, values in kit["attributes"].items():
            vals = f" — values: {', '.join(values)}" if values else ""
            out.append(f"- `[{attr}]`{vals}")
        out.append("")

    if kit.get("behaviourHooks"):
        out += ["## Behaviour hooks", "",
                "No CSS of their own, but the delegated script finds its targets by them.",
                "", " · ".join("." + c for c in kit["behaviourHooks"]), ""]

    out += ["## Tokens", "",
            "Reference the semantic aliases. The palette ramps are listed so you can",
            "recognise one and avoid writing it directly.", ""]
    for family, block in tokens.items():
        if not (isinstance(block, dict) and "tokens" in block):
            continue
        names = [t["name"] for t in block["tokens"]]
        out.append(f"**{family}** ({len(names)}) — " + ", ".join(f"`--{n}`" for n in names))
        out.append("")

    styles = tokens.get("type", {}).get("groups", [{}])[0].get("styles", [])
    if styles:
        out += [f"**type** ({len(styles)} roles, use as `font: var(--type-NAME)`) — "
                + ", ".join(f"`--type-{s['name']}`" for s in styles), ""]

    if icon_slugs:
        out += [f"## Icon slugs ({len(icon_slugs)})", "",
                "Every id in the sprite. `<svg class=\"icon\"><use href=\"#SLUG\" /></svg>`.",
                "A slug not listed here renders blank, silently.", "",
                ", ".join(f"`{s}`" for s in icon_slugs), ""]

    if kit.get("showcaseOnly"):
        out += ["## Never use these", "",
                f"{len(kit['showcaseOnly'])} classes that example.html styles in its own",
                "`<style>` block and nowhere else. They look like kit classes in markup.",
                "", " · ".join("." + c for c in kit["showcaseOnly"]), ""]

    return "\n".join(out) + "\n"


def build_llms_txt():
    """The llms.txt index — a short map for a tool that fetches one file."""
    return """# Icarus Prototype Design System

> Plain HTML/CSS for prototyping the Operationalize app. An extension of Picasso,
> Toptal's production React system, re-expressed as three stylesheets a browser
> loads directly — no React, no build step. Every token is Picasso's name and
> value, or is marked `extension` with a reason.

Start with AGENTS.md. Never invent a class: if it is not in dist/kit.json, it
does not exist, and a class nothing defines renders as nothing.

## Docs

- [AGENTS.md](AGENTS.md): the rules, the traps, and how to build and check a prototype. Read first.
- [llms-full.txt](llms-full.txt): the rules plus the complete class and token inventory, in one file. Paste this if you have no filesystem.
- [recipes.html](recipes.html): minimal correct markup, one block per component. Copy from here rather than inferring structure from class names.
- [design.md](design.md): the full written system, ~16k tokens. Read a section, not the file.
- [README.md](README.md): what this is and how the three layers fit together.

## Machine-readable

- [dist/kit.json](dist/kit.json): every class, grouped; the attribute-driven components; the behaviour hooks; and the showcase-only classes to reject.
- [dist/tokens.json](dist/tokens.json): every token with its value and a usage note, light and dark.
- [dist/bundle.css](dist/bundle.css): the stylesheet, with the bridge a generated tokens.css cannot supply.

## Optional

- [starter/index.html](starter/index.html): a working skeleton that lints clean. Copy it rather than assembling one.
- [lint.py](lint.py): checks a prototype and exits non-zero on errors.
- [figma-map.json](figma-map.json): per component, the Picasso React component, its import, and the Storybook story id.
"""


def build_tool_files(agents_md):
    """Copies for tools that do not read AGENTS.md.

    Generated rather than hand-kept, because four hand-maintained copies of one
    guide is four chances to disagree with it. Regenerating is the only way to
    change them, and --check fails when they fall behind.
    """
    body = agents_md.rstrip()
    return {
        ".github/copilot-instructions.md": f"{GENERATED}\n\n{body}\n",
        ".cursor/rules/designmd.mdc": (
            "---\n"
            "description: How to build prototypes with the designmd design system\n"
            "alwaysApply: true\n"
            "---\n\n"
            f"{GENERATED}\n\n{body}\n"
        ),
        ".windsurfrules": f"{GENERATED}\n\n{body}\n",
        ".clinerules": f"{GENERATED}\n\n{body}\n",
    }


# -------------------------------------------------------------------- main


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail if dist/ is out of date")
    args = ap.parse_args()

    tokens_css = (ROOT / "tokens.css").read_text()
    semantic_css = (ROOT / "semantic.css").read_text()
    components_css = (ROOT / "components.css").read_text()
    example_html = (ROOT / "example.html").read_text()
    design_md = (ROOT / "design.md").read_text()
    recipes_html = (ROOT / "recipes.html").read_text() if (ROOT / "recipes.html").exists() else ""
    icons_svg = (ROOT / "icons.svg").read_text() if (ROOT / "icons.svg").exists() else ""
    other_css = "".join(
        (ROOT / f).read_text()
        for f in ["devtools.css", "plugins.css", "review.css", "versions.css"]
        if (ROOT / f).exists()
    )

    primitives = parse_declarations(tokens_css)
    semantic_light = parse_declarations(semantic_css, ":root")
    semantic_dark = parse_declarations(semantic_css, '[data-theme="dark"]')

    table = {n: v for n, v, _ in primitives}
    for n, v, _ in semantic_light:
        table.setdefault(n, v)

    outputs = {
        "tokens.json": json.dumps(
            build_tokens_json(primitives, semantic_light, semantic_dark, table), indent=2
        )
        + "\n",
        "kit.json": json.dumps(
            build_kit_json(components_css, semantic_css, example_html, other_css, design_md), indent=2
        )
        + "\n",
        "bundle.css": build_bundle_css(tokens_css, semantic_css, components_css),
    }

    tk = json.loads(outputs["tokens.json"])
    kit = json.loads(outputs["kit.json"])

    # Entry points live at the repo root, not in dist/, because that is where
    # each tool looks for them.
    agents_md = (ROOT / "AGENTS.md").read_text()
    recipes = slice_recipes(recipes_html)
    icon_slugs = sorted(set(re.findall(r'<symbol[^>]*id="(i-[^"]+)"', icons_svg)))

    kit_classes = {c for g in kit["classes"].values() for c in g}
    kit_classes |= set(kit.get("behaviourHooks", []))
    problems = check_recipes(recipes, kit_classes, set(icon_slugs))
    if problems:
        print("recipes.html teaches something that does not exist:", file=sys.stderr)
        for p_ in problems:
            print("  " + p_, file=sys.stderr)
        return 1
    root_outputs = {
        "llms.txt": build_llms_txt(),
        "llms-full.txt": build_llms_full(agents_md, kit, tk, recipes, icon_slugs),
        **build_tool_files(agents_md),
    }

    if args.check:
        stale = [f"dist/{n}" for n, body in outputs.items()
                 if not (DIST / n).exists() or (DIST / n).read_text() != body]
        stale += [n for n, body in root_outputs.items()
                  if not (ROOT / n).exists() or (ROOT / n).read_text() != body]
        if stale:
            print("out of date: " + ", ".join(stale), file=sys.stderr)
            print("run: python3 tools/build-packages.py", file=sys.stderr)
            return 1
        print("dist/ and the entry points are current")
        return 0

    DIST.mkdir(exist_ok=True)
    for name, body in outputs.items():
        (DIST / name).write_text(body)
    for name, body in root_outputs.items():
        target = ROOT / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body)
    counted = sum(len(v["tokens"]) for k, v in tk.items() if isinstance(v, dict) and "tokens" in v)
    styles = len(tk["type"]["groups"][0]["styles"])
    print(f"dist/tokens.json   {counted} tokens across "
          f"{sum(1 for v in tk.values() if isinstance(v, dict) and 'tokens' in v)} families, "
          f"{styles} text styles")
    print(f"dist/kit.json      {kit['counts']['classes']} classes, "
          f"{kit['counts']['showcaseOnly']} showcase-only excluded")
    print(f"dist/bundle.css    {len(outputs['bundle.css']):,} bytes")
    full = root_outputs["llms-full.txt"]
    print(f"llms-full.txt      {len(full):,} bytes  (~{len(full)//4:,} tokens — pasteable)")
    print("entry points       " + ", ".join(sorted(root_outputs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
