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
must point at this folder, in this order —

```html
<link rel="stylesheet" href="PATH/TO/tokens.css" />      <!-- primitives -->
<link rel="stylesheet" href="PATH/TO/semantic.css" />    <!-- aliases + reset -->
<link rel="stylesheet" href="PATH/TO/components.css" />  <!-- the classes -->
```

Get them wrong and the page renders as bare HTML with no error — `lint.py` is what
catches it.

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
5. **Copy is part of the system too.** `UXCopy.md` decides how a label, an
   error or a date is written. What a thing is called, and how the product
   behaves, come from the **test oracle** — `topteam/test-oracle/`, the
   Operationalize behaviour spec, a read-only clone beside `icarus/` in Toptal's
   working layout; its glossary is §7 of `00-system-overview.md`. Ask it before
   naming anything or stating a product rule, and cite the rule ID.
   `features/CONTEXT.md` layers the Operating Framework's policy and the
   prototype inventory on top, and says how to query the oracle. A screen with
   invented wording drifts the same way invented CSS does, and is harder to
   spot.
6. **Don't write component CSS in a prototype.** If a variant is missing, add it to
   `designmd/components.css` so the next screen inherits it, then re-inline.
7. **Build light only — dark theme is parked.** `[data-theme="dark"]` exists in the
   stylesheet, but it is being rebuilt on Picasso's own dark values. Don't set it,
   don't write `prefers-color-scheme` blocks, and don't add dark overrides for a new
   token. Anything written for it now gets thrown away.
8. **A full-window screen is `<div class="app-shell is-fullscreen">`, and that is all.**
   No `height`, `min-height`, `flex` or `overflow` in the page, and no
   `html, body { height: 100% }` reset — the variant bounds the body and
   `.app-shell-main` scrolls on its own. Older prototypes carry four hand-written
   lines because the variant did not exist yet; they are not the pattern to copy.

## Start here

**Don't write the shell by hand — duplicate `template/`.** It is a real prototype
that lints and inlines, carrying the top bar, side nav, page head and the delegated
handlers the kit does not ship. Run from here:

```bash
python3 tools/new-prototype.py <kebab-name> --title "<Title>" --nav "<Section>"
# or, for a brand-new sidenav entry:
python3 tools/new-prototype.py <kebab-name> --title "<Title>" --new-nav "<Label>" --nav-icon i-<slug>
```

That copies `template/index.html` into `features/<kebab-name>/index.html` (pass
`--into <path>` elsewhere), marks the nav, registers a card in `features/index.html`
and adds a `status.json` entry. Then build the feature into the content region,
from the classes in `dist/kit.json`, and run:

A prototype that predates the current system carries a quarantine marker in its
`<head>`, and `lint.py` prints its errors without failing on them:

```html
<!-- designmd:legacy — frozen on the --ic-* vocabulary, so inline.py cannot
     refresh it and no kit change reaches it. tools/migrate-ic-tokens.py is
     the way out; see data/ic-token-map.json. Remove this line once it lints
     clean. -->
```

`data/ic-token-map.json` classifies every legacy token four ways, because a
migration is not a rename: `same` is identical in value, `shifts` is a value the
system deliberately changed, `literals` is a role the system models no token for
at all — the `var()` goes and its value stays — and `none` needs a human. The
`--ic-*` vocabulary is now fully retired: where no current step survived, the
entry names the nearest surviving one and records the CIE ΔE, so a reviewer can
see at a glance which substitutions are invisible and which are a real change.
Two whole ramps had no survivor and fold onto a neighbour — orange onto yellow,
since warning is yellow here, and cyan onto blue, which `tokens.css` was already
part-way through. Nothing maps onto `zinc`: it is dark-theme internal and must
never appear in a prototype.

That is the whole point of the marker: **anything without one has to pass**, so
`python3 lint.py features/*/index.html` stays a real gate for new work. The list
can only shrink — removing the line is how a prototype says it has been migrated,
and `--strict` ignores markers entirely. Never add one to a new screen.

Across many files, use `--report` instead. The per-file output is sorted by line
number, which is right for one screen and useless for fifty: the classes that render
as nothing end up interleaved with spacing nits, and nobody reads to the end of four
thousand lines. `--report` ranks the same findings by code and then by subject, which
says two things the per-file view structurally cannot — what is broken on screen right
now, and which hand-written class has been written often enough to belong in
`components.css`:

```bash
python3 lint.py ../features/*/index.html --report          # the whole estate, ranked
python3 lint.py ../features/*/index.html --report --top 30 # longer lists
```

