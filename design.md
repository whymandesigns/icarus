# Icarus — design.md

> Source of truth for vibe prototyping. Paste this file (or the **Vibe prompt** section) into your LLM context when generating new HTML prototypes. Every prototype links three stylesheets in order: `tokens.css` → `semantic.css` → `components.css`.

---

## Architecture

Three layers. Don't skip them.

```
┌──────────────────────────────────────────────────────────────┐
│  tokens.css        Primitives — palette, scale, raw values   │  ← never reference directly in components
│                    (--ic-palette-*, --ic-text-*, --ic-space-*)│
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

**Rule:** components and prototypes reference **semantic** aliases (`--color-bg`, `--type-h1`), never primitives (`--ic-palette-blue-500`). This makes theme swaps and brand changes one-file edits.

---

## 1. Principles

- **Calm, not loud.** Generous whitespace. Type does hierarchy, not boxes.
- **Three color roles, kept distinct:**
  - **Brand mark = Blue-500** (`--color-accent`). The logo color. White-on-graphite lockup in the topbar. Rarely surfaces elsewhere in the UI.
  - **Primary CTA = Green-500** (`--color-brand`). The attention-grabbing action color on dense data pages. Used **diligently** — ideally one `btn-primary` per page; every other CTA is `.btn-secondary`. Never decorative.
  - **Chrome = Graphite-800**. The dark topbar background that the white logo sits on. Used directly via `var(--ic-palette-graphite-800)` because it's the one place a raw palette reference is intentional.
- **Status colors are scarce.** Red/yellow/green only signal state — never decoration. (Note: green also doubles as the primary CTA color, which is why CTA placement is so disciplined.)
- **Motion is functional.** `--ic-duration-fast` (120ms) for state, `--ic-duration-base` (200ms) for entry/exit. Nothing decorative.
- **Every new prototype ships with the annotation tool wired up.** When scaffolding `features/<name>/index.html`, you MUST copy the `example.html` `<script>` block — that includes the `?notes=1` annotation IIFE alongside the universal handlers (modals, drawers, dropdowns, tabs, toasts, …). The matching CSS comes for free via `devtools.css` (inlined by `inline.py`). Skipping this leaves the prototype without batch annotation, which is the canonical way to iterate visually with an LLM. No exceptions — even a one-screen demo gets it.

---

## 2. Color

### Primitive palette (`tokens.css`)

10 ramps, each with shades 100–900 (cyan is currently a single shade pending full removal), plus `black` and `white` monochromes. Reference: see `tokens.css`.

| Ramp | Role |
|---|---|
| `gray` | Neutrals for surfaces, borders, text |
| `zinc` | Dark theme neutrals |
| `graphite` | Dark chrome — topbar background, inverse text on dark surfaces |
| `red` | Danger / destructive |
| `yellow` | Warning |
| `orange` | Reserved |
| `green` | **Primary CTA** (`--color-brand`) — and success |
| `cyan` | Single shade only (`cyan-500`) — backs `.tag-blue-light` and `.badge-info` text. Pending removal: those components migrate to blue, then the ramp goes away. |
| `blue` | **Brand mark** (logo, `--color-accent`) — also focus rings and links |
| `purple` | Reserved |

### Semantic aliases (`semantic.css`) — **use these in prototypes**

| Token | Light | Dark |
|---|---|---|
| `--color-bg` | gray-100 | zinc-900 |
| `--color-surface` | white | zinc-800 |
| `--color-surface-muted` | gray-150 | zinc-700 |
| `--color-surface-sunken` | gray-200 | zinc-900 |
| `--color-border` | gray-200 | zinc-600 |
| `--color-border-strong` | gray-300 | zinc-500 |
| `--color-border-focus` | blue-500 | blue-500 |
| `--color-text` | graphite-900 | gray-100 |
| `--color-text-muted` | gray-700 | gray-400 |
| `--color-text-subtle` | gray-500 | gray-600 |
| `--color-text-inverse` | white | zinc-900 |
| `--color-text-link` | blue-500 | blue-500 |
| `--color-brand` | green-500 | green-400 |
| `--color-brand-hover` | green-600 | green-300 |
| `--color-brand-active` | green-700 | green-200 |
| `--color-accent` | blue-500 | blue-500 |
| `--color-success` / `-subtle` | green-500 / green-100 | — |
| `--color-warning` / `-subtle` | yellow-500 / yellow-100 | — |
| `--color-danger` / `-subtle` | red-500 / red-100 | — |
| `--color-info` / `-subtle` | cyan-500 / cyan-100 | — |

Switch theme: `<html data-theme="dark">`.

---

## 3. Typography

Family: `Inter` (loaded by `tokens.css`). Mono: system mono stack.

### Size primitives

| Token | Size | Used in |
|---|---|---|
| `--ic-text-xxs` | 11px | tiny labels |
| `--ic-text-xs`  | 12px | captions |
| `--ic-text-sm`  | 13px | body small |
| `--ic-text-base`| 14px | **default body**, H4 |
| `--ic-text-md`  | 16px | body large, H3 |
| `--ic-text-lg`  | 18px | utility |
| `--ic-text-xl`  | 20px | H2 |
| `--ic-text-2xl` | 28px | H1 |

> ⚠️ **Naming gotcha:** `-md` is **not** the default size — it's the *step above* default. The default body size is `--ic-text-base` (14px). Think of the scale as `base → md → lg → xl → 2xl` rather than `sm → md → lg`.

### Type roles (use these as `font:` shorthand)

| Token | Composition |
|---|---|
| `--type-h1` | semibold 28/42 Inter |
| `--type-h2` | semibold 20/30 Inter |
| `--type-h3` | semibold 16/24 Inter |
| `--type-h4` | semibold 14/22 Inter |
| `--type-body-lg` | regular 16/24 Inter |
| `--type-body` | regular 14/22 Inter |
| `--type-body-sm` | regular 13/20 Inter |
| `--type-caption` | medium 12/18 Inter |
| `--type-mono` | regular 13/20 mono |

```css
h1 { font: var(--type-h1); }
.muted { font: var(--type-body-sm); color: var(--color-text-muted); }
```

Helpers in `components.css`: `.h1` `.h2` `.h3` `.h4` `.body` `.body-sm` `.caption`.

---

## 4. Spacing

4px base. Tokens: `--ic-space-1` (4px) → `--ic-space-16` (128px).

`1=4 · 2=8 · 3=12 · 4=16 · 5=24 · 6=32 · 7=40 · 8=48 · 10=64 · 12=80 · 16=128`

Never write raw px. `padding: var(--ic-space-4) var(--ic-space-5)`.

---

## 5. Radii, Shadow, Motion, Layout

| Group | Tokens |
|---|---|
| Radii (t-shirt) | `--ic-radius-none` 0 · `-sm` 4 · `-md` 8 · `-lg` 12 · `-xl` 16 · `-2xl` 24 · `-full` 9999 |
| Radii (numeric) | `--ic-radius-0` · `-4` · `-8` · `-12` (aliases for none/sm/md/lg) |
| Shadow | `--ic-shadow-xs` · `-sm` · `-md` · `-lg` · `-xl` |
| Motion | `--ic-duration-fast` 120 · `-base` 200 · `-slow` 320 — paired with `--ic-ease`, `--ic-ease-out`, `--ic-ease-in` |
| Z-index | `--ic-z-base` 0 · `-dropdown` 100 · `-sticky` 200 · `-overlay` 800 · `-modal` 900 · `-toast` 1000 |
| Container | `--ic-container-sm` 640 · `-md` 768 · `-lg` 1024 · `-xl` 1280 |

---

## 6. Components

All component CSS lives in `components.css` and references **semantic tokens only**. The shortcode table below is the quick-reference index of every component — drop the root class (or attribute) into prototype markup and the styles apply.

### Shortcode reference

> **Pointing at a component.** Every row below links to a live demo at `example.html#<id>`. To tell a teammate "use this component", share that URL — or click the **`#`** anchor next to any heading in the live showcase to copy the link in one go. The id format is stable: `#buttons`, `#alerts`, `#toasts`, etc.

