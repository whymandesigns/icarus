# Icarus — agent guide

HTML prototypes for the **Operationalize** app, built from a design system called
**designmd**. If you are writing UI here, read this first — it is short.

**Paths below are written from the root of this folder** — the one holding `tokens.css`,
`lint.py` and `dist/`. That is true however you got it:

```
# cloned on its own (github.com/whymandesigns/icarus)
icarus/            ← you are here; prototypes live wherever you like
```
```
# inside Toptal's working layout, two sibling checkouts
icarus/
├── designmd/      ← you are here   (repo: whymandesigns/icarus)
└── features/      the prototypes   (repo: whymandesigns/opz-prototypes)
```

Only one path ever needs changing: the three `<link>` hrefs at the top of a prototype
must point at this folder. Get them wrong and the page renders as bare HTML with no
error — `lint.py` is what catches it.

## The rules

1. **Never invent a class.** Every class must be in `designmd/dist/kit.json`. A class
   nothing defines renders as nothing, silently. If the kit has no component for what
   you need, say so rather than approximating it.
2. **Never copy markup out of `designmd/example.html`.** 88 of the classes in that file
   are the showcase's own chrome, styled in its `<style>` block and nowhere else. They
   are indistinguishable from kit classes in the markup. `.btn-cta-icon` is one, and it
   is already shipped in a prototype that way. `kit.json` lists them under
   `showcaseOnly`; the linter rejects them.
3. **Semantic tokens, never primitives.** `var(--color-bg)`, `var(--type-h1)`,
   `var(--spacing-4)` — not `var(--color-blue-500)`. Re-pointing an alias is how a theme
   changes; a primitive reference defeats that. The one sanctioned exception is
   `--color-graphite-800`, the top bar chrome, which does not change with the theme.
4. **One `.btn-primary` per page.** Every other call to action is `.btn-secondary`. Green
   is both the primary CTA and the success colour, so two of them means neither reads as
   the action.
5. **Don't write component CSS in a prototype.** If a variant is missing, add it to
   `designmd/components.css` so the next screen inherits it, then re-inline.

## Start here

Open `starter/index.html` — it renders as it sits and is lint-clean. Copy it to
wherever your prototype lives, repoint its three stylesheet `<link>`s at this folder,
then, run from here:

```bash
python3 lint.py   <path-to-your-prototype>.html    # before you call it done
python3 inline.py <path-to-your-prototype>.html    # bake before sharing
```

`inline.py` folds the CSS, the icon sprite and the fonts into the file, so what you
share has no external dependencies and does not care where it sits.

In Toptal's working layout a prototype is `features/<kebab-name>/index.html` — always
that shape, always `index.html`. On your own, put it where you like.

## Where things are

| | |
|---|---|
| `designmd/dist/kit.json` | **the inventory** — 368 classes grouped, the attribute-driven components, and the showcase-only classes to reject. Read this to find a class. |
| `designmd/starter/` | a working skeleton: top bar, page head, table, modal, search. |
| `designmd/recipes.html` | **minimal correct markup, one block per component.** Class names alone do not tell you that `.drawer-overlay` wraps `.drawer`, or that a drawer borrows the modal's header. Copy from here. |
| `designmd/lint.py` | checks a prototype. Exit 1 on errors. |
| `designmd/design.md` | the full written system, ~15k tokens. Read sections, not the whole file. |
| `designmd/example.html` | the showcase — browse it in a browser, don't copy from it (rule 2). |
| `designmd/llms-full.txt` | this guide plus the complete class and token inventory, ~4k tokens. **Paste this if you have no filesystem.** |
| `designmd/llms.txt` | a short index of everything above, for a tool that fetches one file. |
| `designmd/tools/build-packages.py` | regenerates `dist/` and the entry points after a stylesheet change. |

If your tool reads its own rules file, it already has this guide: `.github/copilot-instructions.md`,
`.cursor/rules/designmd.mdc`, `.windsurfrules` and `.clinerules` are generated copies of it, so
they cannot drift. Edit `AGENTS.md` and regenerate; never edit a copy.

## Things that fail silently

- **Icons.** The three stylesheets do not carry the sprite — only `inline.py` injects it,
  so `<use href="#i-…">` renders blank until you bake. The starter fetches it at dev time
  to cover the gap. Slugs live in `designmd/icons.svg`; the linter checks them.
- **Phosphor is retired.** `<i class="ph ph-x">` renders nothing. Some CSS comments still
  show it; they are stale.
- **The `example.html` script block.** Modals, drawers, dropdowns, tabs and the sheet get
  their behaviour from a delegated block there. Do not copy it whole: it is 2,286 lines
  and its tail renders the showcase's own palette swatches against elements no prototype
  has, which throws and kills every handler after it. Take the handlers you need.
- **`.topbar-title` shows nothing on a wide screen.** It is the *collapsed* title; the top
  bar is a container query that reveals it below 768px. Same for `.topbar-menu` and
  `.topbar-cta`. Put `.topbar-menu` and `.topbar-title` in the markup from the start —
  they are invisible until the bar collapses. `.topbar-cta` is the exception: add it only
  on a page with **no** page head, because nothing hides `.page-head-actions` when the bar
  collapses, so carrying both puts two primary CTAs on screen below 768px.
- **Some classes carry no CSS and are still right.** `.dropdown-trigger` is how the
  delegated script finds a dropdown's button; nothing styles it. `kit.json` lists these
  under `behaviourHooks`, beside `attributes` for the components driven by an attribute
  instead — a tooltip is `[data-tooltip]`, never `.tooltip`.

## Upstream

**Picasso is the source of truth** — Toptal's production React system
([repo](https://github.com/toptal/picasso) ·
[Storybook](https://toptal.github.io/picasso/)). designmd re-expresses its foundations as
plain CSS so a screen can exist in hours. Every token is Picasso's name and value, or is
marked `extension` with a reason in its own comment. Where the two disagree, Picasso is
right and designmd has a bug. `designmd/figma-map.json` carries the Storybook `storyId`
and React mapping per component.

Note the Storybook is a client-side build: `iframe.html?id=anything` returns 200, so a
request succeeding proves nothing about a story existing.

## Two consumers, one generator

designmd feeds Claude Code (this repo) and a published Design System artifact for Claude
Design. Both are generated by `tools/build-packages.py` from the three stylesheets —
`dist/kit.json`, `dist/tokens.json`, `dist/bundle.css`. They were hand-built once and
drifted badly. After changing a stylesheet, re-run it; `--check` fails when `dist/` is
stale.
