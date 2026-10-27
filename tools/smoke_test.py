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

    if problems:
        print(f"\nsmoke test: {problems} failure(s)")
        return 1
    print("\nsmoke test: the documented workflow works end to end")
    return 0


if __name__ == "__main__":
    sys.exit(main())
