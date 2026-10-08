/* review.js — the review bar (author/reviewer tooling). Pairs with review.css.
 *
 * Auto-inlined into every prototype by inline.py. Dormant until turned on
 * with the floating circle button (bottom right of every page) or by opening
 * the page with `?review=1`; the choice is remembered per page in
 * localStorage, `?review=0` or the same button turns it off again.
 *
 * Modes (bottom bar, keyboard letters in brackets):
 *   Interact [I]   use the prototype normally
 *   Edit text [E]  click any text and retype it — edits persist and are reapplied after re-renders
 *   Comment  [C]   click any element, leave a note; numbered pins + a side panel (open / resolved)
 *   Spotlight [S]  drag a rectangle; everything outside it is dimmed
 *
 * Storage: `feedback.json` next to the prototype through `tools/serve.mjs`
 * (POST/GET `api/feedback`), with localStorage as a fallback when the page is
 * served statically. "Copy comments as prompt" turns the open comments into
 * a prompt for a coding agent.
 *
 * Optional host adapter — a prototype may define `window.REVIEW` with:
 *   screen: () => ({ id, name })   name of the screen a comment is left on
 *   goto:   id => void             navigate to that screen ("Go to" button)
 *   roots:  'css selector'         stable containers used to address elements
 *                                  (default: direct children of <body>)
 *   key:    el => string           stable name for such a container (default:
 *                                  data-rv-root, id, data-layer/-pop/-view, tag.class)
 * Elements are addressed by root + child-index path, so a prototype that
 * re-renders its DOM keeps its pins and edits as long as the structure holds.
 */
