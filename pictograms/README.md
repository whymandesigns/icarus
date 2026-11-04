# Pictograms

The workspace for new pictograms and line illustrations in Toptal's pictogram style.
Explore here; move what's signed off into `approved/`; prototypes take from there.

```
pictograms/
├── index.html          the board — generated, don't edit
├── approved/           signed-off pictograms, flat, kebab-case names
└── explorations/
    └── <topic>/        one folder per brief: rob-meetings, initiatives, …
        ├── notes.md    first line shows on the board; the rest is the brief
        ├── *.svg       candidates
        └── ref-*.svg   library references (imported from Figma), shown as refs
```

How to draw one and the style rules live in the `pictogram` skill
(`.claude/skills/pictogram/SKILL.md`); the tool is `tools/pictogram.py`. Ask Claude
for "a pictogram for …" in a session working in `designmd/` and it works in here.
One designer maintains this flow.

## Commands

Run from `designmd/`.

```bash
python3 tools/pictogram.py board                                     # rebuild index.html
python3 tools/pictogram.py lint pictograms/explorations/<topic>/*.svg
python3 tools/pictogram.py approve pictograms/explorations/<topic>/<name>.svg [--as <name>]
```

`approve` lints first and refuses on any error, refuses `ref-*` files, won't overwrite
an existing approved name, then moves the file and rebuilds the board.

## Viewing the board

Start the `designmd` dev server (`designmd/.claude/launch.json`) and open
`/pictograms/index.html`, or run `python3 -m http.server` in this folder. The board renders every pictogram inside
`.pictogram.is-filled` with designmd's own CSS, so what you see is what ships.

## Using an approved pictogram

Prototypes in `features/` take pictograms from `designmd/pictograms/approved/`.

Paste the SVG inside the wrapper:

```html
<span class="pictogram is-filled"><svg viewBox="0 0 64 64" …>…</svg></span>
```

Add `.is-muted` for disabled or secondary states.