| Component | Root | Variants / parts |
|---|---|---|
| [Buttons](./example.html#buttons) | `.btn` | `.btn-primary` · `.btn-secondary` · `.btn-ghost` · `.btn-danger` · `.btn-xs` · `.btn-icon-only` |
| [Inputs](./example.html#inputs) | `.field` + `.input` | `.field-label` · `.field-hint` · `.field-hint.is-error` · `.input-xs` |
| [Select](./example.html#inputs) | `.input-select` | `.input-select-trigger` · `.input-select-value` (+ `.dropdown-menu` for options) |
| [Tag input](./example.html#inputs) | `.input-tags` | `.input-tags-input` · `.chip` · `.chip-remove` |
| [Top bar](./example.html#topbar) | `.topbar` | `.topbar-brand` · `.topbar-search` · `.topbar-avatar` |
| [Side navigation](./example.html#sidenav-demo) | `.sidenav` | `.sidenav-item` · `.sidenav-group` · `.sidenav-group-trigger` · `.sidenav-sublist` · `.sidenav-subitem` · `.sidenav-toggle` · `.is-compact` |
| [Switches](./example.html#switches) | `.switch` | `.switch-input` · `.switch-track` |
| [Radios](./example.html#radios) | `.radio` | `.radio-input` · `.radio-circle` · `.radio-label` · `.is-error` |
| [Checkboxes](./example.html#checkboxes) | `.checkbox` | `.checkbox-input` · `.checkbox-box` · `.checkbox-mark` · `.is-error` |
| [Sliders](./example.html#sliders) | `.slider` + `.slider-input` | Native `<input type="range">`. Optional siblings: `.slider-icon` (Phosphor) · `.slider-label` · `.slider-value` (static min/max) · `<output data-slider-output>` (live readout) · `.slider-field` on an `.input.input-xs` number field (two-way sync). Track fill + sync handled by the example.html script block. |
| [Badges](./example.html#badges) | `.badge` | `.badge-success` · `.badge-warning` · `.badge-danger` · `.badge-info`. Interactive: render as `<button class="badge">` (editable); compose `.badge-icon` (leading Phosphor icon) and/or `.badge-remove` (trailing ×, click deletes the pill). |
| [Tags](./example.html#tags) | `.tag` | `.tag-positive` · `.tag-negative` · `.tag-warning` · `.tag-light` · `.tag-dark` · `.tag-blue` · `.tag-indicator` |
| [Count badge](./example.html#badges) | `.count-badge` | `.count-badge-sm` · `.count-badge-lg` · `.count-badge-secondary` |
| [Avatars](./example.html#avatars) | `.avatar` | `.avatar-xs` (16) · `.avatar-sm` (24) · `.avatar-md` (32, default) · `.avatar-lg` (40) · `.avatar-xl` (80) · `.avatar-2xl` (120) · `.avatar-team` (semantic hook for team/company; same neutral fill, icon child differentiates). Render as `<span>` (read-only) or `<button>` / `<a>` (interactive). Content child is one of: `<img>`, 1–2 letters, or `<i class="ph ph-…">`. |
| [Alerts](./example.html#alerts) | `.alert` | `.alert-danger` · `.alert-warning` · `.alert-success` · `.alert-info` · `.alert-icon` · `.alert-message` · `.alert-actions` · `.alert-close` |
| [Toasts](./example.html#toasts) | `.toast-region` + `.toast` | Colors: `.toast-neutral` · `.toast-error` · `.toast-warning` · `.toast-success` · `.toast-info`. Parts: `.toast-icon` · `.toast-message` · `.toast-action` · `.toast-close`. Spawn via `toast({ variant, message, behavior: 'timed'\|'persistent'\|'action', timeout, action: { label, onClick } })`. |
| [Dropdown menu](./example.html#dropdowns) | `.dropdown` | `.dropdown-trigger` · `.dropdown-menu` · `.dropdown-menu-end` · `.dropdown-item` · `.dropdown-item-danger` · `.dropdown-item-icon` · `.dropdown-item-avatar` · `.dropdown-divider` |
| [Modal](./example.html#modals) | `.modal-overlay` + `.modal` | `.modal-{xs,sm,md,lg,xl}` · `.modal-header` · `.modal-body` · `.modal-footer` · `.modal-close` · `[data-modal-open]` / `[data-modal-close]` |
| [Drawer](./example.html#drawers) | `.drawer-overlay` + `.drawer` | `.drawer-{narrow,regular,medium,wide,ultra,full}` · `.drawer-header` · `.drawer-body` · `.drawer-footer` |
| [Breadcrumbs](./example.html#breadcrumbs) | `.breadcrumbs` + `.breadcrumb` | Parent crumbs are `<a class="breadcrumb">` (blue, underline on hover); current page is `<span class="breadcrumb is-current" aria-current="page">` (plain text). Chevron separators render automatically. Usually the first row inside a page head; works standalone. |
| [Page heads](./example.html#page-heads) | `.page-head` | `.page-head-main` · `.page-head-title` · `.page-head-heading` · `.page-head-subtitle` · `.page-head-actions` · count next to the heading uses `.count-badge .count-badge-lg .count-badge-secondary` · optional `.breadcrumbs` as the first row inside `.page-head-main` |
| [Tabs](./example.html#tabs) | `.tabs` + `.tab` | `.is-active` · `role="tablist"` / `role="tab"` / `aria-controls` / `[role="tabpanel"]` |
| [Tooltips](./example.html#tooltips) | `[data-tooltip="…"]` | `[data-placement="bottom\|left\|right"]` (default top) · `[data-tooltip-style="regular"]` for the white wrapping variant with caret (compact dark pill is the default) |
| [Cards](./example.html#cards) | `.card` | `.card-title` · `.card-body` |
| [Tables](./example.html#tables) | `.table` | `.table-wide` · `.table-scroll` · `.th-sort` · `.cell-title` · `.cell-user` · `.cell-avatar` · `.cell-user-meta` · `.cell-meta` · `.cell-meta-sub` · `.cell-dot` (`.is-warning` / `.is-danger`) · `.cell-actions` |
| [Icons](./example.html#iconography) | `<i class="ph ph-{name}">` | Phosphor regular weight loaded via CDN |
| Type helpers | `.h1`–`.h4`, `.body`, `.body-sm`, `.caption` | — |
| Layout helpers | `.stack`, `.row`, `.page`, `.grid-2` | — |
| Annotation tool | `.annot-toolbar` | Append `?notes=1` to any prototype URL. Click "Inspect", click elements to queue notes, "Copy batch" → paste payload to your agent. Notes clear on reload. CSS lives in `devtools.css` (auto-inlined, but not part of the three-layer chain); JS is in the `example.html` script block (copy it with the rest of the delegated handlers). |

### Rules of thumb

- **Compose, don't override.** Stack variants on the root class (`<button class="btn btn-xs btn-primary">`). Don't write new CSS in a feature file — if a variant is missing, add it to `components.css` and re-inline.
- **Stick to semantic tokens.** In any inline styles use `var(--color-*)` / `var(--ic-space-*)` / `var(--type-*)` — never raw palette tokens like `var(--ic-palette-blue-500)`.
- **JS-driven components** (modals, drawers, dropdowns, tabs, alerts, tooltips, tag inputs, character counters) get their behavior from the `<script>` block in `example.html`. When you build a new prototype, copy that whole block — the handlers are delegated and idempotent, so they activate on any markup that uses the right classes / data attributes.
- **Page structure:** wrap content in `<main class="page">` to get the 1024px max-width centered layout.

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
  <i class="ph ph-warning alert-icon"></i>
  <p class="alert-message">Your trial expires in 5 days.</p>
  <div class="alert-actions">
    <button class="btn btn-xs btn-primary">Upgrade</button>
  </div>
  <button class="alert-close" type="button" aria-label="Close"><i class="ph ph-x"></i></button>
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
│   ├── devtools.css             ← author tooling (annotation, debug overlays) — NOT in the layer chain
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
> A feature's `index.html` MUST have the design system inlined into it before it leaves the local checkout. That means the `<link rel="stylesheet" href="../designmd/...">` tags get replaced with `<style>…</style>` blocks containing the actual CSS, and the logo SVG gets inlined too. After inlining, the file has **zero external dependencies** (the only allowed remote reference is the Phosphor icons CDN if the prototype uses Phosphor icons).
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
  <link rel="stylesheet" href="https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css" />
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
> **Boilerplate** — link all three stylesheets plus the Phosphor icon CDN:
>
> ```html
> <link rel="stylesheet" href="../designmd/tokens.css" />
> <link rel="stylesheet" href="../designmd/semantic.css" />
> <link rel="stylesheet" href="../designmd/components.css" />
> <link rel="stylesheet" href="https://unpkg.com/@phosphor-icons/web@2.1.1/src/regular/style.css" />
> ```
>
> Before shipping, run `python3 inline.py ../features/feature-name/index.html` from `designmd/` to bake all CSS into the file. The Phosphor link stays external — it's the one allowed remote dependency.
>
> **Rules:**
> - Use **semantic tokens only** (`--color-bg`, `--color-text`, `--color-brand`, `--type-h1`). NEVER reference primitives like `--ic-palette-*` directly.
> - **Three color roles:** brand mark = blue-500 (`--color-accent`, logo only); primary CTA = green-500 (`--color-brand`, ONE per page — every other CTA is `.btn-secondary`); chrome = graphite-800 (topbar only).
> - Reuse component classes from the §6 shortcode reference (`.btn`, `.card`, `.input`/`.field`, `.alert`, `.tabs`, `.toast`, `.tooltip` via `[data-tooltip]`, `.avatar`, `.table`, `.dropdown`, `.modal`, `.drawer`, `.page-head`, `.sidenav`, `.topbar`, `.badge`, `.tag`, `.chip`, `.switch`, `.radio`, `.checkbox`, etc.). Compose variants on the root (`<button class="btn btn-xs btn-primary">`). Don't author new component CSS in the prototype — if a variant is missing, add it to `components.css` and re-inline.
> - All spacing via `--ic-space-*`. All radii via `--ic-radius-*`. All motion via `--ic-duration-*` + `--ic-ease*`.
> - Status colors (red/yellow/green) only signal state, never decoration.
> - Type is the visual hierarchy. Avoid extra borders, dividers, or background fills.
> - Layout with `.stack` / `.row` / `.grid-2` and flex/grid. Constrain content via `<main class="page">` (1024px max).
> - Icons: `<i class="ph ph-{name}"></i>` (Phosphor regular weight). Inter font already loaded via `tokens.css`.
> - **JS-driven components** (modals, drawers, dropdowns, tabs, alerts, tooltips, toasts, tag inputs, char counters) need the delegated `<script>` block from `designmd/example.html` copied into your prototype — handlers are idempotent and activate on the right classes / `data-*` attributes.
> - **Annotation tool is mandatory.** That same `<script>` block also includes the `?notes=1` annotation IIFE — copy the WHOLE block; do not strip out the annotation function. Append `?notes=1` to the prototype URL to enable the in-page batch annotation toolbar. The matching CSS lives in `devtools.css` and is auto-inlined by `inline.py`, so no extra `<link>` tag is needed.