It splits findings into **BROKEN ON SCREEN** (invented classes, showcase classes, dead
icons and tokens, Phosphor — all of which render as nothing) and **DRIFT** (correct on
screen, wrong in the system). Then it rolls local classes up into component families,
because thirteen `.sv-*` classes hand-written in five files is one missing component,
not thirteen mistakes. State modifiers (`is-`, `has-`) are left out of that roll-up:
`.cal-day.is-today` belongs to the calendar, not to the kit.

```bash
python3 lint.py   <path-to-your-prototype>.html    # before you call it done
python3 tools/new-prototype.py <kebab-name> --thumb  # 1280x800 card image, re-runnable
python3 inline.py <path-to-your-prototype>.html    # bake before sharing
```

A screen that already exists but is not listed — built before the scaffolder, or
made with `--no-register` — is registered without being touched:

```bash
python3 tools/new-prototype.py <kebab-name> --register-only --title "<Title>" --desc "<one line>"
```

Do not re-run the scaffolder over it to get the card: that copies the template
on top of the prototype.

A hand-written skeleton drifts from the system the moment the system moves; a
duplicated template cannot. If the template lacks something every screen should
have, fix `template/index.html` — never only your copy.

`inline.py` folds the CSS, the icon sprite and the fonts into the file, so what you
share has no external dependencies and does not care where it sits.

In Toptal's working layout a prototype is `features/<kebab-name>/index.html` — always
that shape, always `index.html`. On your own, put it where you like.

## Where things are

| | |
|---|---|
| `designmd/dist/kit.json` | **the inventory** — every class grouped, the attribute-driven components, and the showcase-only classes to reject. Read this to find a class. |
| `designmd/template/index.html` | **the shell every prototype starts as** — top bar, side nav, page head, and the delegated handlers the kit does not ship. Duplicate it with `tools/new-prototype.py`; edit it when the shell itself should change. |
| `designmd/tools/new-prototype.py` | duplicates the template, resolves the sidenav, lists the feature. `--thumb` shoots the card image later. |
| `designmd/lint.py` | checks a prototype. Exit 1 on errors. `--report` ranks every file at once instead of listing each — see below. |
| `designmd/UXCopy.md` | **the words** — button labels, tone, dates, and which of toast / alert / modal / field error a message belongs in. Read it before writing any user-facing string. |
| `designmd/DESIGN.md` | the full written system, ~15k tokens. Read sections, not the whole file. |
| `designmd/example.html` | the showcase — browse it in a browser, don't copy from it (rule 2). |
| `designmd/llms-full.txt` | this guide, the worked markup and the complete class and token inventory, ~9k tokens. **Paste this if you have no filesystem.** |
| `designmd/llms.txt` | a short index of everything above, for a tool that fetches one file. |
| `designmd/tools/build-packages.py` | regenerates `dist/` and the entry points after a stylesheet change. |
| `designmd/tools/sync-picasso-tokens.py` | **checks the `/* picasso */` half of `tokens.css`** against the published Picasso preset. `--fix` rewrites drifted values; `--update` re-vendors `data/picasso-tokens.json`. |
| `designmd/tools/smoke_test.py` | builds a prototype from this guide's own `<link>` block and runs lint → inline → lint. Run it after changing a tool or that snippet. |

If your tool reads its own rules file, it already has this guide: `.github/copilot-instructions.md`,
`.cursor/rules/designmd.mdc`, `.windsurfrules` and `.clinerules` are generated copies of it, so
they cannot drift. Edit `AGENTS.md` and regenerate; never edit a copy.

## Things that fail silently

- **Icons.** The three stylesheets do not carry the sprite — only `inline.py` injects it,
  so `<use href="#i-…">` renders blank until you bake. To see icons while you work, use the
  dev-time fetch in the page skeleton in `DESIGN.md` §6 "The page around them". Slugs live
  in `designmd/icons.svg`; the linter checks them.
