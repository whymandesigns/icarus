// feedback-store.mjs — the merge rules for review-bar feedback.
//
// Shared by tools/serve.mjs (local, writes <prototype>/feedback.json) and by the
// hosted API (see review-bar.html "Hosting the shared store"). Both receive
// small operations from review.js rather than whole documents, so several
// reviewers can work on the same prototype without overwriting each other.
//
// Document: { edits: { "<path>#<i>": {orig, text, screen, author} }, comments: [...], updated }
// Ops:      { t:'comment', c }      upsert a comment by id (server assigns n when missing)
//           { t:'del', id }         delete a comment
//           { t:'edit', k, v }      set (v) or clear (v null) one text edit
//           { t:'edits:clear' }     clear every text edit

export const EMPTY = () => ({ edits: {}, comments: [] });

export function applyOps(doc, ops) {
  // Spread the original first so fields this store doesn't own (e.g. version,
  // versions) survive a write instead of being dropped.
  doc = { ...(doc || {}), edits: { ...(doc?.edits || {}) }, comments: [...(doc?.comments || [])] };
  for (const o of Array.isArray(ops) ? ops : []) {
    if (o?.t === 'comment' && o.c && typeof o.c.id === 'string') {
      const i = doc.comments.findIndex(c => c.id === o.c.id);
      const c = { ...(doc.comments[i] || {}), ...o.c };
      if (typeof c.text === 'string') c.text = c.text.slice(0, 5000);
      if (!c.n) c.n = doc.comments.reduce((m, x) => Math.max(m, x.n || 0), 0) + 1;
      if (i < 0) { if (doc.comments.length < 1000) doc.comments.push(c); } else doc.comments[i] = c;
    } else if (o?.t === 'del' && typeof o.id === 'string') {
      doc.comments = doc.comments.filter(c => c.id !== o.id);
    } else if (o?.t === 'edit' && typeof o.k === 'string') {
      if (o.v && typeof o.v === 'object') { if (Object.keys(doc.edits).length < 2000) doc.edits[o.k] = o.v; }
      else delete doc.edits[o.k];
    } else if (o?.t === 'edits:clear') {
      doc.edits = {};
    }
  }
  doc.updated = new Date().toISOString();
  return doc;
}

// A prototype is addressed by its URL path: "/action-trace/". Reject anything odd.
export const cleanPath = p => {
  p = String(p || '').replace(/index\.html$/, '');
  if (!p.startsWith('/') || p.includes('..') || p.length > 200) return null;
  return p.endsWith('/') ? p : p + '/';
};
