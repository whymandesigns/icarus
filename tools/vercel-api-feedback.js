// Hosted store for the review bar — a Vercel serverless function.
//
// Copy this file to `api/feedback.js` in the repository that Vercel deploys
// your prototypes from (the folder that holds <prototype>/index.html). Vercel
// picks up `api/*.js` automatically; no package.json or build step needed.
//
// Storage: a Redis database from the Vercel Marketplace (Upstash, free tier is
// plenty). Vercel → your project → Storage → Create Database → Upstash Redis →
// connect to the project. That injects KV_REST_API_URL / KV_REST_API_TOKEN
// (or UPSTASH_REDIS_REST_URL / _TOKEN); redeploy once and the bar switches
// from "Local only" to "Shared".
//
// API (same contract as tools/serve.mjs locally):
//   GET  /api/feedback?p=/action-trace/     → { edits, comments, updated }
//   POST /api/feedback  { p, ops }           → merged document
// Ops are documented in tools/feedback-store.mjs; the merge below is a copy of it.

const URL_ = process.env.KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL;
const TOKEN = process.env.KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN;

async function redis(cmd) {
  const r = await fetch(URL_, { method: 'POST', headers: { Authorization: `Bearer ${TOKEN}`, 'Content-Type': 'application/json' }, body: JSON.stringify(cmd) });
  if (!r.ok) throw new Error('store ' + r.status);
  const j = await r.json(); if (j.error) throw new Error(j.error);
  return j.result;
}

const EMPTY = () => ({ edits: {}, comments: [] });
function applyOps(doc, ops) {
  doc = { edits: { ...(doc?.edits || {}) }, comments: [...(doc?.comments || [])] };
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
const cleanPath = p => {
  p = String(p || '').replace(/index\.html$/, '');
  if (!p.startsWith('/') || p.includes('..') || p.length > 200) return null;
  return p.endsWith('/') ? p : p + '/';
};

module.exports = async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  if (!URL_ || !TOKEN) return res.status(503).json({ error: 'Store not configured: connect an Upstash Redis database to this Vercel project.' });
  try {
    const body = req.method === 'POST' ? (typeof req.body === 'string' ? JSON.parse(req.body || '{}') : req.body || {}) : {};
    const p = cleanPath(req.method === 'POST' ? body.p : req.query?.p);
    if (!p) return res.status(400).json({ error: 'bad prototype path' });
    const key = 'rv:' + p;
    const read = async () => { const v = await redis(['GET', key]); try { return v ? JSON.parse(v) : EMPTY(); } catch { return EMPTY(); } };
    if (req.method === 'GET') return res.status(200).json(await read());
    if (req.method === 'POST') {
      if (JSON.stringify(body).length > 200000) return res.status(413).json({ error: 'too large' });
      const doc = applyOps(await read(), body.ops);
      await redis(['SET', key, JSON.stringify(doc)]);
      return res.status(200).json(doc);
    }
    res.status(405).end();
  } catch (e) {
    res.status(500).json({ error: String(e.message || e) });
  }
};
