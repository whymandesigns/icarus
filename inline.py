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
- Adds the review bar (review.css inside the style block + review.js in a
  `<script>` before `</body>`). It is dormant until the prototype is opened
  with `?review=1`. `--only-review` injects/refreshes just that, for prototypes
  that do not use the design-system CSS at all.
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
import base64

ROOT = os.path.dirname(os.path.abspath(__file__))

def read(name):
    with open(os.path.join(ROOT, name)) as f:
        return f.read()

def embed_fonts(css):
    # Replace self-hosted font url('fonts/x.woff2') with base64 data URIs so an
    # inlined prototype carries the fonts with it (no external font files).
    def repl(m):
        path = os.path.join(ROOT, m.group(1))
        if not os.path.exists(path):
            return m.group(0)
        b64 = base64.b64encode(open(path, 'rb').read()).decode('ascii')
        return f"url(data:font/woff2;base64,{b64}) format('woff2')"
    return re.sub(r"url\('(fonts/[^']+\.woff2)'\)\s*format\('woff2'\)", repl, css)

def build_style_block():
    # The three-layer chain (tokens → semantic → components) is followed by
    # devtools.css — auto-inlined for convenience but explicitly NOT part of
    # the layer chain. See design.md §7 and devtools.css's own header for why.
    return (
        '<style>\n'
        '    /* === tokens.css === */\n' + embed_fonts(read('tokens.css')) + '\n'
        '    /* === semantic.css === */\n' + read('semantic.css') + '\n'
        '    /* === components.css === */\n' + read('components.css') + '\n'
        '    /* === devtools.css === */\n' + read('devtools.css') + '\n'
        '    /* === review.css === */\n' + read('review.css') + '\n'
        '  </style>'
    )

def build_inline_logo():
    logo = read('assets/logo.svg')
    # Apply the topbar-brand-logo class for sizing
    return logo.replace('<svg ', '<svg class="topbar-brand-logo" ', 1).replace('\n', '')

REVIEW_OPEN = '<!-- === review.js === -->'
REVIEW_CLOSE = '<!-- === /review.js === -->'

def build_review_script():
    # The review bar (comments, inline text edits, spotlight) — see review.js.
    return REVIEW_OPEN + '\n<script>\n' + read('review.js').strip() + '\n</script>\n' + REVIEW_CLOSE

# Standalone review-bar CSS for prototypes that don't carry the design system
REVIEW_STYLE_OPEN = '<!-- === review.css === -->'
REVIEW_STYLE_CLOSE = '<!-- === /review.css === -->'

def build_review_style():
    return REVIEW_STYLE_OPEN + '\n<style>\n' + read('review.css').strip() + '\n</style>\n' + REVIEW_STYLE_CLOSE

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
BODY_END_PATTERN = re.compile(r'</body>')
REVIEW_PATTERN = re.compile(re.escape(REVIEW_OPEN) + r'.*?' + re.escape(REVIEW_CLOSE), re.DOTALL)
REVIEW_STYLE_PATTERN = re.compile(re.escape(REVIEW_STYLE_OPEN) + r'.*?' + re.escape(REVIEW_STYLE_CLOSE), re.DOTALL)
# Phosphor CDN link — no longer used; strip it if present
PHOSPHOR_PATTERN = re.compile(r'\s*<link[^>]*@phosphor-icons[^>]*>\s*\n?')

def add_review(html, with_style):
    # Review bar script — refresh an existing block, else inject before </body>.
    # with_style also carries review.css standalone (prototypes without the system CSS).
    parts = (build_review_style() + '\n' if with_style else '') + build_review_script()
    if with_style and REVIEW_STYLE_PATTERN.search(html):
        html = REVIEW_STYLE_PATTERN.sub(lambda _: build_review_style(), html)
        if REVIEW_PATTERN.search(html):
            html = REVIEW_PATTERN.sub(lambda _: build_review_script(), html)
        else:
            html = BODY_END_PATTERN.sub(lambda _: build_review_script() + '\n</body>', html, count=1)
        return html, 'refreshed review bar (css + js)'
    if REVIEW_PATTERN.search(html):
        html, n = REVIEW_PATTERN.subn(lambda _: build_review_script(), html)
        return html, f'refreshed review bar ({n} block)'
    if BODY_END_PATTERN.search(html):
        html = BODY_END_PATTERN.sub(lambda _: parts + '\n</body>', html, count=1)
        return html, 'injected review bar before </body>'
    return html, 'no </body> found — review bar NOT injected'

def inline_review_only(path):
    with open(path) as f:
        html = f.read()
    html, status = add_review(html, with_style=True)
    with open(path, 'w') as f:
        f.write(html)
    print(f'  {status}')
    print(f'  final size: {os.path.getsize(path):,} bytes')

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

    # Review bar — CSS already travels in the style block; add/refresh the script
    html, review_status = add_review(html, with_style=False)

    with open(path, 'w') as f:
        f.write(html)

    size = os.path.getsize(path)
    print(f'  {css_status}')
    print(f'  {logo_status}')
    print(f'  {sprite_status}')
    print(f'  {review_status}')
    print(f'  final size: {size:,} bytes')

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    only_review = '--only-review' in sys.argv
    if not args:
        print('Usage: python3 inline.py [--only-review] <prototype.html> [more.html ...]')
        sys.exit(1)
    for path in args:
        print(f'\n{path}')
        if not os.path.exists(path):
            print('  not found, skipping')
            continue
        (inline_review_only if only_review else inline)(path)

if __name__ == '__main__':
    main()
