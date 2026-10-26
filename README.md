# designmd

A plain HTML/CSS extension of **[Picasso](https://github.com/toptal/picasso)**, Toptal's
production design system, built so Operationalize can prototype quickly and hand over
something that translates.

**Picasso is the source of truth.** Its [Storybook](https://toptal.github.io/picasso/)
and `packages/base/<Component>/src/` define what a component is and what a token is worth.
designmd re-expresses those foundations as three stylesheets a browser can load directly —
no React, no build step — so a screen can exist in hours rather than days.

Every token here is either Picasso's, name and value verbatim, or marked `extension` with
a reason in its own comment. Where the two disagree, Picasso is right and this is a bug.

```
tokens.css      primitives — Picasso's palette, scale and shadows
semantic.css    intent aliases — --color-bg, --type-h1
components.css  the component classes
example.html    the showcase: every token and component, live
design.md       the full reference, and the file to paste into an LLM
figma-map.json  the registry binding each class to its Picasso React component
```

Open `example.html` to browse the system, or `design.md` to read it. Prototypes live in the
sibling `features/` folder and are shipped as single self-contained HTML files — `inline.py`
bakes the stylesheets, the icon sprite and the fonts into each one.
