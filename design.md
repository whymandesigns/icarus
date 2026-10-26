# Icarus — design.md

> Source of truth for vibe prototyping. Paste this file (or the **Vibe prompt** section) into your LLM context when generating new HTML prototypes. Every prototype links three stylesheets in order: `tokens.css` → `semantic.css` → `components.css`.

---

## Architecture

Three layers. Don't skip them.

```
┌──────────────────────────────────────────────────────────────┐
│  tokens.css        Primitives — palette, scale, raw values   │  ← never reference directly in components
│                    (--color-*, --text-*, --spacing-*)         │
├──────────────────────────────────────────────────────────────┤
│  semantic.css      Intent aliases — bg, text, brand, danger  │  ← what components and prototypes USE
│                    (--color-bg, --color-text, --type-h1)     │
├──────────────────────────────────────────────────────────────┤
│  components.css    Reusable classes — .btn, .card, .input    │  ← composed of semantic tokens only
└──────────────────────────────────────────────────────────────┘
            │
            ▼
       prototype.html      ← consumes components + semantic tokens
```

**Rule:** components and prototypes reference **semantic** aliases (`--color-bg`, `--type-h1`), never primitives (`--color-blue-500`). This makes theme swaps and brand changes one-file edits.

---

## 1. Principles

- **Calm, not loud.** Generous whitespace. Type does hierarchy, not boxes.
- **Three color roles, kept distinct:**
  - **Brand mark = Blue-500** (`--color-accent`). The logo color. White-on-graphite lockup in the topbar. Rarely surfaces elsewhere in the UI.
  - **Primary CTA = Green-500** (`--color-brand`). The attention-grabbing action color on dense data pages. Used **diligently** — ideally one `btn-primary` per page; every other CTA is `.btn-secondary`. Never decorative.
  - **Chrome = Graphite-800**. The dark topbar background that the white logo sits on. Used directly via `var(--color-graphite-800)` because it's the one place a raw palette reference is intentional.
- **Status colors are scarce.** Red/yellow/green only signal state — never decoration. (Note: green also doubles as the primary CTA color, which is why CTA placement is so disciplined.)
- **Motion is functional.** `--duration-fast` (120ms) for state, `--duration-base` (200ms) for entry/exit. Nothing decorative.
- **Every prototype ships with the review bar.** `inline.py` bakes `review.css` + `review.js` into every prototype it touches. Click the circle button bottom-right on any prototype (or open it with `?review=1`) and a bar appears at the bottom: **Edit text** (retype any copy in place), **Comment** (click an element, leave a note — numbered pins + a side panel) and **Spotlight** (dim everything outside a dragged rectangle). Comments and edits are saved to `feedback.json` next to the prototype when it runs on `tools/serve.mjs`. This is the canonical way to review a prototype and hand the notes to an LLM — see §7 "Review bar" and `review-bar.html`.
- **Copy the `example.html` `<script>` block** into every new prototype — it carries the universal handlers (modals, drawers, dropdowns, tabs, toasts, …).

---

## 2. Color

### Primitive palette (`tokens.css`)

Every token is either **Picasso's**, name and value verbatim, or an **extension**
designmd adds — and each declaration in `tokens.css` says which. 93 Picasso, 77
extensions. If a prototype uses an extension, that colour has no Tailwind class
waiting for it in production; reach for a Picasso one unless you mean it.

Picasso's palette is deliberately small: 30 colours, with three graphites, three
reds, three yellows and a single purple.

| Ramp | Picasso has | Role |
|---|---|---|
| `gray` | 50–600 | Neutrals for surfaces, borders, text |
| `graphite` | 700, 800, 900 | Dark chrome — topbar background, inverse text |
| `blue` | 100, 150, 400, 500, 600, 700 | **Brand mark** (logo, `--color-accent`), focus rings, links, info |
| `green` | 100, 150, 500, 600, 700 | **Primary CTA** (`--color-brand`) — and success |
| `red` | 100, 150, 500 | Danger / destructive |
| `yellow` | 100, 150, 500 | Warning |
| `purple` | 500 | Reserved |
| `zinc` | *none* | Dark-theme neutrals — entirely a designmd extension, and **hidden from the palette gallery**. It exists only to back `[data-theme="dark"]`; never reach for it in a prototype. Picasso ships real dark values, and rebuilding dark mode on those retires this ramp. |

Extensions are down to **21**. 36 unreferenced shades — the mid-ramps of red, yellow,
blue and purple — are commented out in `tokens.css` rather than deleted, so a shade can
come back if a prototype needs it; `purple-100` and `-150` already have. What survives:

| Extension | Why it stays |
|---|---|
| `gray-700` | `--color-text-muted`. Picasso's darkest text grey is 3.56:1 on white, below AA |
| `purple-100`, `-150` | kept deliberately; Picasso has only `purple-500`, so neither has a class |
| `yellow-700` | `.badge-warning` text — warning copy needs contrast Picasso's yellow-500 cannot give |
| `graphite-750` | `--color-icon` and the active segmented item |
| `graphite-300`, `green-200/300/400/800`, `zinc-500…900` | the dark theme, which is designmd's own |
| `blue/green/red-500-hover` and `-active` | Picasso's Button states, which it hardcodes as hex |

Nine of the nineteen exist only because dark mode does. Rebuilding it on Picasso's own
dark values would retire them in one move.

> **If you remember the old names.** `gray-100`→`gray-50`, `gray-150`→`gray-100`,
> `graphite-500`→`graphite-700`, `graphite-600/700`→`graphite-725/750`, and the
> cyan ramp is gone: `cyan-500` was always Picasso's `blue-400`. The old
> `blue-400` was not Picasso's; it became `blue-450` and is now commented out, since nothing used it.

### Semantic aliases (`semantic.css`) — **use these in prototypes**

Picasso has no semantic layer — these roles are designmd's, mapped onto Picasso
primitives so a prototype reads by intent and still translates to a real class.

| Token | Light | Dark |
|---|---|---|
| `--color-bg` | gray-50 | zinc-900 |
| `--color-surface` | white | zinc-800 |
| `--color-surface-muted` | gray-100 | zinc-700 |
| `--color-surface-sunken` | gray-200 | zinc-900 |
| `--color-border` | gray-200 | zinc-600 |
| `--color-border-strong` | gray-300 | zinc-500 |
| `--color-border-focus` | blue-500 | — |
| `--color-text` | graphite-900 | gray-50 |
| `--color-text-muted` | gray-700 | gray-400 |
| `--color-text-subtle` | gray-500 | gray-600 |
| `--color-text-inverse` | white | zinc-900 |
| `--color-text-link` | blue-500 | — |
| `--color-icon` | graphite-750 | graphite-300 |
| `--color-brand` / `-hover` / `-active` / `-subtle` | green-500 / #27D496 / #00A96C / green-100 | green-400 / 300 / 200 / 800 |
| `--color-accent` / `-hover` / `-active` / `-subtle` | blue-500 / #4269D6 / #1A41AB / blue-100 | — |
| `--color-success` / `-subtle` | green-500 / green-100 | — |
| `--color-warning` / `-subtle` | yellow-500 / yellow-100 | — |
| `--color-danger` / `-hover` / `-active` / `-subtle` | red-500 / #DB466B / #B01F43 / red-100 | — |

