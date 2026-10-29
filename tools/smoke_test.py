#!/usr/bin/env python3
"""smoke_test.py — build a prototype the way the guide says to, end to end.

`build-packages.py --check` proves the generated files are current and that
the docs name real classes. It does not prove the documented *workflow* runs,
and that is where this folder actually broke: AGENTS.md's canonical <link>
block carries trailing comments, inline.py's pattern did not allow them, and
baking a prototype copied from the guide printed "no CSS links found", exited
0, injected the sprite anyway and handed back a file that looked baked and
rendered unstyled. Nothing caught it because nothing ran the guide's own
snippet through the tools.

So this takes the <link> block out of AGENTS.md verbatim, builds a page from
it, and runs the real loop: lint → inline → lint. Edit that snippet into a
shape inline.py cannot bake and this fails.

Phase two does the same for `template/` — the shell every prototype is
duplicated from — by actually running tools/new-prototype.py. Same failure mode,
one level up: the plugin CSS moved out of the design-system style block and a
first bake stopped carrying it at all, so every freshly scaffolded prototype
shipped a launcher with `position: static`. It looked fine in any prototype old
enough to have been baked before the move, which is why nobody saw it.
"""

import pathlib
import re
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent


def fail(msg):
    print(f"  FAIL  {msg}")
    return 1


def run(script, target):
    return subprocess.run(
        [sys.executable, str(ROOT / script), str(target)],
        capture_output=True, text=True)


def link_block():
    """The three <link> tags exactly as AGENTS.md tells a reader to write them."""
    agents = (ROOT / "AGENTS.md").read_text()
    for block in re.findall(r"```html\n(.*?)```", agents, re.S):
        if "tokens.css" in block and "components.css" in block:
            return block.strip().replace("PATH/TO/", "../")
    raise SystemExit("smoke_test: no <link> block found in AGENTS.md")


PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Smoke test</title>
%s
</head>
<body>
  <main class="page">
    <div class="page-head">
      <div class="page-head-main"><h1 class="page-head-title">Smoke test</h1></div>
      <div class="page-head-actions">
        <button class="btn btn-primary">
          <svg class="icon icon-16"><use href="#i-plus"/></svg>New
        </button>
      </div>
    </div>
    <a class="list-row" href="#">
      <div>
        <p class="list-row-title">An objective</p>
        <p class="list-row-meta">Updated today</p>
      </div>
      <span class="tag tag-positive">On track</span>
    </a>
  </main>
</body>
</html>
"""


def styles(html):
    """Every <style> block's contents, joined — what the page actually styles."""
    return "\n".join(re.findall(r"<style>(.*?)</style>", html, re.S))


# What the shell is, as a contract. The docs describe this in prose in four
# places; prose cannot fail a build. Each entry is (what it is, the string that
# must appear in a scaffolded prototype) — drop a piece of the shell out of
# template/index.html and this names the piece.
SHELL_CONTRACT = [
    ("the three stylesheets, in order", 'href="../../designmd/tokens.css"'),
    ("the collapsed bar's hamburger",   'class="btn btn-icon-only btn-ghost topbar-menu"'),
    ("the collapsed bar's title",       'class="topbar-title"'),
    ("the collapsed bar's CTA",         'topbar-cta'),
    ("the off-canvas panel header",     'class="sidenav-head"'),
    ("the panel's dark wordmark",       'class="sidenav-logo"'),
    ("the panel's close hook",          'sidenav-close'),
    ("the panel's search field",        'class="input-icon input-icon-left sidenav-search"'),
    ("the full-window app shell",       'class="app-shell is-fullscreen"'),
    ("the hamburger handler",           "closest('.topbar-menu')"),
    ("the sprite fetch",                "fetch('../../designmd/icons.svg')"),
]

# Things the shell must NOT scaffold. Both were removed on purpose: a generated
# subtitle is always filler, and an icon on a scaffolded button is a guess at
# what the button will do.
SHELL_FORBIDDEN = [
    ("a page-head subtitle",            'page-head-subtitle'),
    ("an icon inside a page-head CTA",  '<svg class="btn-icon"><use href="#i-plus"/></svg>New'),
]


