#!/usr/bin/env python3
"""new-prototype.py — scaffold a feature prototype by duplicating template/.

    python3 tools/new-prototype.py billing-portal --title "Billing portal" --nav Initiatives
    python3 tools/new-prototype.py billing-portal --title "Billing portal" \
        --new-nav Billing --nav-icon i-credit-card
    python3 tools/new-prototype.py --thumb billing-portal

The point is that nothing here is generated. `template/index.html` is a real
file that lints and inlines like any other prototype, so the shell a new
feature starts from is the shell the system currently ships — not whatever an
agent remembered about it. Change the top bar in components.css, update the
template once, and every prototype made afterwards has it.

Three things happen on a scaffold:
  1. template/index.html is copied to <features>/<name>/index.html with the
     title substituted and the sidenav resolved (one existing item marked
     active, or a new item inserted).
  2. A card is registered in <features>/index.html, in alphabetical order, so
     the feature is listed from minute one rather than when someone remembers.
  3. status.json gets an entry, defaulting to in-progress.

The thumbnail is deliberately NOT shot here: at scaffold time the page is an
empty shell, and a card carrying a screenshot of nothing is worse than a card
carrying none. Run `--thumb` once there is something to look at; it is
re-runnable and overwrites in place.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                      # designmd/
TEMPLATE = ROOT / 'template' / 'index.html'

# Where prototypes live in Toptal's working layout: a sibling of designmd/.
# `features` inside the repo is a symlink to it; resolve() follows that, so a
# standalone clone without the sibling falls through to a clear error.
DEFAULT_FEATURES = ROOT.parent / 'features'

NAME_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
CARD_RE = re.compile(r'<a class="card"[^>]*href="\./([^/"]+)/"')
THUMB_URL = 'http://localhost:5733/{name}/'
CHROME_CANDIDATES = [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
    'google-chrome', 'chromium', 'chromium-browser',
]


def die(msg):
    print(f'✗ {msg}', file=sys.stderr)
    sys.exit(1)


def titleise(name):
    """billing-portal -> Billing portal. Sentence case, matching the kit."""
    words = name.split('-')
    return ' '.join([words[0].capitalize()] + words[1:])


# ---------------------------------------------------------------- sidenav

def set_active_nav(html, label):
    """Mark the existing .sidenav-item whose label is `label` active.

    Matches on the label text rather than a data attribute so the template
    stays plain kit markup with nothing extra to explain.
    """
    pattern = re.compile(
        r'(<a class="sidenav-item)(" href="#">(?:(?!</a>).)*?'
        r'<span class="sidenav-item-label">' + re.escape(label) + r'</span>)',
        re.S)
    html, n = pattern.subn(r'\1 is-active\2', html, count=1)
    if not n:
        known = re.findall(r'<a class="sidenav-item" href="#">.*?'
                           r'<span class="sidenav-item-label">([^<]+)</span>', html, re.S)
        die(f'no sidenav item named {label!r}. The template has: ' + ', '.join(known))
    return html


def insert_nav(html, label, icon):
    """Add a new top-level nav item, active, at the end of .sidenav-list."""
    item = (f'        <li><a class="sidenav-item is-active" href="#">'
            f'<svg class="sidenav-item-icon"><use href="#{icon}"/></svg>'
            f'<span class="sidenav-item-label">{label}</span></a></li>\n')
    marker = '      </ul>\n      <div class="sidenav-spacer">'
    if marker not in html:
        die('could not find the end of .sidenav-list in the template')
    return html.replace(marker, item + marker, 1)


# ---------------------------------------------------------- features index

def register_card(index_file, name, title, desc):
    """Insert a card into features/index.html, alphabetical by folder."""
    html = index_file.read_text(encoding='utf8')
    if f'href="./{name}/"' in html:
        return 'already listed'

    card = (f'      <a class="card" href="./{name}/">\n'
            f'        <div class="card-meta">\n'
            f'          <h3 class="card-title">{title} <span class="arrow">&rarr;</span></h3>\n'
            f'          <p class="card-body">{desc}</p>\n'
            f'          <span class="folder">{name}/</span>\n'
            f'        </div>\n'
            f'      </a>\n')

    # Slot it before the first card whose folder sorts after this one; if this
    # one sorts last, go in just before the list closes.
    for m in CARD_RE.finditer(html):
        if m.group(1) > name:
            start = html.rfind('\n', 0, m.start()) + 1
            return _write(index_file, html[:start] + card + html[start:], 'card added')

    end = html.find('</section>', html.find('id="feature-list"'))
    if end < 0:
        return 'could not find #feature-list — add the card by hand'
    start = html.rfind('\n', 0, end) + 1
    return _write(index_file, html[:start] + card + html[start:], 'card added')


def _write(path, text, msg):
    path.write_text(text, encoding='utf8')
    return msg


def register_status(features, name, status):
    f = features / 'status.json'
    if not f.exists():
        return 'no status.json'
    data = json.loads(f.read_text(encoding='utf8'))
    if name in data:
        return 'already in status.json'
    data[name] = status
    # Keep the "_values" legend first, then the folders alphabetically.
    ordered = {'_values': data.pop('_values')} if '_values' in data else {}
    ordered.update({k: data[k] for k in sorted(data)})
    f.write_text(json.dumps(ordered, indent=2) + '\n', encoding='utf8')
    return f'status: {status}'


# -------------------------------------------------------------- thumbnail

def find_chrome():
    for c in CHROME_CANDIDATES:
        if Path(c).exists():
            return c
        found = shutil.which(c)
        if found:
            return found
    return None


def shoot_thumb(features, name, url):
    chrome = find_chrome()
    if not chrome:
        die('no headless Chrome found. Install Chrome, or pass --chrome <path>.')
    thumbs = features / '_thumbs'
    thumbs.mkdir(exist_ok=True)
    out = thumbs / f'{name}.png'
    cmd = [chrome, '--headless', '--disable-gpu', '--hide-scrollbars',
           '--window-size=1280,800', '--virtual-time-budget=4000',
           f'--screenshot={out}', url]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if not out.exists():
        die(f'Chrome wrote no file. Is the server up at {url}?\n{r.stderr.strip()[:400]}')
    print(f'  shot {out.relative_to(features)} from {url}')

    # Put the <img> into the card if it is not there yet.
    index_file = features / 'index.html'
    if index_file.exists():
        html = index_file.read_text(encoding='utf8')
        anchor = f'<a class="card" href="./{name}/">'
        i = html.find(anchor)
        if i < 0:
            print('  card not found in index.html — add the <img> by hand')
        elif f'_thumbs/{name}.png' in html:
            print('  card already references the thumbnail')
        else:
            title = re.search(r'<h3 class="card-title">([^<]*)', html[i:i + 600])
            alt = (title.group(1).strip() if title else name) + ' screenshot'
            img = (f'\n        <img class="thumb" src="./_thumbs/{name}.png" '
                   f'alt="{alt}" loading="lazy" />')
            j = i + len(anchor)
            index_file.write_text(html[:j] + img + html[j:], encoding='utf8')
            print('  card now shows the thumbnail')


# ------------------------------------------------------------------- main

def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('name', help='kebab-case folder name, e.g. billing-portal')
    p.add_argument('--title', help='human title (default: derived from the name)')
    p.add_argument('--desc', help='card body in features/index.html')
    p.add_argument('--nav', help='existing sidenav section to mark active, e.g. Initiatives')
    p.add_argument('--new-nav', dest='new_nav', help='label for a brand-new sidenav item')
    p.add_argument('--nav-icon', dest='nav_icon', default='i-overview',
                   help='icon slug for --new-nav (default: i-overview)')
    p.add_argument('--into', help='prototypes folder (default: the features/ sibling)')
    p.add_argument('--status', default='in-progress', help='status.json value')
    p.add_argument('--no-register', dest='register', action='store_false',
                   help='write the folder only — leave index.html and status.json alone '
                        '(throwaway scaffolds, previews, and layouts with no feature index)')
    p.add_argument('--thumb', action='store_true',
                   help='shoot the 1280x800 thumbnail for an existing prototype and stop')
    p.add_argument('--url', help='page to shoot for --thumb (default: the local prototypes server)')
    p.add_argument('--force', action='store_true', help='overwrite an existing folder')
    a = p.parse_args()

    if not NAME_RE.match(a.name):
        die(f'{a.name!r} is not kebab-case. Use letters, digits and single hyphens.')

    features = Path(a.into).resolve() if a.into else DEFAULT_FEATURES.resolve()
    if not features.is_dir():
        die(f'no prototypes folder at {features}. Pass --into <path>.')

    if a.thumb:
        if not (features / a.name).is_dir():
            die(f'{features / a.name} does not exist')
        shoot_thumb(features, a.name, a.url or THUMB_URL.format(name=a.name))
        return

    if a.nav and a.new_nav:
        die('pass --nav or --new-nav, not both')
    if not a.nav and not a.new_nav:
        die('say where this sits in the sidenav: --nav "Initiatives" (mark an '
            'existing section active) or --new-nav "Billing" --nav-icon i-credit-card')

    if not TEMPLATE.is_file():
        die(f'the template is missing: {TEMPLATE}')

    target = features / a.name
    if target.exists() and not a.force:
        die(f'{target} already exists. Pass --force to overwrite it.')

    title = a.title or titleise(a.name)
    desc = a.desc or f'{title}. Scaffolded, not yet built.'

    html = TEMPLATE.read_text(encoding='utf8')
    html = set_active_nav(html, a.nav) if a.nav else insert_nav(html, a.new_nav, a.nav_icon)
    html = (html.replace('{{FEATURE_TITLE}}', title)
                .replace('{{FEATURE_NAME}}', a.name))

    target.mkdir(parents=True, exist_ok=True)
    (target / 'index.html').write_text(html, encoding='utf8')

    print(f'✓ {target / "index.html"}')
    print(f'  from {TEMPLATE.relative_to(ROOT.parent)}')
    print(f'  nav: ' + (f'{a.nav} marked active' if a.nav else f'new item {a.new_nav!r} ({a.nav_icon})'))

    index_file = features / 'index.html'
    if not a.register:
        print('  not listed (--no-register)')
    else:
        if index_file.exists():
            print(f'  index.html: {register_card(index_file, a.name, title, desc)}')
        print(f'  {register_status(features, a.name, a.status)}')

    rel = target.relative_to(features)
    print('\nNext:')
    print(f'  build the feature in {features.name}/{rel}/index.html, from dist/kit.json')
    print(f'  python3 lint.py {features}/{a.name}/index.html')
    print(f'  python3 tools/new-prototype.py {a.name} --thumb       # once there is something to see')
    print(f'  python3 inline.py {features}/{a.name}/index.html      # before you share it')


if __name__ == '__main__':
    main()