(() => {
  /* ── Enable / disable ─────────────────────────────────────────────── */
  const KEY = 'rv:' + location.pathname.replace(/index\.html$/, '');
  const q = new URLSearchParams(location.search).get('review');
  try { if (q === '1' || q === '') localStorage.setItem(KEY + ':on', '1'); if (q === '0') localStorage.removeItem(KEY + ':on'); } catch {}
  let on = false; try { on = localStorage.getItem(KEY + ':on') === '1'; } catch {}

  /* Floating toggle — present on every page, turns the bar on/off (reloads so the page starts clean) */
  const ICON = '<svg viewBox="0 0 20 20" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5.5A2.5 2.5 0 0 1 5.5 3h9A2.5 2.5 0 0 1 17 5.5v6a2.5 2.5 0 0 1-2.5 2.5H9l-3.6 3v-3H5.5A2.5 2.5 0 0 1 3 11.5z"/><path d="M7 7.5h6M7 10.5h3.5"/></svg>';
  const mountToggle = () => {
    document.body.insertAdjacentHTML('beforeend', `<button type="button" id="rvToggle" class="rv-toggle${on ? ' on' : ''}" title="${on ? 'Turn the review bar off' : 'Review this page: comment, edit text, spotlight'}" aria-label="Review bar">${ICON}</button>`);
    document.getElementById('rvToggle').addEventListener('click', () => {
      try { on ? localStorage.removeItem(KEY + ':on') : localStorage.setItem(KEY + ':on', '1'); } catch {}
      const u = new URL(location.href); u.searchParams.delete('review'); location.replace(u.href);
    });
  };
  if (document.body) mountToggle(); else document.addEventListener('DOMContentLoaded', mountToggle);
  if (!on) return;

  const HOST = () => window.REVIEW || {};
  const REVIEW_UI = '.rv-bar,.rv-side,.rv-pins,.rv-hover,.rv-spot,.rv-toggle';
  let FB = {edits:{}, comments:[]};
  let mode = 'interact';                 // interact | edit | comment | spot
  let sideOpen = false, draft = null, selId = null, filter = 'open', saveState = '', online = false;
  const $ = s => document.querySelector(s);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

  /* ── Mount the UI ─────────────────────────────────────────────────── */
  document.body.insertAdjacentHTML('beforeend',
    `<div id="rvPins" class="rv-pins"></div><div id="rvHover" class="rv-hover rv-hidden"><span class="lb"></span></div>` +
    `<div id="rvSpot" class="rv-spot rv-hidden"></div><div id="rvBar" class="rv-bar"></div><div id="rvSide"></div>`);

  /* ── Store: feedback.json via the dev server, localStorage fallback ── */
  const fetchFB = async () => { const r = await fetch('api/feedback', {cache:'no-store'}); if (!r.ok) throw 0; return r.json(); };
  async function load() {
    try { FB = await fetchFB(); saveState = 'Synced'; online = true; }
    catch { try { FB = JSON.parse(localStorage.getItem(KEY)) || FB; } catch {} saveState = 'Local only'; }
    FB.edits ||= {}; FB.comments ||= [];
    restoreSession(); refresh(); renderBar(); renderSide();
  }
  let saveT = null;
  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(FB)); } catch {}
    clearTimeout(saveT); saveState = 'Saving…'; renderBar();
    saveT = setTimeout(async () => {
      try {
        const r = await fetch('api/feedback', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(FB)}); if (!r.ok) throw 0;
        saveState = 'Saved'; online = true;
      } catch { saveState = online ? 'Save failed' : 'Saved locally'; }
      renderBar();
    }, 250);
  }
  const screen = () => { try { return HOST().screen?.() || null; } catch { return null; } };
  function restoreSession() {
    let s; try { s = JSON.parse(sessionStorage.getItem('rv-session')); sessionStorage.removeItem('rv-session'); } catch {}
    if (!s) return;
    sideOpen = !!s.sideOpen; selId = s.selId; filter = s.filter || filter;
    if (s.mode) setMode(s.mode);
  }

  /* ── Stable addressing: root key + child-index path ───────────────── */
  function roots() {
    const sel = HOST().roots;
    const list = sel ? [...document.querySelectorAll(sel)] : [...document.body.children];
    return list.filter(r => !r.matches(REVIEW_UI));
  }
  function rootKey(r) {
    try { const k = HOST().key?.(r); if (k) return String(k); } catch {}
    if (r.dataset.rvRoot) return r.dataset.rvRoot;
    if (r.id) return '#' + r.id;
    for (const a of ['layer', 'pop', 'view', 'panel', 'screen']) if (r.dataset[a]) return a + ':' + r.dataset[a];
    const tag = r.tagName.toLowerCase(), cls = [...r.classList].filter(c => !c.startsWith('rv-')).slice(0, 2).join('.');
    return tag + (cls ? '.' + cls : '');
  }
  function rootOf(el) { for (const r of roots()) if (r === el || r.contains(el)) return {el:r, key:rootKey(r)}; return null; }
  function pathOf(el) {
    const root = rootOf(el); if (!root) return null; const idx = [];
    for (let n = el; n && n !== root.el; n = n.parentElement) idx.unshift([...n.parentElement.children].indexOf(n));
    return root.key + '/' + idx.join('.');
  }
  function resolve(path) {
    if (!path) return null;
    const i = path.indexOf('/'); const key = path.slice(0, i), rest = path.slice(i + 1);
    const root = roots().find(r => rootKey(r) === key); if (!root) return null;
    let n = root;
    for (const j of (rest ? rest.split('.') : [])) { n = n.children[Number(j)]; if (!n) return null; }
    return n;
  }
  const textNodes = el => [...el.childNodes].filter(n => n.nodeType === 3 && n.data.trim());
  function label(el) {
    const tag = el.tagName.toLowerCase();
    const txt = (el.getAttribute('aria-label') || el.getAttribute('alt') || el.getAttribute('title') || el.textContent || '').replace(/\s+/g, ' ').trim();
    const cls = [...el.classList].filter(c => !c.startsWith('rv-')).slice(0, 2).join('.');
    return `${tag}${cls ? '.' + cls : ''}${txt ? ` "${txt.slice(0, 48)}${txt.length > 48 ? '…' : ''}"` : ''}`;
  }

  /* ── Keep edits and pins in place when the prototype re-renders ───── */
  let applying = false;
  function applyEdits() {
    applying = true;
    for (const [k, e] of Object.entries(FB.edits)) {
      const [p, ti] = k.split('#'); const el = resolve(p); if (!el) continue;
      const tn = textNodes(el)[Number(ti)];
      if (tn && tn.data.trim() === e.orig.trim()) { const lead = tn.data.match(/^\s*/)[0], trail = tn.data.match(/\s*$/)[0]; tn.data = lead + e.text + trail; }
    }
    applying = false;
  }
  const refresh = () => { applyEdits(); placePins(); };
  let refreshT = null;
  new MutationObserver(muts => {
    if (applying || refreshT) return;
    if (!muts.some(m => !m.target.closest?.(REVIEW_UI) && !m.target.parentElement?.closest?.(REVIEW_UI))) return;
    refreshT = setTimeout(() => { refreshT = null; refresh(); }, 0);
  }).observe(document.body, {childList:true, subtree:true, characterData:true});
  window.reviewRefresh = refresh;

  /* ── Text editing ─────────────────────────────────────────────────── */
  function textNodeAt(x, y) {
    let node = null;
    if (document.caretRangeFromPoint) node = document.caretRangeFromPoint(x, y)?.startContainer;
    else if (document.caretPositionFromPoint) node = document.caretPositionFromPoint(x, y)?.offsetNode;
    if (!node || node.nodeType !== 3 || !node.data.trim()) return null;
    const r = document.createRange(); r.selectNodeContents(node);
    const hit = [...r.getClientRects()].some(b => x >= b.left - 2 && x <= b.right + 2 && y >= b.top - 2 && y <= b.bottom + 2);
    return hit && !node.parentElement.closest(REVIEW_UI + ',input,textarea,select,[contenteditable=true]') ? node : null;
  }
  function startEdit(tn) {
    const parent = tn.parentElement; const ti = textNodes(parent).indexOf(tn);
    const p = pathOf(parent); if (!p) return; const key = p + '#' + ti;
    const orig = FB.edits[key]?.orig ?? tn.data.trim();
    const lead = tn.data.match(/^\s*/)[0], trail = tn.data.match(/\s*$/)[0];
    const span = document.createElement('span');
    span.className = 'rv-editing'; span.contentEditable = 'plaintext-only'; span.textContent = tn.data.trim();
    applying = true; tn.replaceWith(document.createTextNode(lead), span, document.createTextNode(trail)); applying = false;
    span.focus(); const sel = getSelection(); const r = document.createRange(); r.selectNodeContents(span); sel.removeAllRanges(); sel.addRange(r);
    let done = false;
    const finish = commit => {
      if (done) return; done = true;
      const val = commit ? span.textContent.replace(/\s+/g, ' ').trim() : (FB.edits[key]?.text ?? orig);
      const out = document.createTextNode(lead + (val || orig) + trail);
      applying = true; span.previousSibling?.remove(); span.nextSibling?.remove(); span.replaceWith(out); applying = false;
      if (commit) { if (!val || val === orig) delete FB.edits[key]; else FB.edits[key] = {orig, text:val, screen:screen()?.name}; save(); }
    };
    span.addEventListener('blur', () => finish(true));
    span.addEventListener('keydown', e => {
      e.stopPropagation();
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); finish(true); }
      if (e.key === 'Escape') { e.preventDefault(); finish(false); }
    });
    ['click','mousedown','keyup','input'].forEach(t => span.addEventListener(t, e => e.stopPropagation()));
  }

  /* ── Hover highlight ──────────────────────────────────────────────── */
  function pickTarget(el) {
    if (!el || el.closest(REVIEW_UI)) return null;
    if (el.closest('svg')) el = el.closest('svg').parentElement || el;
    if (el === document.body || el === document.documentElement || !rootOf(el)) return null;
    return el;
  }
  function showHover(el, cls, text) {
    const h = $('#rvHover'); if (!el) { h.classList.add('rv-hidden'); return; }
    const b = el.getBoundingClientRect(); h.className = 'rv-hover ' + cls;
    Object.assign(h.style, {left:b.left - 2 + 'px', top:b.top - 2 + 'px', width:b.width + 4 + 'px', height:b.height + 4 + 'px'});
    h.querySelector('.lb').textContent = text;
  }
  document.addEventListener('mousemove', e => {
    if (mode === 'interact') return;
    if (mode === 'spot') return showHover(null);
    if (mode === 'edit') {
      const tn = textNodeAt(e.clientX, e.clientY);
      if (!tn) return showHover(null);
      const r = document.createRange(); r.selectNodeContents(tn); const b = r.getBoundingClientRect();
      const h = $('#rvHover'); h.className = 'rv-hover';
      Object.assign(h.style, {left:b.left - 3 + 'px', top:b.top - 2 + 'px', width:b.width + 6 + 'px', height:b.height + 4 + 'px'});
      h.querySelector('.lb').textContent = 'Click to edit text';
    } else {
      const el = pickTarget(e.target); showHover(el, 'c', el ? label(el) : '');
    }
  }, true);

  /* ── Spotlight: drag a rectangle; everything outside it is dimmed ─── */
  let spot = null, spotDrag = null;
  function drawSpot() {
    const el = $('#rvSpot'); const r = spotDrag || spot;
    if (!r) { el.classList.add('rv-hidden'); return; }
    const x = Math.min(r.x0, r.x1), y = Math.min(r.y0, r.y1);
    Object.assign(el.style, {left:x + 'px', top:y + 'px', width:Math.abs(r.x1 - r.x0) + 'px', height:Math.abs(r.y1 - r.y0) + 'px'});
    el.classList.remove('rv-hidden'); el.classList.toggle('drawing', !!spotDrag);
  }
  const clearSpot = () => { spot = spotDrag = null; drawSpot(); renderBar(); };
  window.addEventListener('pointerdown', e => {
    if (mode !== 'spot' || e.button !== 0 || e.target.closest?.(REVIEW_UI)) return;
    e.stopPropagation(); e.preventDefault();
    spotDrag = {x0:e.clientX, y0:e.clientY, x1:e.clientX, y1:e.clientY}; drawSpot();
  }, true);
  window.addEventListener('pointermove', e => { if (!spotDrag) return; spotDrag.x1 = e.clientX; spotDrag.y1 = e.clientY; drawSpot(); }, true);
  window.addEventListener('pointerup', () => {
    if (!spotDrag) return;
    const r = spotDrag; spotDrag = null;
    spot = Math.abs(r.x1 - r.x0) > 6 && Math.abs(r.y1 - r.y0) > 6 ? r : null;   // a plain click clears it
    drawSpot(); renderBar();
  }, true);

  /* ── Swallow clicks in edit/comment/spot mode so the prototype doesn't react ── */
  const swallow = e => {
    if (mode === 'interact' || e.target.closest?.(REVIEW_UI) || e.target.closest?.('.rv-editing')) return;
    if (mode === 'edit' && e.target.closest?.('input,textarea,select,[contenteditable=true]')) return;
    e.stopPropagation(); e.preventDefault();
  };
  ['mousedown','mouseup','pointerdown','dblclick'].forEach(t => window.addEventListener(t, swallow, true));
  window.addEventListener('click', e => {
    if (mode === 'interact' || e.target.closest?.(REVIEW_UI) || e.target.closest?.('.rv-editing')) return;
    if (mode === 'edit' && e.target.closest?.('input,textarea,select,[contenteditable=true]')) return;
    e.stopPropagation(); e.preventDefault();
    if (mode === 'spot') return;
    if (mode === 'edit') { const tn = textNodeAt(e.clientX, e.clientY); if (tn) { showHover(null); startEdit(tn); } return; }
    const el = pickTarget(e.target); if (!el) return;
    const b = el.getBoundingClientRect(), sc = screen();
    draft = {path:pathOf(el), el:label(el), html:el.outerHTML.replace(/\s+/g, ' ').slice(0, 600),
      screenId:sc?.id ?? null, screen:sc?.name || document.title || location.pathname, url:location.pathname + location.hash,
      rect:{x:Math.round(b.left), y:Math.round(b.top), w:Math.round(b.width), h:Math.round(b.height)}};
    sideOpen = true; selId = null; renderSide(); placePins(); renderBar();
    $('#rvDraft')?.focus();
  }, true);

  /* ── Pins ─────────────────────────────────────────────────────────── */
  function placePins() {
    const host = $('#rvPins'); if (!host) return;
    let html = '';
    const outline = b => `<div class="rv-outline" style="left:${b.left - 3}px;top:${b.top - 3}px;width:${b.width + 6}px;height:${b.height + 6}px"></div>`;
    FB.comments.filter(c => filter === 'all' || (filter === 'open' ? !c.resolved : c.resolved)).forEach(c => {
      const el = resolve(c.path); if (!el) return;
      const b = el.getBoundingClientRect(); if (!b.width && !b.height) return;
      html += `<div class="rv-pin ${c.resolved ? 'done' : ''} ${c.id === selId ? 'sel' : ''}" data-pin="${c.id}" style="left:${b.right}px;top:${b.top}px">${c.n}</div>`;
      if (c.id === selId) html += outline(b);
    });
    if (draft) { const el = resolve(draft.path); if (el) html += outline(el.getBoundingClientRect()); }
    applying = true; host.innerHTML = html; applying = false;
  }
  let pinT = null; const schedulePins = () => { if (!pinT) pinT = setTimeout(() => { pinT = null; placePins(); }, 16); };
  document.addEventListener('scroll', schedulePins, true); window.addEventListener('resize', schedulePins);
  document.addEventListener('click', e => { const p = e.target.closest('[data-pin]'); if (p) { selId = p.dataset.pin; sideOpen = true; draft = null; renderSide(); placePins(); document.querySelector(`[data-cid="${selId}"]`)?.scrollIntoView({block:'nearest'}); } });

  /* ── Bar ──────────────────────────────────────────────────────────── */
  function setMode(m) {
    mode = m; document.body.classList.toggle('rv-edit', m === 'edit'); document.body.classList.toggle('rv-comment', m === 'comment'); document.body.classList.toggle('rv-spotmode', m === 'spot');
    showHover(null); if (m === 'comment') sideOpen = true; renderBar(); renderSide();
  }
  function renderBar() {
    const open = FB.comments.filter(c => !c.resolved).length, edits = Object.keys(FB.edits).length;
    $('#rvBar').innerHTML = `
      <button class="${mode === 'interact' ? 'on' : ''}" data-rv-mode="interact">Interact <span class="k">I</span></button>
      <button class="${mode === 'edit' ? 'on' : ''}" data-rv-mode="edit">Edit text <span class="k">E</span></button>
      <button class="${mode === 'comment' ? 'on' : ''}" data-rv-mode="comment">Comment <span class="k">C</span>${open ? `<span class="n">${open}</span>` : ''}</button>
      <button class="${mode === 'spot' ? 'on' : ''}" data-rv-mode="spot">Spotlight <span class="k">S</span></button>
      ${spot ? `<button data-rv="clear-spot" title="Remove the spotlight">✕ Clear spotlight</button>` : ''}
      <span class="sep"></span>
      <button data-rv="side">${sideOpen ? 'Hide' : 'Show'} comments</button>
      ${edits ? `<button data-rv="reset" title="Undo all text edits">↺ ${edits} edit${edits > 1 ? 's' : ''}</button>` : ''}
      <span class="st">${saveState}</span>`;
  }
  document.addEventListener('click', e => {
    const m = e.target.closest('[data-rv-mode]'); if (m) return setMode(m.dataset.rvMode);
    const a = e.target.closest('[data-rv]'); if (!a) return;
    const act = a.dataset.rv, c = a.dataset.id && FB.comments.find(c => c.id === a.dataset.id);
    if (act === 'side') { sideOpen = !sideOpen; if (!sideOpen) draft = null; renderBar(); renderSide(); placePins(); }
    if (act === 'reset' && confirm('Undo all inline text edits? The page reloads.')) { FB.edits = {}; save(); setTimeout(() => location.reload(), 300); }
    if (act === 'close') { sideOpen = false; draft = null; selId = null; if (mode === 'comment') setMode('interact'); renderBar(); renderSide(); placePins(); }
    if (act === 'cancel') { draft = null; renderSide(); placePins(); }
    if (act === 'post') postDraft();
    if (act === 'clear-spot') clearSpot();
    if (act === 'filter') { filter = a.dataset.v; renderSide(); placePins(); }
    if (act === 'del' && c) { e.stopPropagation(); FB.comments = FB.comments.filter(x => x !== c); save(); renderSide(); placePins(); renderBar(); }
    if (act === 'resolve' && c) { e.stopPropagation(); c.resolved = !c.resolved; save(); renderSide(); placePins(); renderBar(); }
    if (act === 'goto' && c) { e.stopPropagation(); try { HOST().goto?.(c.screenId); } catch {} selId = c.id; renderSide(); placePins(); }
    if (act === 'copy') {
      const open = FB.comments.filter(c => !c.resolved);
      const file = location.pathname.replace(/^\//, '').replace(/\/$/, '/index.html') || 'index.html';
      const txt = `Apply these prototype comments in ${file}:\n\n` + open.map(c => `#${c.n} [${c.screen}] ${c.el}\n   → ${c.text}`).join('\n\n');
      navigator.clipboard?.writeText(txt).then(() => { a.textContent = 'Copied ✓'; setTimeout(() => renderSide(), 1200); });
    }
  });
  document.addEventListener('click', e => { const c = e.target.closest('[data-cid]'); if (c && !e.target.closest('button')) { selId = c.dataset.cid; renderSide(); placePins(); resolve(FB.comments.find(x => x.id === selId)?.path)?.scrollIntoView?.({block:'center', behavior:'smooth'}); } });

  function postDraft() {
    const t = $('#rvDraft')?.value.trim(); if (!t || !draft) return;
    const n = FB.comments.reduce((m, c) => Math.max(m, c.n), 0) + 1;
    const c = {id:'c' + Date.now().toString(36), n, ...draft, text:t, created:new Date().toISOString(), resolved:false};
    FB.comments.push(c); draft = null; selId = c.id; save(); renderSide(); placePins(); renderBar();
  }

  /* ── Side panel ───────────────────────────────────────────────────── */
  function renderSide() {
    document.body.classList.toggle('rv-side-open', sideOpen);
    if (!sideOpen) { $('#rvSide').innerHTML = ''; return; }
    const list = FB.comments.filter(c => filter === 'all' || (filter === 'open' ? !c.resolved : c.resolved)).slice().reverse();
    const counts = {open:FB.comments.filter(c => !c.resolved).length, resolved:FB.comments.filter(c => c.resolved).length, all:FB.comments.length};
    const when = c => new Date(c.created).toLocaleString([], {month:'short', day:'numeric', hour:'numeric', minute:'2-digit'});
    $('#rvSide').innerHTML = `<div class="rv-side">
      <div class="h"><b>Comments</b><button class="x" data-rv="close" title="Close">×</button></div>
      <div class="tabs2">${['open','resolved','all'].map(f => `<button class="${filter === f ? 'on' : ''}" data-rv="filter" data-v="${f}">${f[0].toUpperCase() + f.slice(1)} ${counts[f]}</button>`).join('')}</div>
      <div class="body">
        ${draft ? `<div class="rv-compose"><div style="font-weight:600;margin-bottom:6px">New comment · ${esc(draft.screen)}</div>
          <div class="rv-target">${esc(draft.el)}</div>
          <textarea id="rvDraft" placeholder="What should change here?"></textarea>
          <div class="f"><span class="hint">⌘↵ to post</span><button class="btn" data-rv="cancel">Cancel</button><button class="btn primary" data-rv="post">Comment</button></div></div>`
        : mode === 'comment' ? `<div class="rv-empty" style="padding:12px 8px 20px">Click any element in the prototype to leave a comment on it.</div>` : ''}
        ${list.length ? list.map(c => `<div class="rv-c ${c.resolved ? 'done' : ''} ${c.id === selId ? 'sel' : ''}" data-cid="${c.id}">
            <div class="t"><span class="num">${c.n}</span><span class="el" title="${esc(c.el)}">${esc(c.el)}</span></div>
            <div class="msg">${esc(c.text)}</div>
            ${c.resolution ? `<div class="res">✓ ${esc(c.resolution)}</div>` : ''}
            <div class="meta2"><span>${esc(c.screen || '')} · ${when(c)}</span><span style="flex:1"></span>
              ${c.screenId != null && HOST().goto ? `<button data-rv="goto" data-id="${c.id}">Go to</button>` : ''}<button data-rv="resolve" data-id="${c.id}">${c.resolved ? 'Reopen' : 'Resolve'}</button><button class="del" data-rv="del" data-id="${c.id}">Delete</button></div>
          </div>`).join('') : (!draft ? `<div class="rv-empty">No ${filter === 'all' ? '' : filter + ' '}comments yet.</div>` : '')}
      </div>
      <div class="foot">Comments are saved to <code>feedback.json</code> next to this prototype when it runs on the Icarus dev server, otherwise in this browser only.
        <div><button class="btn" data-rv="copy">Copy comments as prompt</button></div></div>
    </div>`;
    const ta = $('#rvDraft');
    ta?.addEventListener('keydown', e => { e.stopPropagation(); if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) postDraft(); if (e.key === 'Escape') { draft = null; renderSide(); placePins(); } });
  }

  /* ── Shortcuts ────────────────────────────────────────────────────── */
  document.addEventListener('keydown', e => {
    if (e.target.closest('input,textarea,[contenteditable],select') || e.metaKey || e.ctrlKey || e.altKey) return;
    const k = e.key.toLowerCase();
    if (k === 'e') setMode(mode === 'edit' ? 'interact' : 'edit');
    if (k === 'c') setMode(mode === 'comment' ? 'interact' : 'comment');
    if (k === 'i') setMode('interact');
    if (k === 's') setMode(mode === 'spot' ? 'interact' : 'spot');
    if (e.key === 'Escape' && spot) { e.stopImmediatePropagation(); clearSpot(); return; }   // spotlight first, then the mode
    if (e.key === 'Escape' && mode !== 'interact') { e.stopImmediatePropagation(); draft = null; setMode('interact'); placePins(); }
  }, true);

  renderBar(); load();
})();