def template_phase():
    """Scaffold from template/ the way the guide says to, then bake it.

    The temp folder sits beside designmd/, because the template links the system
    at ../../designmd/ — the path a real prototype in features/ uses.
    """
    problems = 0
    with tempfile.TemporaryDirectory(dir=ROOT.parent) as tmp:
        r = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "new-prototype.py"), "smoke-template",
             "--title", "Smoke template", "--nav", "Initiatives", "--into", tmp],
            capture_output=True, text=True)
        proto = pathlib.Path(tmp) / "smoke-template" / "index.html"
        if r.returncode != 0 or not proto.is_file():
            return fail(f"the scaffolder did not produce a prototype:\n{r.stdout}{r.stderr}")
        print("  ok    scaffolds a prototype from template/")

        scaffold = proto.read_text()
        # Count the markup, not the string: the tabs handler in the template
        # also mentions is-active.
        active = scaffold.count('class="sidenav-item is-active"')
        if active != 1:
            problems += fail(f"the scaffold marked {active} sidenav items active, "
                             "not exactly one.")
        elif "{{" in scaffold:
            problems += fail("the scaffold still carries an unreplaced {{PLACEHOLDER}}.")
        else:
            print("  ok    sidenav resolved, no placeholders left")

        # Comments discuss what the shell deliberately leaves out, so they have
        # to come off first — otherwise the note explaining why there is no
        # page-head subtitle reads as a page-head subtitle.
        body = re.sub(r"<!--.*?-->", "", scaffold, flags=re.S)
        missing = [what for what, s in SHELL_CONTRACT if s not in body]
        present = [what for what, s in SHELL_FORBIDDEN if s in body]
        if missing:
            problems += fail("the scaffolded shell is missing: " + "; ".join(missing)
                             + ".\n        template/index.html no longer matches what "
                               "AGENTS.md and DESIGN.md describe.")
        elif present:
            problems += fail("the scaffolded shell carries what it should not: "
                             + "; ".join(present) + ".")
        else:
            print(f"  ok    shell carries all {len(SHELL_CONTRACT)} documented parts")

        r = run("lint.py", proto)
        if r.returncode != 0:
            problems += fail(f"the scaffold does not lint clean while linked:\n"
                             f"{r.stdout}{r.stderr}")
        else:
            print("  ok    scaffold lints clean while linked")

        r = run("inline.py", proto)
        if r.returncode != 0:
            problems += fail(f"inline.py refused the scaffold:\n{r.stdout}{r.stderr}")
        else:
            print("  ok    scaffold bakes")

        baked = proto.read_text()
        if ".pg-fab" not in styles(baked):
            problems += fail("the baked scaffold carries the plugin launcher's markup "
                             "but none of its CSS — the launcher renders as a "
                             "statically positioned button in the page flow.")
        else:
            print("  ok    launcher and review-bar CSS baked in")

        run("inline.py", proto)
        if proto.read_text() != baked:
            problems += fail("baking twice changed the file — inline.py is not "
                             "idempotent on a scaffold.")
        else:
            print("  ok    baking is idempotent")

        r = run("lint.py", proto)
        if r.returncode != 0:
            problems += fail(f"the baked scaffold does not lint clean:\n"
                             f"{r.stdout}{r.stderr}")
        else:
            print("  ok    scaffold lints clean once baked")
    return problems


def main():
    problems = 0
    with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
        proto = pathlib.Path(tmp) / "index.html"
        proto.write_text(PAGE % link_block())

        r = run("lint.py", proto)
        if r.returncode != 0:
            problems += fail("a prototype built from the documented classes does "
                             f"not lint clean:\n{r.stdout}{r.stderr}")
        else:
            print("  ok    lints clean while linked")

        r = run("inline.py", proto)
        if r.returncode != 0:
            problems += fail(f"inline.py refused the guide's own snippet:\n"
                             f"{r.stdout}{r.stderr}")
        elif "no CSS links found" in r.stdout:
            problems += fail("inline.py did not recognise the <link> block in "
                             "AGENTS.md — a prototype copied from the guide "
                             "would ship unstyled.")
        else:
            print("  ok    bakes using the <link> block from AGENTS.md")

        baked = proto.read_text()
        if re.search(r'<link[^>]*rel="stylesheet"', baked):
            problems += fail("a baked prototype still links stylesheets — it is "
                             "not self-contained.")
        elif "<style>" not in baked:
            problems += fail("a baked prototype carries no inline CSS.")
        else:
            print("  ok    baked file is self-contained")

        if 'id="i-plus"' not in baked:
            problems += fail("the icon sprite was not injected — every <use> "
                             "renders blank.")
        else:
            print("  ok    icon sprite injected")

        r = run("lint.py", proto)
        if r.returncode != 0:
            problems += fail(f"the baked prototype does not lint clean:\n"
                             f"{r.stdout}{r.stderr}")
        else:
            print("  ok    lints clean once baked")

    problems += template_phase()

    if problems:
        print(f"\nsmoke test: {problems} failure(s)")
        return 1
    print("\nsmoke test: the documented workflow works end to end")
    return 0


if __name__ == "__main__":
    sys.exit(main())