**Hover goes lighter, active goes darker.** Picasso's Button hardcodes those six values rather than using palette shades, so designmd carries them as `--color-{blue,green,red}-500-{hover,active}`. designmd used to darken on hover, which was backwards from the product.

Two aliases point at extensions on purpose. `--color-text-muted` is gray-700 because Picasso's darkest text grey, gray-600, is 3.56:1 on white — below AA for body text; gray-700 is 6.04:1. `--color-icon` is designmd's own call: Picasso icons carry no colour at all, they inherit `currentColor`.
| `--color-info` / `-subtle` | blue-400 / blue-100 | — |

Switch theme: `<html data-theme="dark">`.

---

## 3. Typography

Family: **Proxima Nova** — the product/Figma typeface, **self-hosted** as licensed `.woff2` in `designmd/fonts/`. `--font-sans` leads with `"Proxima Nova"`; **Inter** (Google Fonts) stays as the metric fallback. Supplied weights are **Regular (400)** and **Semibold (600)** — 500 folds into Regular and 700 into Semibold via `@font-face` weight ranges until Medium/Bold `.woff2` are added. That matches Picasso, which uses only those two: its `Typography` exposes `regular`, `semibold` and `inherit`, and no component uses anything else. `--font-weight-thin` (100) and `--font-weight-light` (300) exist because Picasso's preset defines the keys, but nothing uses them and Proxima has no face for them — treat them as unavailable. `inline.py` base64-embeds the woff2 into inlined prototypes, so they render Proxima Nova with **zero external font files**. Mono: system mono stack.

### Role → Picasso `<Typography>`

Picasso's Typography resolves a `variant` × `size` pair into a size class, a weight **and
a colour**. Nine of designmd's roles land on a pair exactly:

| designmd | weight · size | Picasso |
|---|---|---|
| `--type-h1` | semibold · 2xl | `variant="heading" size="xlarge"` |
| `--type-h2` | semibold · xl | `heading` · `large` |
| `--type-h3` | semibold · lg | `heading` · `medium` |
| `--type-h4` | semibold · md | `heading` · `small` |
| `--type-body-lg` | regular · lg | `body` · `large` |
| `--type-body` | regular · md | `body` · `medium` *(Picasso's default)* |
| `--type-body-sm` | regular · sm | `body` · `small` |
| `--type-body-xs` | regular · xxs | `body` · `xsmall` |
| `--type-body-xxs` | regular · 2xs | `body` · `xxsmall` |
| `--type-caption` | regular · xxs | `body` · `xsmall` — **identical to `--type-body-xs`** |
| `--type-body-*-semibold` ×5 | semibold | `body` · size + `weight="semibold"`; Picasso's body variant is always regular, so the weight must be passed |
| `--type-mono` | regular · sm · mono | **none** — Picasso's Typography has no mono variant |

**Colour is the real divergence.** Picasso bakes it into the variant; designmd's `--type-*`
tokens carry font only and inherit `--color-text`:

| | designmd | Picasso | on white |
|---|---|---|---|
| Headings | graphite-900 `#191E28` | **black** `#000000` | 16.7:1 vs 21:1 |
| Body | graphite-900 `#191E28` | **graphite-700** `#455065` | 16.7:1 vs 8.1:1 |

So designmd's body copy is markedly darker than the product's — a prototype reads heavier
than the screen a developer builds. Worth settling deliberately: either `--color-text`
splits into a heading colour and a body colour, or designmd accepts the difference and
says so.

One Picasso oddity with no designmd counterpart: `heading` · `xsmall` is `text-md` at
**regular** weight and graphite-700 — a heading that isn't bold.

### Size primitives

| Token | Size | Used in |
|---|---|---|
| `--text-2xs` | 11px | tiny labels |
| `--text-xxs`  | 12px | captions |
| `--text-sm`  | 13px | body small |
| `--text-md`| 14px | **default body**, H4 |
| `--text-lg`  | 16px | body large, H3 |
| `--text-xl`  | 20px | H2 |
| `--text-2xl` | 28px | H1 |

> ⚠️ **Naming gotcha:** `-md` is **not** the default size — it's the *step above* default. The default body size is `--text-md` (14px). Think of the scale as `base → md → lg → xl → 2xl` rather than `sm → md → lg`.

### Type roles (use these as `font:` shorthand)

| Token | Composition |
|---|---|
| `--type-h1` | semibold 28/42 Inter |
| `--type-h2` | semibold 20/30 Inter |
| `--type-h3` | semibold 16/24 Inter |
| `--type-h4` | semibold 14/22 Inter |
| `--type-body-lg` | regular 16/24 Inter |
| `--type-body` | regular 14/22 Inter |
| `--type-body-sm` | regular 13/20 |
| `--type-body-xs` | regular 12/18 |
| `--type-body-xxs` | regular 11/16 |
| `--type-body-lg-semibold` | semibold 16/24 |
| `--type-body-semibold` | semibold 14/22 |
| `--type-body-sm-semibold` | semibold 13/20 |
| `--type-body-xs-semibold` | semibold 12/18 |
| `--type-body-xxs-semibold` | semibold 11/16 |
| `--type-caption` | medium 12/18 |
| `--type-mono` | regular 13/20 mono |

```css
h1 { font: var(--type-h1); }
.muted { font: var(--type-body-sm); color: var(--color-text-muted); }
```

Helpers in `components.css`: `.h1` `.h2` `.h3` `.h4` `.body-lg` `.body` `.body-sm` `.body-xs` `.body-xxs` `.caption`. Body scale mirrors the product: Large 16/24 · Medium 14/22 · Small 13/20 · Xsmall 12/18 · Xxsmall 11/16 (all weight 400).

---

## 4. Spacing

**Picasso's scale, names and values verbatim.** The number *is* the value: `n × 0.25rem`,
Tailwind's convention. So `--spacing-4` is exactly what a developer writes as `p-4`, and a
prototype translates to production without arithmetic.

`0=0 · 1=4 · 2=8 · 3=12 · 4=16 · 6=24 · 8=32 · 10=40 · 12=48`

**No extensions.** The scale is Picasso's nine and stops where Picasso stops. The three
that used to sit above it are gone: 20 and 32 were never referenced, and 16 turned out to
be the topbar height plus a gap wearing a spacing number — `.page-toc` now says
`calc(var(--header-height) + var(--spacing-2))`, which is what it always meant.

Never write raw px. `padding: var(--spacing-4) var(--spacing-6)`.

> **If you remember the old scale, re-read the numbers.** designmd used to be index-based —
> sequential steps — which collided with Picasso above step 4: the old step 8 was 48px
> where Picasso's `8` is 32px. Old → new: `5→6 · 6→8 · 7→10 · 8→12 · 10→16 · 12→20 · 16→32`.
> Steps 0–4 are unchanged.

---

## 5. Radii, Shadow, Motion, Layout

| Group | Tokens |
|---|---|
| Radii | `--radius-none` 0 · `-sm` 4 · `-md` 8 · `-full` 9999 — **Picasso's four, no extensions.** Picasso *replaces* Tailwind's radius scale rather than extending it, so `rounded-lg` and friends do not exist; for anything off-scale it writes a literal (its Tag uses `rounded-[6.25rem]`). |
| Shadow | `--shadow-0` … `--shadow-5`, Picasso's values. They are **roles, not a ramp**: 1 paper · 2 modal · 3 growl · 4 tooltip · 5 scroll menu. Pick by what the surface *is*. |
| Motion | `--duration-350` (Picasso) · `--duration-fast` 120 · `-base` 200 · `-slow` 320, paired with `--ease`, `--ease-out`, `--ease-in` (extensions — Picasso defines no easings). `--ease` and `--duration-fast` carry almost all of it; `-slow`, `-out` and `-in` are used by nothing but the Motion gallery. |
| Animation | `--animate-circle-spin` (Picasso) · `--animate-highlight` · `-fade-in` · `-slider-progress` · `-card-land` (from the Operationalize config). Apply whole: `animation: var(--animate-fade-in)`. All five collapse to `none` under `prefers-reduced-motion`. |
| Z-index | Picasso's: `--z-drawer` 1200 · `-modal` 1300 · `-tooltip` 1300 · `-snackbar` 1400. Extensions below them: `-dropdown` 100 · `-sticky` 200 · `-overlay` 800. (`--z-base` was 0 and unused.) |
| Breakpoints | `--breakpoint-xs` 0 · `-sm` 480 · `-md` 768 · `-lg` 1024 · `-xl` 1440 — Picasso's screens |
| Container | `--container-lg` 1024 only — the `.page` max-width. Picasso has breakpoints, not container widths; `sm`, `md` and `xl` were never referenced and are retired. |

**Sizing.** Picasso's `minWidth`, `maxWidth`, `minHeight` and `maxHeight` all start from
the spacing scale (`...theme('spacing')`), so `min-w-4` is just `--spacing-4` and needs no
token of its own. Only what Picasso adds on top is declared:

| Group | Tokens |
|---|---|
| Min width | `--min-width-14` 56px · `-16` 64px · `-24` 96px — the three steps past the spacing scale |
| Max width | `--max-width-1-12` … `--max-width-11-12` — Picasso's 12-column grid. The class is `max-w-1/12`; a slash cannot appear in a custom property name, so the token spells it out. |

Still not carried: the two plugin utilities `.font-inherit-weight` and
`.font-inherit-size`.

### Breakpoints

Match **Picasso's** screen breakpoints when writing responsive rules — viewport `@media`, or `@container` for framed previews (e.g. the app-shell device tabs). Source: [Picasso breakpoints](https://toptal.github.io/picasso/?path=/story/utils-breakpoints--breakpoints).

| Name | Range | Edge |
|---|---|---|
| `xs` | `< 480px` | — |
| `sm` | `480px ≤ w < 768px` | 480 |
| `md` | `768px ≤ w < 1024px` | 768 |
| `lg` | `1024px ≤ w < 1440px` | 1024 |
| `xl` | `≥ 1440px` | 1440 |

The four edges are **480 · 768 · 1024 · 1440**. Author mobile-first (base = `xs`) and layer overrides upward with `min-width`:

```css
.grid { grid-template-columns: 1fr; }                 /* xs — mobile */
@media (min-width: 768px)  { .grid { grid-template-columns: 1fr 1fr; } }        /* md+ */
@media (min-width: 1024px) { .grid { grid-template-columns: repeat(3, 1fr); } } /* lg+ */
```

CSS custom properties can't be read inside a `@media`/`@container` condition, so use the literal px edges above. On the React side Picasso exposes the same values via its `screens()` helper and the Tailwind `sm:` / `md:` / `lg:` / `xl:` prefixes.

---

## 6. Components

All component CSS lives in `components.css` and references **semantic tokens only**. The shortcode table below is the quick-reference index of every component — drop the root class (or attribute) into prototype markup and the styles apply.

### Shortcode reference

> **Pointing at a component.** Every row below links to a live demo at `example.html#<id>`. To tell a teammate "use this component", share that URL — or click the **`#`** anchor next to any heading in the live showcase to copy the link in one go. The id format is stable: `#buttons`, `#alerts`, `#toasts`, etc.

| Component | Root | Variants / parts |
|---|---|---|
| [Buttons](./example.html#buttons) | `.btn` | `.btn-primary` · `.btn-secondary` · `.btn-ghost` · `.btn-danger` · `.btn-xs` · `.btn-icon-only` |
| [Date picker](./example.html#datepicker) | `.datepicker` + `data-datepicker` | Wraps an `.input-icon` field with `.datepicker-input`; the `[data-datepicker]` handler in `example.html` builds `.datepicker-panel` (`.datepicker-head` · `.datepicker-month` · `.datepicker-grid` · `.datepicker-dow` · `.datepicker-day` · `.datepicker-foot`). Options: `data-min` (ISO), `data-min-from` (selector of another date field), `data-align="end"`. Day states: `.is-today` · `.is-selected` · `.is-outside` · `:disabled`. Picking fires `input` + `change`. |
| [Inputs](./example.html#inputs) | `.field` + `.input` | `.field-label` · `.field-hint` · `.field-hint.is-error` · `.input-xs` · `.input-icon` wrapper (`.input-icon-left` / `.input-icon-right`) with a `.input-icon-glyph` for an inset icon |
| [Select](./example.html#inputs) | `.input-select` | `.input-select-trigger` · `.input-select-value` (+ `.dropdown-menu` for options) |
| [Tag input](./example.html#inputs) | `.input-tags` | `.input-tags-input` · `.chip` · `.chip-remove` |
| [Top bar](./example.html#topbar) | `.topbar` | `.topbar-brand` · `.topbar-search` · `.topbar-avatar` |
| [Side navigation](./example.html#sidenav-demo) | `.sidenav` | `.sidenav-item` · `.sidenav-group` · `.sidenav-group-trigger` · `.sidenav-sublist` · `.sidenav-subitem` · `.sidenav-toggle` · `.is-compact` |
| [Switches](./example.html#switches) | `.switch` | `.switch-input` · `.switch-track` |
| [Radios](./example.html#radios) | `.radio` | `.radio-input` · `.radio-circle` · `.radio-label` · `.is-error` |
| [Checkboxes](./example.html#checkboxes) | `.checkbox` | `.checkbox-input` · `.checkbox-box` · `.checkbox-mark` · `.is-error` |
| [Sliders](./example.html#sliders) | `.slider` + `.slider-input` | Native `<input type="range">`. Optional siblings: `.slider-icon` · `.slider-label` · `.slider-value` (static min/max) · `<output data-slider-output>` (live readout) · `.slider-field` on an `.input.input-xs` number field (two-way sync). Track fill + sync handled by the example.html script block. |
| [Tags](./example.html#tags) | `.tag` | Solid + indicator: `.tag-positive` · `.tag-negative` · `.tag-warning` · `.tag-light` · `.tag-dark` · `.tag-blue` · `.tag-indicator` |
| [Status pills](./example.html#tags) | `.badge` | `.badge-success` · `.badge-warning` · `.badge-danger` · `.badge-info`. Interactive: render as `<button class="badge">` (editable); compose `.badge-icon` (leading icon) and/or `.badge-remove` (trailing ×, click deletes the pill). Demoed under Tags. |
| [Count badges](./example.html#badges) | `.count-badge` | `.count-badge-sm` · `.count-badge-lg` · `.count-badge-secondary` |
| [Avatars](./example.html#avatars) | `.avatar` | `.avatar-xs` (16) · `.avatar-sm` (24) · `.avatar-md` (32, default) · `.avatar-lg` (40) · `.avatar-xl` (80) · `.avatar-2xl` (120) · `.avatar-team` (semantic hook for team/company; same neutral fill, icon child differentiates). Render as `<span>` (read-only) or `<button>` / `<a>` (interactive). Content child is one of: `<img>`, 1–2 letters, or `<svg class="icon"><use href="#i-…"></svg>`. |
| [Accordion](./example.html#accordion) | `.accordion-group` > `.accordion` | Item = `.accordion-summary` (trigger, `aria-expanded`) + `.accordion-details` > `.accordion-content`. Open with `.is-open`, disable with `.is-disabled` (+ `disabled` on the summary). Group border modifiers: `.borders-all` (default) · `.borders-middle` · `.borders-none`. Chevron `.accordion-chevron` rotates; toggle handled by the delegated script. |
| [Alerts](./example.html#alerts) | `.alert` | `.alert-danger` · `.alert-warning` · `.alert-success` · `.alert-info` · `.alert-icon` · `.alert-message` · `.alert-actions` · `.alert-close` |
| [Toasts](./example.html#toasts) | `.toast-region` + `.toast` | Colors: `.toast-neutral` · `.toast-error` · `.toast-warning` · `.toast-success` · `.toast-info`. Parts: `.toast-icon` · `.toast-message` · `.toast-action` · `.toast-close`. Spawn via `toast({ variant, message, behavior: 'timed'\|'persistent'\|'action', timeout, action: { label, onClick } })`. |
| [Loaders](./example.html#loaders) | `.chase` / `.chase-cw` | Chase spinner — the logo mark's 24 segments fading in sequence. `.chase` counter-clockwise (blue) · `.chase-cw` clockwise (graphite + blue flash). Sizes `.size-sm` 24 · `.size-md` 32 · `.size-lg` 48. Copy the `<svg viewBox="0 0 22 32">` block from example.html#loaders; segment delays come from the script block. Respects `prefers-reduced-motion`. |
| [Dropdown menu](./example.html#dropdowns) | `.dropdown` | `.dropdown-trigger` · `.dropdown-menu` · `.dropdown-menu-end` · `.dropdown-item` · `.dropdown-item-danger` · `.dropdown-item-icon` · `.dropdown-item-avatar` · `.dropdown-divider` · `.dropdown-header` (profile card: avatar + name + role) · `.dropdown-item-count` (trailing badge). Account menu demoed at [#topbar](./example.html#topbar). |
| [Dropzone](./example.html#dropzone) | `.dropzone-field` > `.dropzone` | Dashed click-or-drag file target. `.dropzone` wraps a full-bleed `.dropzone-input` (`<input type=file>`) so the whole area is clickable + focusable. Parts: `.dropzone-icon` · `.dropzone-title` · `.dropzone-hint`. States: `.is-dragover` (blue) · `.is-disabled` (muted) · `.is-error` (red). Feedback row: `.dropzone-status` (+ `.is-error`) with `.dropzone-status-label` · `.dropzone-progress` > `.dropzone-progress-bar` · `.dropzone-status-dismiss`. Add `data-dropzone` to the field for the `initDropzones()` helper (drag highlight + simulated progress). |
| [Modal](./example.html#modals) | `.modal-overlay` + `.modal` | `.modal-{xs,sm,md,lg,xl}` · `.modal-header` · `.modal-body` · `.modal-footer` · `.modal-close` · `[data-modal-open]` / `[data-modal-close]` |
| [Drawer](./example.html#drawers) | `.drawer-overlay` + `.drawer` | `.drawer-{narrow,regular,medium,wide,ultra,full}` · `.drawer-header` · `.drawer-body` · `.drawer-footer` |
| [Breadcrumbs](./example.html#breadcrumbs) | `.breadcrumbs` + `.breadcrumb` | Parent crumbs are `<a class="breadcrumb">` (blue, underline on hover); current page is `<span class="breadcrumb is-current" aria-current="page">` (plain text). Chevron separators render automatically. Usually the first row inside a page head; works standalone. |
| [Page heads](./example.html#page-heads) | `.page-head` | `.page-head-main` · `.page-head-title` · `.page-head-heading` · `.page-head-subtitle` · `.page-head-actions` · count next to the heading uses `.count-badge .count-badge-lg .count-badge-secondary` · optional `.breadcrumbs` as the first row inside `.page-head-main` |
| [Tabs](./example.html#tabs) | `.tabs` + `.tab` | `.is-active` · `role="tablist"` / `role="tab"` / `aria-controls` / `[role="tabpanel"]` |
| [Stepper](./example.html#stepper) | `.stepper` (`<ol>`) | `.stepper-step` (+ `.is-current` filled / `.is-complete` check) · `.stepper-num` · `.stepper-label` · `.stepper-sep` (caret between steps) |
| [Tooltips](./example.html#tooltips) | `[data-tooltip="…"]` | `[data-placement="bottom\|left\|right"]` (default top) · `[data-tooltip-style="regular"]` for the white wrapping variant with caret (compact dark pill is the default) |
| [Cards](./example.html#cards) | `.card` | `.card-title` · `.card-body` |
| [Tables](./example.html#tables) | `.table` | `.table-wide` · `.table-scroll` · `.th-sort` · `.cell-title` · `.cell-user` · `.avatar` · `.cell-user-meta` · `.cell-meta` · `.cell-meta-sub` · `.cell-dot` (`.is-warning` / `.is-danger`) · `.cell-actions` |
| [Toolbar](./example.html#toolbar) | `.toolbar` | Control strip above a table/list. Parts: `.toolbar-search` (grow, wrap an `.input-icon`) · `.toolbar-end` (pin controls right) · `.toolbar-spacer`. Composes `.input-select.is-auto` (content-width quick-filters), `.btn`, `.segmented`, `.checkbox`. |
| [Segmented](./example.html#toolbar) | `.segmented` | Bordered mutually-exclusive switcher. `.segmented-item` (`.is-active` = dark fill) · `.segmented-icon` for icon-only segments. Click handled by the delegated `.segmented` handler. |
| [Sheet](./example.html#sheet) | `.table.table-sheet` + `data-sheet` | Editable-spreadsheet variant of `.table`. Structure: `.sheet-gutter` (row `#`) · `.sheet-toggle` (pinned expand/collapse column — the module hoists each row's `.row-toggle` here and adds a `.sheet-collapse-all` control in its header) · `.sheet-col` header (`.sheet-col-inner` · `.th-sort` · `.th-menu` · `.th-resize`) · `td.sheet-cell` per cell. Cell config via attrs: `data-type="text\|select\|person\|date\|tags\|link"`, `data-variant="name\|muted\|health\|time"`, `data-value`, `data-label` (link), `data-dot` (`is-warning`/`is-danger`), `data-empty-icon`, `data-fail` (demo save error). Cell states: `.is-empty` · `.is-selected` · `.is-editing` · `.is-saving` · `.is-saved` · `.is-error` · `.is-range` · `.is-readonly` · `.is-skeleton`. Behaviour is auto-wired by the `data-sheet` module in the `example.html` script block. |
| [Icons](./example.html#iconography) | `.icon` | `<svg class="icon"><use href="#i-{name}"></svg>` — references the custom Figma icon sprite (`icons.svg`, 320 icons + aliases). **Two sizes only: 16 & 24** (`.icon-16` / `.icon-24`). Default colour graphite-700 (`--color-icon`); colour-carrying contexts (buttons, links, badges, toasts) override via `currentColor`. Browse/search them in the Iconography section. |
| Type helpers | `.h1`–`.h4`, `.body`, `.body-sm`, `.caption` | — |
| Layout helpers | `.stack`, `.row`, `.page`, `.grid-2` | — |
| Plugin launcher | `.pg-fab` | One button, bottom-right of every prototype, that switches the plugins below on and off. Lists only what the page carries; the rest are greyed out with the reason. CSS in `plugins.css`, JS in `plugins.js`, both inlined by `inline.py` alongside the review bar. |
| Review bar | `.rv-bar` | Switched on from the plugin launcher bottom-right, or with `?review=1` on the URL (remembered per page; `?review=0` turns it off). Edit text / Comment / Spotlight; comments persist to `feedback.json` via `tools/serve.mjs`. `review.css` + `review.js` are auto-inlined by `inline.py` — nothing to copy. See §7. |
| [Versions & changes](./versions.html) | `.vr-bar` · `.vr-legend` · `[data-change]` | Only on features prototyped in versions (`features/<feature>/vN-<name>/` + `versions.json`), declared per version with `<meta name="icarus-versions" content="../versions.json">`. **Versions** (`?versions=1`) — bar bottom-centre to flip between versions, state carries over, Alt+← / Alt+→. **Changes** (`?changes=1`) — outlines elements marked `data-change="new\|moved\|changed"` + `data-change-note` vs the version in `basedOn`. `versions.css` + `versions.js` are auto-inlined with the review bar. |

### Rules of thumb

- **Check the system before you build.** Nothing bespoke until `example.html` has been looked at and found wanting. Most of what a prototype needs is already a component — toasts, snackbars, modals, drawers, switches, empty states, banners — and a hand-rolled version of something that exists is drift the moment the real one changes. The order is: find the component → if it is close, add a variant to `components.css` → only then write something new, and write it in `components.css` so the next prototype inherits it, not inline in one file. A one-off that lives in a single page is the thing this system exists to prevent.
- **Compose, don't override.** Stack variants on the root class (`<button class="btn btn-xs btn-primary">`). Don't write new CSS in a feature file — if a variant is missing, add it to `components.css` and re-inline.
- **Stick to semantic tokens.** In any inline styles use `var(--color-*)` / `var(--spacing-*)` / `var(--type-*)` — never raw palette tokens like `var(--color-blue-500)`.
- **JS-driven components** (modals, drawers, dropdowns, tabs, alerts, tooltips, tag inputs, character counters) get their behavior from the `<script>` block in `example.html`. When you build a new prototype, copy that whole block — the handlers are delegated and idempotent, so they activate on any markup that uses the right classes / data attributes.
- **Page structure:** wrap content in `<main class="page">` to get the 1024px max-width centered layout.
- **Wide vs. sheet tables.** Both share the `.table` base, so a prototype can offer a view toggle by swapping the modifier. Use `.table-wide` for read-heavy lists (tall rows, zebra striping, rich cell content). Use `.table-sheet` + `data-sheet` for editable, dense, Airtable/Linear-style grids where every cell is inline-editable through the shared cell state machine. Drive columns and cell values off `data-*` attributes — the module renders and wires everything; you don't hand-author cell inner markup (except the Name cell's `.sheet-tree` scaffold for the row toggle).

### Common snippets

```html
<!-- Button -->
<button class="btn btn-primary">Continue</button>
<button class="btn btn-secondary">Cancel</button>
<button class="btn btn-ghost">Skip</button>
<button class="btn btn-danger">Delete</button>

<!-- Field + Input -->
<label class="field">
  <span class="field-label">Email</span>
  <input class="input" type="email" placeholder="you@example.com" />
  <span class="field-hint">We'll never share your email.</span>
</label>

<!-- Card -->
<article class="card">
  <h3 class="card-title">Title</h3>
  <p class="card-body">Body text.</p>
</article>

<!-- Badge -->
<span class="badge badge-success">Active</span>

<!-- Alert -->
<div class="alert alert-warning" role="alert">
  <svg class="icon alert-icon"><use href="#i-warning"></use></svg>
  <p class="alert-message">Your trial expires in 5 days.</p>
  <div class="alert-actions">
    <button class="btn btn-xs btn-primary">Upgrade</button>
  </div>
  <button class="alert-close" type="button" aria-label="Close"><svg class="icon"><use href="#i-x"></use></svg></button>
</div>

<!-- Tabs -->
<div class="tabs" role="tablist">
  <button class="tab is-active" role="tab" aria-selected="true" aria-controls="p-1" id="t-1" type="button">Overview</button>
  <button class="tab" role="tab" aria-selected="false" aria-controls="p-2" id="t-2" type="button">Activity</button>
</div>
<div role="tabpanel" id="p-1" aria-labelledby="t-1">…</div>
<div role="tabpanel" id="p-2" aria-labelledby="t-2" hidden>…</div>

<!-- Tooltip -->
<button class="btn btn-secondary" data-tooltip="Save your changes" data-placement="top">Save</button>

<!-- Type helpers -->
<h1 class="h1">Page title</h1>
<p class="body">Body copy.</p>
<span class="caption">Caption</span>
```

For the full inventory with every modifier and live demos, open `example.html` — it's the source of truth for what's available and how each component composes.

---

## 7. Workflow — central system, inlined single-file prototypes

The deliverable for any prototype is **one HTML file** with all CSS + assets inlined. No external dependencies, no build step at runtime, no GitHub setup needed for the file to work. Drop it on Netlify, attach it to an email, open it from `file://` — same render every time.

### Two folders, side by side

```
Development/
├── designmd/                    ← the design system → pushed to GitHub
│   ├── tokens.css               ← primitives
│   ├── semantic.css             ← aliases + reset
│   ├── components.css           ← all component CSS
│   ├── devtools.css             ← author tooling (debug overlays) — NOT in the layer chain
│   ├── plugins.css / plugins.js ← the plugin launcher (one button for every plugin)
│   ├── versions.css / versions.js ← Versions + Changes plugins (versioned features only) — auto-inlined
│   ├── review.css / review.js   ← the review bar (comments, text edits, spotlight) — auto-inlined, dormant until ?review=1
│   ├── tools/serve.mjs          ← dev server: static files + feedback.json API for the review bar
│   ├── design.md                ← this file (LLM context + reference)
│   ├── assets/
│   │   └── logo.svg
│   ├── inline.py                ← bakes the system into a prototype HTML
│   └── example.html             ← system showcase (uses local ./ links)
│
└── features/                    ← prototypes → dropped onto Netlify
    ├── integrations/
    │   └── index.html           ← single-file prototype
    └── slide-integration/
        └── index.html           ← single-file prototype
```

`designmd/` is the stable source of truth that gets pushed to GitHub. `features/` is a separate, fast-moving sandbox of single HTML files. The two folders are **siblings** — `features/` is not a subfolder of `designmd/`, so the design-system repo isn't polluted with prototype churn.

> **Rule — every feature follows `features/feature-name/index.html`.**
>
> The path has three fixed levels:
>
> 1. **`features/`** — the parent folder. It lives as a sibling of `designmd/` and is always present. If it doesn't exist yet, create it on first use.
> 2. **`feature-name/`** — a folder *inside* `features/`, named after the feature in kebab-case (e.g. `billing-portal/`, `slide-integration/`). One folder per feature, never reused.
> 3. **`index.html`** — the working file. Always called exactly `index.html` — never `feature-name.html` or anything else.
>
> Full example: `features/billing-portal/index.html`.
>
> This keeps URLs clean (`/billing-portal/` instead of `/billing-portal.html`), lets each feature ship its own colocated assets later if needed, and matches the structure of the existing `integrations/` and `slide-integration/` prototypes.

> **Rule — every feature prototype ships as a self-contained single file.**
>
> **`inline.py` refuses a prototype whose own styles use tokens the system no longer
> defines.** It only swaps the block between the `tokens.css` markers, so a prototype
> written against an older vocabulary would keep its hand-written styles and lose every
> reference underneath them — the page comes out unstyled and it looks like the script
> broke it. The check compares against what `tokens.css` and `semantic.css` actually
> define (not a hardcoded prefix, so it survives later renames), ignores `var(--x,
> fallback)` and anything the prototype defines itself, and prints the offending tokens
> with counts. Rename them first, then inline. `--force` overrides, and `--only-review`
> skips the check since it never touches the token block.

> A feature's `index.html` MUST have the design system inlined into it before it leaves the local checkout. That means the `<link rel="stylesheet" href="../designmd/...">` tags get replaced with `<style>…</style>` blocks containing the actual CSS, and the logo SVG gets inlined too. After inlining, the file has **zero external dependencies** — including the custom icon sprite (`icons.svg`), which `inline.py` injects after `<body>`. (Phosphor has been retired; there is no remote icon CDN anymore.)
>
> Why: the deliverable for every prototype is one HTML file. It needs to render identically when dropped on Netlify, attached to an email, opened from `file://`, hosted from any static server, or shared as a download. Relative `../designmd/` links work locally but break the moment the file is moved — so the file is never shipped with those links live.
>
> **How:** run `python3 inline.py ../features/feature-name/index.html` from the `designmd/` folder (the script is idempotent — re-running it on an already-inlined file updates the inline block in place). Run before every commit / share / deploy.
>
> **Local iteration is exempt** — while actively building the feature you can keep the `<link>` tags pointing at `../designmd/` for instant feedback when the system CSS changes. Just inline before you push the prototype anywhere.

### Building a new prototype

Create `features/billing-portal/index.html` (or whatever your feature is named, kebab-case) linking to the sibling system:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>My prototype</title>
  <link rel="stylesheet" href="../designmd/tokens.css" />
  <link rel="stylesheet" href="../designmd/semantic.css" />
  <link rel="stylesheet" href="../designmd/components.css" />
</head>
<body>
  <!-- prototype markup -->
  <img class="topbar-brand-logo" src="../designmd/assets/logo.svg" alt="…" />
</body>
</html>
```

Iterate locally — open via `file://` or a small static server. Relative paths to `../designmd/` resolve as long as both folders stay siblings.

### Inline + ship

When you're ready to deploy, from the `designmd/` folder run:

```bash
python3 inline.py ../features/billing-portal/index.html
```

The script reads `tokens.css` / `semantic.css` / `components.css` / `assets/logo.svg` from `designmd/` (where it lives) and bakes them into the target HTML at whatever path you point it at. The file becomes self-contained (~88 KB for a full prototype).

**Feature-local `<style>` blocks survive.** `inline.py` only touches the design-system block (bounded by the `/* === tokens.css === */` marker) and the topbar logo. Any other `<style>` block in the prototype — say, a one-off layout grid or a single demo override — is preserved exactly as written. You can author prototype-specific CSS without fear of it getting wiped on the next inline pass. (That said, if a style would be useful in more than one prototype, promote it into `components.css` instead.)

Drag the resulting HTML onto [app.netlify.com/drop](https://app.netlify.com/drop). Done.

### Refreshing prototypes when the system updates

The script is **idempotent** — running it on an already-inlined file detects the `/* === tokens.css === */` marker and replaces the inline block in place:

```bash
cd designmd
python3 inline.py ../features/*/index.html
```

Every prototype is back in sync with the latest system CSS. No external CDN, no broken links, no manual swap.

### Preview server setup (Claude Code / IDE preview panel)

The preview panel runs the dev servers defined in `.claude/launch.json` — one for `designmd/` (port 4173) and one for `features/` (port 4174). The features server must use an **absolute path**, not `../features`:

```json
{
  "name": "features",
  "runtimeExecutable": "npx",
  "runtimeArgs": ["-y", "serve", "/absolute/path/to/icarus/features", "-l", "4174"],
  "port": 4174
}
```

Why: when the project is checked out via a git worktree (which Claude Code does for isolated sessions), the worktree's cwd is *not* a sibling of `icarus/features/`, so a relative `../features` resolves to a non-existent folder and the preview 404s. The absolute path stays correct regardless of worktree location.

The HTML inside each prototype is unaffected by this — the `<link rel="stylesheet" href="../../designmd/…">` tags resolve correctly under both the preview server and standalone `file://` use, and an inlined prototype has no dependencies at all.

### Review bar — comments, inline text edits, spotlight

Every inlined prototype carries the review bar. Turn it on with the circle button in the bottom-right corner of the page, or with `?review=1` on the URL (the choice sticks per page in `localStorage`; the button or `?review=0` turns it off). Modes, with single-letter shortcuts:

- **Interact** (`I`) — use the prototype normally.
- **Edit text** (`E`) — click any text and retype it. Edits are stored by element path and reapplied after the prototype re-renders, so they survive navigation inside the page.
- **Comment** (`C`) — click any element to leave a note on it. Numbered pins mark commented elements; the side panel lists open / resolved comments, with Resolve, Delete and **Copy comments as prompt**.
- **Spotlight** (`S`) — drag a rectangle; everything outside it is dimmed. Esc clears it.

**Shared, not private.** Every comment and edit is sent as a small operation to `/api/feedback` and the page polls it, so everyone who opens the same prototype sees the same comments and edited copy (reviewers are asked for a name once). Locally the Icarus dev server is that API and persists to `feedback.json` next to the prototype's `index.html`:

```bash
node tools/serve.mjs /absolute/path/to/features 5733
```

(`.claude/launch.json` entry: `"runtimeExecutable": "node", "runtimeArgs": ["/abs/path/icarus/tools/serve.mjs", "/abs/path/features", "5733"], "port": 5733`.)

**Deployed on Vercel:** the prototypes repo already carries `api/feedback.js` (+ `lib/feedback-db.mjs`, `db/schema.sql`). Add a Neon Postgres database from the Vercel Marketplace (injects `DATABASE_URL`), run `psql "$DATABASE_URL" -f db/schema.sql`, redeploy. One row per comment, so concurrent reviewers can't overwrite each other and Delete is a soft delete. Optionally set `REVIEW_TOKEN` to gate writes. Without a reachable store the bar says "Local only" and queues its changes until the store appears. The ops contract is in `tools/feedback-store.mjs`; full setup in `review-bar.html`. Archive an approved prototype's comments back into git with `node tools/feedback-sync.mjs pull <prototype>`.

**`feedback.json` shape.** `edits` maps `"<root>/<child.index.path>#<textNodeIndex>"` → `{orig, text, screen}`; `comments` is a list of `{id, n, path, el, html, screen, screenId, url, rect, text, created, resolved, resolution?}`. `el` is a human label (`button.btn "Save"`), `html` the first 600 chars of the element's markup, `screen` whatever the prototype reports as the current screen (its `<title>` by default).

**Applying comments with an LLM.** In a Claude Code session on the prototype folder, say *"apply the prototype comments"*: read the store (`feedback.json` locally, or `GET https://<site>/api/feedback?p=/<prototype>/` for the live link), implement every comment with `resolved: false` in `index.html` (use `el`, `html`, `screen` and `url` to find the spot), then set `resolved: true` and a one-line `resolution` on each (on the live store: `POST /api/feedback` with `{p, ops:[{t:'comment', c:{id, resolved:true, resolution}}]}`). Inline `edits` are applied at runtime; bake them into the source only when asked. "Copy comments as prompt" in the side panel produces the same instructions as plain text for any other agent.

**Optional host adapter.** A prototype with its own screen/flow model can tell the bar about it:

```js
window.REVIEW = {
  screen: () => ({ id: state.step, name: SCREENS[state.step] }),   // stamped on every comment
  goto: id => showStep(id),                                        // enables "Go to" on a comment
  roots: '[data-layer], #main, .sidenav'                           // stable containers for element paths (default: <body> children)
};
```

### Two iteration modes

- **Iterating on a prototype** (the common case): edit `features/feature-X/index.html` directly. CSS is already inlined — the `<style>` block sits at the top of the file, ignore it and edit the markup below.
- **Iterating on the design system** (less common): edit `designmd/tokens.css` / `semantic.css` / `components.css` and reload `designmd/example.html` (uses local `./` links for instant feedback). When stable, push to GitHub and run `inline.py` across every prototype to bake the changes in.

### Why this approach over CDN-linked HTML

We tried two patterns before this:

1. **`./` local links** — fast to develop, but the HTML breaks the moment you move it out of the folder. Can't drop on Netlify standalone.
2. **CDN-hosted CSS via jsDelivr** — portable, but requires the GitHub repo to be public and pushed, with a find/replace for `USER/REPO`. Cache TTL means CSS edits don't appear instantly. Loses the "single file works anywhere" property if the repo is private.

Inlined HTML is the lightweight, zero-headache version: the file IS the design system at the moment of inlining. Frozen, portable, no infrastructure.

---

## 8. Vibe prompt (paste into LLM)

> Build an HTML prototype for the Icarus design system at `features/feature-name/index.html`. The system lives in a sibling `designmd/` folder.
>
> **Boilerplate** — link the three stylesheets (icons are injected by `inline.py`, no icon CDN):
>
> ```html
> <link rel="stylesheet" href="../designmd/tokens.css" />
> <link rel="stylesheet" href="../designmd/semantic.css" />
> <link rel="stylesheet" href="../designmd/components.css" />
> ```
>
> Before shipping, run `python3 inline.py ../features/feature-name/index.html` from `designmd/` to bake all CSS **and the icon sprite** into the file. Result: zero external dependencies.
>
> **Rules:**
> - Use **semantic tokens only** (`--color-bg`, `--color-text`, `--color-brand`, `--type-h1`). NEVER reference primitives like `--color-blue-500` directly.
> - **Three color roles:** brand mark = blue-500 (`--color-accent`, logo only); primary CTA = green-500 (`--color-brand`, ONE per page — every other CTA is `.btn-secondary`); chrome = graphite-800 (topbar only).
> - Reuse component classes from the §6 shortcode reference (`.btn`, `.card`, `.input`/`.field`, `.alert`, `.tabs`, `.toast`, `.tooltip` via `[data-tooltip]`, `.avatar`, `.table` (+ `.table-sheet` editable grid via `data-sheet`), `.dropdown`, `.modal`, `.drawer`, `.page-head`, `.sidenav`, `.topbar`, `.badge`, `.tag`, `.chip`, `.switch`, `.radio`, `.checkbox`, etc.). Compose variants on the root (`<button class="btn btn-xs btn-primary">`). Don't author new component CSS in the prototype — if a variant is missing, add it to `components.css` and re-inline.
> - All spacing via `--spacing-*`. All radii via `--radius-*`. All motion via `--duration-*` + `--ease*`.
> - Status colors (red/yellow/green) only signal state, never decoration.
> - Type is the visual hierarchy. Avoid extra borders, dividers, or background fills.
> - Layout with `.stack` / `.row` / `.grid-2` and flex/grid. Constrain content via `<main class="page">` (1024px max).
> - Icons: `<svg class="icon"><use href="#i-{name}"></svg>` from the custom Figma sprite (`icons.svg`, auto-injected by `inline.py`). Inter font already loaded via `tokens.css`.
> - **JS-driven components** (modals, drawers, dropdowns, tabs, alerts, tooltips, toasts, tag inputs, char counters) need the delegated `<script>` block from `designmd/example.html` copied into your prototype — handlers are idempotent and activate on the right classes / `data-*` attributes.
> - **The review bar comes for free.** `inline.py` adds `review.css` + `review.js` to every prototype; open it with `?review=1` to comment, edit text and spotlight. Don't build your own feedback tooling. Serve prototypes with `tools/serve.mjs` so comments persist to `feedback.json`.

## 9. Figma design — requirements & guidelines

Claude increasingly drives the Figma design flow directly (reading frames, generating designs, and syncing them back through the Figma MCP). These are the house rules every Figma design must follow. Treat them the way the rest of this doc treats tokens: non-negotiable defaults, deviate only when a requirement explicitly says so.

### Frame dimensions

- **Width is always `1440px`.** Every frame added to a Figma file — screen, page, or full-view mockup — is authored at 1440px wide. This is the canonical desktop canvas; do not use 1280, 1512, or any other width unless a ticket names a specific breakpoint.
- **Height varies with content, and `900px` is the default.** Reach for 900px first; grow the frame taller only when the content genuinely needs it (long lists, stacked sections). Keep the *above-the-fold* region within the first 900px so the primary content and CTA are visible without scrolling.

| Property | Value |
| --- | --- |
| Frame width | **1440px** (fixed) |
| Frame height | varies — **900px** default, taller as content requires |

More Figma requirements (naming, layers, component usage, tokens/variables, hand-off) will be added to this section as the flow matures.

### Component binding — designmd ↔ Figma ↔ React (Picasso)

There are **two** component libraries for Icarus: this HTML/CSS one (`designmd/`) and a Figma component library. They must stay in lockstep so that when an approved feature moves from HTML into Figma, Claude drops the **real published Figma component** — never a hand-drawn or randomly generated approximation — and, in reverse, recreates a Figma frame with the correct designmd classes.

The binding is stored in two artifacts:

1. **`figma-map.json` (phase 1 — in repo now).** The authoritative pairing: for every component it records the designmd side (`root` class, `variants`, canonical `snippet`, shortcode URL) and the Figma side (`component` name, `nodeId`, `key`, and a `propMap` from Figma variant/property values → designmd variant classes). The Figma fields start as `pending-discovery` and are filled by reading the published library (`get_code_connect_suggestions` → `get_context_for_code_connect`).
2. **Code Connect templates (phase 2 — `figma/*.figma.ts`).** Once the Figma library is published and a Node toolchain is available, each mapping is emitted as a `.figma.ts` template that returns the designmd HTML snippet, published via the Code Connect CLI so it also surfaces natively in Figma Dev Mode and the MCP. Generated from `figma-map.json`, not authored by hand.
3. **React cross-reference (`react` block, in repo now).** Each entry also carries a `react` block binding the component to the **Picasso** React/Storybook library — `component`, `import`, Storybook `storyId`, a `status` (`mapped` · `partial` · `gap`), and a `propMap` translating designmd variant classes → React props. A stable `slug` is stamped onto the markup as `data-component="<slug>"` (auto-applied from each entry's `stampSelector`). Engineers open any prototype with **`?map=1`** (or the goggles toggle in `example.html`'s nav): mapped components get a pink dotted outline and hovering one shows the resolved React usage (e.g. `<Button variant="primary" size="small" />`), the import line, and a deep link to the Picasso story. `gap`/`partial` entries surface their `note` so library gaps stay visible instead of being faked.

**Rules for using the binding**

- **Mapped components come first — always.** Whenever a Figma flow is being built (a new frame, screen, or view), the mapped library component in `figma-map.json` is the default and must be used before anything else. The order of preference is: (1) a `mapped` / `mapped-external` component → instantiate it by `nodeId`; (2) a `composite` / `no-component-yet` entry → assemble from its listed `parts`; (3) only if neither exists, build from scratch — and flag it as a library gap. Never hand-draw or auto-generate an approximation of something that already has a mapping.

- **Code → design (approved feature → Figma).** For every element in the HTML, look up its `root` class in `figma-map.json`, then instantiate the mapped Figma component by `nodeId` (via `use_figma`) and set its variants from `propMap`. If a class has a mapping, you MUST use that component — do not draw rectangles/text to fake it. If a class has **no** mapping yet, flag it (it's a gap to add to the library), don't silently improvise.
- **Design → code (Figma frame → HTML).** Reverse-lookup by Figma component name/`nodeId` and emit the recorded `snippet` with the right variant classes.
- **Icons come from the custom Figma pack — both sides.** designmd now ships the pack itself as an inline SVG sprite (`icons.svg`, generated by `tools/export_icons.py` from the Figma *Iconography* file); Phosphor is fully retired. HTML uses `<svg class="icon"><use href="#i-{slug}"></svg>`; Figma flows use the same pack via icon instance-swaps. Slugs match 1:1, so there is no name translation — `#i-{slug}` in HTML ↔ the `{slug}` component in Figma. New icons: add them to the Figma pack, re-run `export_icons.py`, and they appear in both places.
  - **Two grids, and icons scale with their text.** The pack is drawn on a 16 and a 24
    grid — those are the only two artworks, in HTML and in Figma. Rendering is `1em`:
    `.icon` is `width: 1em; height: 1em` with `vertical-align: -0.125em`, which is
    character-for-character what Picasso does (`h-[1em] align-[-.125em]` on every icon
    component). So an icon in a 13px button renders at 13px, exactly as Picasso's does —
    its own button sizes are 12, 13 and 15px, never 16.

    Pin a size with `.icon-16` / `.icon-24` only where a context genuinely needs one
    independent of its text — `.sidenav-item-icon` does, so the icon reads a little
    larger than its 14px label. Don't invent a third size: 18px, 14px and 12px literals
    were all removed in favour of `1em` or a pinned 16. If a design needs a larger
    graphic, that's a [Pictogram](#9-figma-design--requirements--guidelines) (64×64),
    not an icon. Stroke icons carry `vector-effect="non-scaling-stroke"`, so the stroke
    stays a constant 1px at any rendered size (the exporter/importer add it
    automatically).
  - **Default colour: graphite-700** (`--color-icon`). Standalone icons rest at graphite-700; icons inside colour-carrying components (primary buttons, links, badges, tags, toasts) inherit that component's colour instead.
- **Keep the map in sync.** Every new designmd component (a new §6 shortcode row) gets a matching `figma-map.json` entry in the same change — including its `slug`, `stampSelector`, Figma binding, and `react` block. A component isn't "done" until all three sides (designmd, Figma, React) and the mapping exist. `react.propMap` values are best-effort until confirmed against the Picasso story controls.

Frame dimensions from the section above (1440 × 900) still apply to whatever view the mapped components are assembled into.
