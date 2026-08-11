#!/usr/bin/env python3
"""
inline.py — inline the design system CSS + logo into a prototype HTML file.

Usage:
    python3 inline.py <prototype.html>

What it does:
- Replaces a `<link rel="stylesheet" href="./tokens.css" />` (+ semantic + components)
  block with one `<style>...</style>` block containing all three files concatenated.
- Replaces an `<img src="./assets/logo.svg" ...>` with an inline `<svg>`.
- Works in-place: edits the file. Idempotent — running it twice re-inlines the
  latest CSS without ballooning the file.

What it deliberately does NOT touch:
- The Phosphor icons CDN link (`https://unpkg.com/@phosphor-icons/web/...`).
  This is the one allowed remote dependency in inlined prototypes — features that
  use `<i class="ph ph-…">` icons keep them by loading Phosphor from unpkg.
- Any additional inline `<style>` blocks in the prototype (e.g. one-off layout
  styles a feature needs). Only the design-system block bounded by the
  `/* === tokens.css === */` marker is replaced; everything else survives.

Workflow:
- Prototypes can use either form:
  1. `<link rel="stylesheet" href="./tokens.css" />`  ← source form, easy to edit
  2. `<style>/* === tokens.css === */ ... </style>`   ← inlined form, ready to deploy
- This script converts (1) → (2). To "refresh" an inlined prototype after editing
  the system CSS, edit the link form first OR just re-run the script — the markers
  inside the existing <style> block are detected and replaced.
"""

import re
import sys
import os

ROOT = os.path.dirname(os.path.abspath(__file__))

def read(name):
    with open(os.path.join(ROOT, name)) as f:
        return f.read()

def build_style_block():
    # The three-layer chain (tokens → semantic → components) is followed by
    # devtools.css — auto-inlined for convenience but explicitly NOT part of
    # the layer chain. See design.md §7 and devtools.css's own header for why.
    return (
        '<style>\n'
        '    /* === tokens.css === */\n' + read('tokens.css') + '\n'
        '    /* === semantic.css === */\n' + read('semantic.css') + '\n'
        '    /* === components.css === */\n' + read('components.css') + '\n'
        '    /* === devtools.css === */\n' + read('devtools.css') + '\n'
        '  </style>'
    )

def build_inline_logo():
    logo = read('assets/logo.svg')
    # Apply the topbar-brand-logo class for sizing
    return logo.replace('<svg ', '<svg class="topbar-brand-logo" ', 1).replace('\n', '')

SPRITE_OPEN = '<!-- === icons.svg === -->'
SPRITE_CLOSE = '<!-- === /icons.svg === -->'

def build_icon_sprite():
    # The custom Figma icon sprite (designmd/icons.svg) — inlined so prototypes
    # are fully self-contained. Referenced via <svg class="icon"><use href="#i-…"></svg>.
    return SPRITE_OPEN + '\n' + read('icons.svg').strip() + '\n' + SPRITE_CLOSE

# Pattern A: source form — optional comment block + 3 <link> tags
LINK_PATTERN = re.compile(
    r'(<!--.*?-->\s*\n\s*)?'
    r'<link[^>]*tokens\.css[^>]*/>\s*\n\s*'
    r'<link[^>]*semantic\.css[^>]*/>\s*\n\s*'
    r'<link[^>]*components\.css[^>]*/>',
    re.DOTALL
)

# Pattern B: previously-inlined form — replace the existing <style> block
STYLE_PATTERN = re.compile(
    r'<style>\s*/\* === tokens\.css === \*/.*?</style>',
    re.DOTALL
)

# Image patterns
IMG_PATTERN = re.compile(r'<img class="topbar-brand-logo"[^>]*src="[^"]*logo\.svg"[^>]*/?>')
INLINE_LOGO_PATTERN = re.compile(r'<svg class="topbar-brand-logo"[^>]*>.*?</svg>', re.DOTALL)

# Icon sprite — previously-injected block (idempotent refresh) + <body> anchor
SPRITE_PATTERN = re.compile(re.escape(SPRITE_OPEN) + r'.*?' + re.escape(SPRITE_CLOSE), re.DOTALL)
BODY_PATTERN = re.compile(r'(<body[^>]*>)')
# Phosphor CDN link — no longer used; strip it if present
PHOSPHOR_PATTERN = re.compile(r'\s*<link[^>]*@phosphor-icons[^>]*>\s*\n?')

def inline(path):
    with open(path) as f:
        html = f.read()

    style_block = build_style_block()
    inline_logo = build_inline_logo()

    # CSS — try replacing the existing inlined block first; fall back to link tags
    if STYLE_PATTERN.search(html):
        html, n = STYLE_PATTERN.subn(style_block, html)
        css_status = f'refreshed inline CSS ({n} block)'
    else:
        html, n = LINK_PATTERN.subn(style_block, html)
        css_status = f'inlined {n} CSS link block(s)' if n else 'no CSS links found'

    # Logo — try replacing existing inline SVG first; fall back to <img>
    if INLINE_LOGO_PATTERN.search(html):
        html, m = INLINE_LOGO_PATTERN.subn(inline_logo, html)
        logo_status = f'refreshed inline logo ({m} svg)'
    else:
        html, m = IMG_PATTERN.subn(inline_logo, html)
        logo_status = f'inlined {m} logo img(s)' if m else 'no logo found'

    # Phosphor CDN is retired — strip any leftover link
    html, ph = PHOSPHOR_PATTERN.subn('\n', html)

    # Icon sprite — refresh an existing injected block, else inject right after <body>
    sprite = build_icon_sprite()
    if SPRITE_PATTERN.search(html):
        html, s = SPRITE_PATTERN.subn(lambda _: sprite, html)
        sprite_status = f'refreshed icon sprite ({s} block)'
    elif BODY_PATTERN.search(html):
        html, s = BODY_PATTERN.subn(lambda mo: mo.group(1) + '\n  ' + sprite, html, count=1)
        sprite_status = f'injected icon sprite after <body>'
    else:
        sprite_status = 'no <body> found — icon sprite NOT injected'
    if ph:
        sprite_status += f' · stripped {ph} Phosphor link(s)'

    with open(path, 'w') as f:
        f.write(html)

    size = os.path.getsize(path)
    print(f'  {css_status}')
    print(f'  {logo_status}')
    print(f'  {sprite_status}')
    print(f'  final size: {size:,} bytes')

def main():
    if len(sys.argv) < 2:
        print('Usage: python3 inline.py <prototype.html> [more.html ...]')
        sys.exit(1)
    for path in sys.argv[1:]:
        print(f'\n{path}')
        if not os.path.exists(path):
            print('  not found, skipping')
            continue
        inline(path)

if __name__ == '__main__':
    main()
