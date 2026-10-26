/* versions.js — the Versions + Changes plugins. Pairs with versions.css.
 *
 * For a feature that is prototyped in several versions (variants) side by
 * side, e.g.
 *
 *   features/<feature>/versions.json
 *   features/<feature>/v1-<name>/index.html
 *   features/<feature>/v2-<name>/index.html …
 *
 * Each version declares the family in its <head>:
 *
 *   <meta name="icarus-versions" content="../versions.json" />
 *
 * Without that tag this file does nothing, and the plugin launcher greys both
 * plugins out — they only exist on features that have versions.
 *
 *   Versions  ?versions=1  a panel, shaped like the States switcher: every
 *                          version in the family, the current one marked;
 *                          click one or use Alt+← / Alt+→ to move.
 *                          Switching keeps the query and hash, so the same
 *                          state (?states=1&state=…) opens in the other version.
 *   Changes   ?changes=1   outlines what is new / moved / changed in this
 *                          version compared with the one it is basedOn. The
 *                          markup carries the markers:
 *                            data-change="new|moved|changed"
 *                            data-change-note="Short reason"
 *
 * versions.json:
 *   { "family": "…", "versions": [
 *       { "folder": "v1-drawer", "label": "v1 · Drawer", "date": "2026-10-01",
 *         "note": "One line on what it is", "basedOn": null },
 *       { "folder": "v2-full-screen", …, "basedOn": "v1-drawer" } ] }
 *
 * Like the other plugins, toggling reloads (the launcher sets the parameter);
 * the page always boots into a known state. See versions.html.
 */
(() => {
  if (window.__icarusVersions) return;
  window.__icarusVersions = true;

  const meta = document.querySelector('meta[name="icarus-versions"]');
  if (!meta) return;

  const params = new URLSearchParams(location.search);
  const barOn = params.get('versions') === '1';
  const changesOn = params.get('changes') === '1';
  const manifestUrl = new URL(meta.getAttribute('content') || '../versions.json', location.href);
  const here = location.pathname.replace(/index\.html$/, '').split('/').filter(Boolean).pop();
  const esc = v => String(v ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  // Outline the markers straight away; the legend fills in once the manifest is read.
  if (changesOn) document.documentElement.classList.add('vr-changes');
  if (!barOn && !changesOn) return;

  const href = v => new URL(`${v.folder}/`, manifestUrl).pathname + location.search + location.hash;
  const setParam = (key, on) => {
    const p = new URLSearchParams(location.search);
    p.set(key, on ? '1' : '0');
    location.search = p.toString();
  };

  fetch(manifestUrl, { cache: 'no-store' }).then(r => r.json()).then(({ family, versions = [] }) => {
    const i = versions.findIndex(v => v.folder === here);
    const cur = versions[i];
    const base = cur?.basedOn ? versions.find(v => v.folder === cur.basedOn) : null;
    // Count distinct changes — the same marker can appear in create and view mode.
    const marks = new Set([...document.querySelectorAll('[data-change]')].map(el => `${el.dataset.change}:${el.dataset.changeNote || ''}`)).size;

    // One panel, shaped like the States switcher: dark title bar, white body,
    // a group per concern. The version list is the body's first group; the
    // changes toggle and legend follow it.
    let body = '';
    if (barOn) {
      body += `<div class="vr-group"><span>Versions</span>
        ${versions.map(v => `<a class="vr-item${v.folder === here ? ' is-current' : ''}" href="${esc(href(v))}"${v.folder === here ? ' aria-current="page"' : ''}>${esc(v.label)}${v.note ? `<small>${esc(v.note)}</small>` : ''}</a>`).join('')}
      </div>`;
      if (marks) body += `<div class="vr-group"><span>Changes</span>
        <button type="button" class="vr-changes-toggle${changesOn ? ' is-on' : ''}" data-vr-changes>${changesOn ? 'Hide' : 'Show'} changes</button>
      </div>`;
    }
    if (changesOn) {
      body += marks
        ? `<div class="vr-legend"><strong>${marks} change${marks === 1 ? '' : 's'}</strong>${base ? `vs ${esc(base.label)}` : ''}
        <span><i class="vr-new"></i>New</span><span><i class="vr-moved"></i>Moved</span><span><i class="vr-changed"></i>Changed</span></div>`
        : `<div class="vr-legend">No changes marked in this version${base ? ` (vs ${esc(base.label)})` : ''}</div>`;
    }
    document.body.insertAdjacentHTML('beforeend', `<div class="vr-dock" role="navigation" aria-label="${esc(family || 'Versions')}">
      <div class="vr-head"><span>${esc(family || 'Versions')}</span><button type="button" class="vr-collapse" aria-label="Collapse">\u2013</button></div>
      <div class="vr-body">${body}</div>
    </div>`);

    // Collapse to the title bar, remembered for the session like the switcher
    const dock = document.querySelector('.vr-dock');
    const CKEY = 'vr:collapsed';
    try { if (sessionStorage.getItem(CKEY) === '1') dock.classList.add('is-collapsed'); } catch {}
    const cbtn = dock.querySelector('.vr-collapse');
    const paintCollapse = () => {
      const on = dock.classList.contains('is-collapsed');
      cbtn.textContent = on ? '+' : '\u2013';
      cbtn.setAttribute('aria-label', on ? 'Expand' : 'Collapse');
    };
    paintCollapse();
    cbtn.addEventListener('click', () => {
      dock.classList.toggle('is-collapsed');
      try { sessionStorage.setItem(CKEY, dock.classList.contains('is-collapsed') ? '1' : '0'); } catch {}
      paintCollapse();
    });


    const step = d => { const v = versions[i + d]; if (v) location.href = href(v); };
    document.addEventListener('click', e => {
      if (e.target.closest('[data-vr-changes]')) setParam('changes', !changesOn);
    });
    if (barOn) document.addEventListener('keydown', e => {
      if (!e.altKey || (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight')) return;
      e.preventDefault();
      step(e.key === 'ArrowRight' ? 1 : -1);
    });
  }).catch(() => {});
})();