- **Phosphor is retired, and gone.** No prototype carries `<i class="ph ph-x">` any more;
  the last 1,078 were migrated on 2026-11-08. If you meet one in an old branch,
  `tools/migrate-phosphor.py` does the swap — `data/phosphor-map.json` holds all 92 glyph
  decisions, each picked by rendering the candidates rather than by matching names, which
  is how `i-brochure` turned out to be the open book and `i-estimated-delivery` the
  chequered flag. `.icon` is sized in `em` exactly as the Phosphor `<i>` was, so existing
  `font-size:` rules keep working.
  Two traps the migration hit, both worth knowing:
  - A CSS rule keyed on the **glyph name** (`.row .ph-caret-right`) loses its aim when the
    glyph moves into the `<use href>`. `.icon` is not a replacement — if two icons share
    that scope the rule now hits both. Give the element a purpose class instead.
  - An icon id built at **runtime** must still appear in the file as a literal
    `href="#i-…"`, or `inline.py` narrows the sprite and drops it. Put whole `<svg>` markup
    in the lookup table, not a bare slug.
- **The `example.html` script block.** Modals, drawers, dropdowns, tabs and the sheet get
  their behaviour from a delegated block there. Do not copy it whole: it is 2,286 lines
  and its tail renders the showcase's own palette swatches against elements no prototype
  has, which throws and kills every handler after it. Take the handlers you need.
- **`.topbar-title` shows nothing on a wide screen.** It is the *collapsed* title, and
  the bar collapses at **1024px** — the same edge as the side nav, because the hamburger
  it reveals is what opens the off-canvas rail. Same for `.topbar-menu` and
  `.topbar-cta`. Put `.topbar-menu` and `.topbar-title` in the markup from the start —
  they are invisible until the bar collapses. Carry `.topbar-cta` too — **one per CTA in
  the page head, same order, same variant** (`.btn-secondary` stays secondary). `.page-head`
  is hidden at that same 1024px edge, so exactly one of the two sets is ever on screen, and
  shipping only the primary is how a page's other actions disappear on a phone. (This used to be the opposite —
  nothing hid the page head, and carrying both showed two primary CTAs once the bar
  collapsed. That is fixed; ignore any older note saying to leave `.topbar-cta` off.)
  (The kit's own playground collapses on a *container* query at 768px instead, since
  there the bar is narrow inside a wide window and the viewport says nothing useful.
  That edge measures the bar, not the screen; it never applies to a feature prototype.)
- **The side nav is off-canvas at ≤1024px, and that needs three things.** The kit
  hides the rail and reveals `.topbar-menu` below Picasso's lg edge; the hamburger
  then has to toggle `.is-open` on the `.sidenav`. `template/index.html` ships the
  markup and the handler, so a prototype duplicated from it already works. Write the
  shell by hand and you get a hidden nav with nothing to open it.
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
right and designmd has a bug. `designmd/data/figma-map.json` carries the Storybook `storyId`
and React mapping per component.

Picasso is Toptal's *company* system, not Operationalize's: it has no Operationalize side
nav, top bar or page head, and it is not going to grow one. TopTeam builds those itself —
78 components in `front-end/src/topkit/`, and `TopBar`/`Sidebar` written from scratch
against Picasso's palette. So designmd is two layers in one file, and `tokens.css` already
labels every line with which:

| | upstream | drifts? |
|---|---|---|
| `/* picasso */` | `@toptal/picasso-tailwind` on public npm | **yes, silently** |
| `/* extension */` | none — Operationalize's own | no |

Only the first can be wrong, and it goes wrong quietly: Picasso ships a new value, nobody
re-transcribes it, and a prototype renders a colour the product retired. That is what
happened to `gray-100`. Picasso publishes those values as a Tailwind preset, so they never
needed transcribing by hand:

```bash
python3 tools/sync-picasso-tokens.py            # report
python3 tools/sync-picasso-tokens.py --check    # exit 1 if a value drifted
python3 tools/sync-picasso-tokens.py --fix      # rewrite the ones that drifted
python3 tools/sync-picasso-tokens.py --update   # re-vendor after a Picasso bump
```

It touches nothing but drifted values — the `extension` lines, the commented-out ramps and
all the prose stay byte-for-byte. Run `--check` alongside `build-packages.py --check`; run
`--fix` then `build-packages.py` when it reports drift. The preset is vendored to
`data/picasso-tokens.json` with the version it came from, so the everyday run needs neither
network nor `node_modules` — this repo has no `package.json` and does not want one.

Note the Storybook is a client-side build: `iframe.html?id=anything` returns 200, so a
request succeeding proves nothing about a story existing.

## Two consumers, one generator

designmd feeds Claude Code (this repo) and a published Design System artifact for Claude
Design. Both are generated by `tools/build-packages.py` from the three stylesheets —
`dist/kit.json`, `dist/tokens.json`, `dist/bundle.css`. They were hand-built once and
drifted badly. After changing a stylesheet, re-run it; `--check` fails when `dist/` is
stale.
