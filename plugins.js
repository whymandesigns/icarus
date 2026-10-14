/* plugins.js — the plugin launcher. Pairs with plugins.css.
 *
 * One floating button that turns the author plugins on and off:
 *
 *   Review bar      ?review=1   comment, retype copy, spotlight          (review.js)
 *   States switcher ?states=1   jump between a prototype's designed states
 *   Component map   ?map=1      cross-reference components to Picasso
 *
 * Each plugin still owns its own behaviour and its own URL parameter; this only
 * gathers the switches into one place, so a prototype shows one unobtrusive
 * button instead of a button bottom-right, a panel bottom-left and nothing at
 * all for the third.
 *
 * Toggling always reloads. Every one of these plugins decides what to do at
 * boot — stamp the page, replay a state, render a bar — so flipping them live
 * would mean three teardown paths that only ever run in author tooling. A
 * reload is one path, and the page always starts in a known state.
 *
 * A plugin appears in the panel only if it is actually on the page; the rest
 * are listed greyed out, so the launcher tells the truth about what this page
 * carries rather than offering a switch that does nothing.
 */
(() => {
  if (window.__icarusLauncher) return;            // never mount twice
  window.__icarusLauncher = true;
  document.documentElement.classList.add('pg-has-launcher');   // review.js hides its own button

  const P = () => new URLSearchParams(location.search);
  const isOn = key => P().get(key) === '1';

  /* ── What this page actually carries ──────────────────────────────
     Detection is deliberately structural rather than a flag each plugin
     has to set, so a prototype that was built before the launcher existed
     still lights up correctly. */
  const DETECT = {
    // review.js announces itself; fall back to the bar/toggle it leaves behind
    review: () => !!(window.__icarusReview || document.querySelector('.rv-toggle, #rvBar')),
    // switchers are hand-copied with a per-prototype prefix (in-, ws-, pr-, …),
    // so the stable hook is the id suffix rather than a class
    states: () => !!document.querySelector('[id$="-switcher"]'),
    // the kit's goggles button, or a page that ships the registry
    map:    () => !!document.querySelector('.map-toggle') || !!window.__icarusComponentMap,
  };

  const PLUGINS = [
    { key: 'review', name: 'Review bar',      on: 'Comment, retype copy, spotlight a region.',
      off: 'Not on this page — inline.py adds it.' },
    { key: 'states', name: 'States switcher', on: "Jump between this prototype's designed states.",
      off: 'This prototype has no states defined.' },
    { key: 'map',    name: 'Component map',   on: 'Cross-reference components to React / Storybook.',
      off: 'Only on the component kit for now.' },
  ];

  const ICON = '<svg viewBox="0 0 20 20" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M7.5 3h-3A1.5 1.5 0 0 0 3 4.5v3A1.5 1.5 0 0 0 4.5 9h3A1.5 1.5 0 0 0 9 7.5v-3A1.5 1.5 0 0 0 7.5 3Z"/><path d="M15.5 3h-3A1.5 1.5 0 0 0 11 4.5v3A1.5 1.5 0 0 0 12.5 9h3A1.5 1.5 0 0 0 17 7.5v-3A1.5 1.5 0 0 0 15.5 3Z"/><path d="M7.5 11h-3A1.5 1.5 0 0 0 3 12.5v3A1.5 1.5 0 0 0 4.5 17h3A1.5 1.5 0 0 0 9 15.5v-3A1.5 1.5 0 0 0 7.5 11Z"/><path d="M14 11.5v5M11.5 14h5"/></svg>';

  let open = false;

  /* Flipping a plugin: the parameter is set explicitly either way rather than
     deleted, because the plugins disagree about what a missing parameter means
     — the review bar remembers its last state in localStorage, so it needs a
     literal review=0 to be told to stop. */
  function toggle(key) {
    const p = P();
    p.set(key, isOn(key) ? '0' : '1');
    location.search = p.toString();
  }

  function render() {
    document.getElementById('pgPanel')?.remove();
    document.body.classList.toggle('pg-open', open);

    const live = PLUGINS.filter(x => DETECT[x.key]() && isOn(x.key)).length;
    const fab = document.getElementById('pgFab');
    fab.classList.toggle('on', live > 0);
    fab.setAttribute('aria-expanded', String(open));
    fab.innerHTML = ICON + (live ? `<span class="pg-count">${live}</span>` : '');

    if (!open) return;

    const rows = PLUGINS.map(x => {
      const here = DETECT[x.key]();
      const on = here && isOn(x.key);
      return `<button class="pg-item${on ? ' is-on' : ''}" type="button" data-pg="${x.key}"${here ? '' : ' disabled'}>
          <span><span class="pg-name">${x.name}</span><span class="pg-why">${here ? x.on : x.off}</span></span>
          <span class="pg-switch"></span>
        </button>`;
    }).join('');

    document.body.insertAdjacentHTML('beforeend', `
      <div class="pg-panel" id="pgPanel" role="dialog" aria-label="Plugins">
        <div class="pg-head">Plugins<button type="button" data-pg-close aria-label="Close">×</button></div>
        <div class="pg-list">${rows}</div>
        <div class="pg-foot">Switching one reloads the page, so it starts clean.</div>
      </div>`);
  }

  function mount() {
    document.body.insertAdjacentHTML('beforeend',
      `<button type="button" id="pgFab" class="pg-fab" aria-label="Plugins" aria-expanded="false" title="Plugins — review bar, states, component map">${ICON}</button>`);
    render();
  }

  document.addEventListener('click', e => {
    if (e.target.closest('#pgFab'))        { open = !open; return render(); }
    if (e.target.closest('[data-pg-close]')) { open = false; return render(); }
    const row = e.target.closest('[data-pg]');
    if (row && !row.disabled) return toggle(row.dataset.pg);
    if (open && !e.target.closest('#pgPanel')) { open = false; render(); }
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && open) { open = false; render(); }
  });

  if (document.body) mount();
  else document.addEventListener('DOMContentLoaded', mount);
})();
