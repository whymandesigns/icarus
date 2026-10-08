// serve.mjs — static dev server for prototypes + the review bar's feedback API.
//
//   node tools/serve.mjs [dir] [port]      (defaults: ../features next to this repo, 5733)
//
// Serves `dir` as plain files. `/api/feedback?p=/<prototype>/` reads and writes
// `<dir>/<prototype>/feedback.json`, the local store for the review bar
// (review.js). GET returns the document; POST takes { p, ops } and returns the
// merged document — the same contract as the hosted API, see
// tools/feedback-store.mjs for the ops.
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { applyOps, cleanPath, EMPTY } from './feedback-store.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(process.argv[2] || path.join(HERE, '..', '..', 'features'));
const PORT = Number(process.argv[3] || process.env.PORT) || 5733;
const TYPES = { '.html':'text/html; charset=utf-8', '.js':'text/javascript', '.mjs':'text/javascript', '.css':'text/css', '.json':'application/json',
  '.svg':'image/svg+xml', '.png':'image/png', '.jpg':'image/jpeg', '.jpeg':'image/jpeg', '.gif':'image/gif', '.webp':'image/webp', '.ico':'image/x-icon',
  '.woff2':'font/woff2', '.woff':'font/woff', '.mp4':'video/mp4', '.webm':'video/webm', '.csv':'text/csv', '.txt':'text/plain' };

const safe = p => { const f = path.normalize(path.join(ROOT, decodeURIComponent(p))); return f.startsWith(ROOT) ? f : null; };
const json = (res, code, body) => { res.writeHead(code, { 'Content-Type':'application/json', 'Cache-Control':'no-store' }); res.end(JSON.stringify(body)); };
const readDoc = async file => { try { return JSON.parse(await fs.readFile(file, 'utf8')); } catch { return EMPTY(); } };

// Serialise read-modify-write per file: two reviewers posting at the same moment
// would otherwise both read the old document and the second write would drop the
// first one's op. Each file gets a promise chain; writes run one at a time.
const chains = new Map();
function withLock(key, fn) {
  const run = (chains.get(key) || Promise.resolve()).then(fn, fn);
  chains.set(key, run.then(() => {}, () => {}));
  return run;
}
// Write through a temp file + rename so a crash mid-write can't truncate the store.
async function writeDoc(file, doc) {
  await fs.mkdir(path.dirname(file), { recursive: true });
  const tmp = file + '.tmp';
  await fs.writeFile(tmp, JSON.stringify(doc, null, 2) + '\n');
  await fs.rename(tmp, file);
}

http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x');
  try {
    if (url.pathname === '/api/feedback') {
      let body = {}; if (req.method === 'POST') { let raw = ''; for await (const c of req) raw += c; body = JSON.parse(raw || '{}'); }
      const p = cleanPath(req.method === 'POST' ? body.p : url.searchParams.get('p'));
      const file = p && safe(p + 'feedback.json');
      if (!file) return json(res, 400, { error: 'bad prototype path' });
      if (req.method === 'GET') return json(res, 200, await readDoc(file));
      if (req.method === 'POST') {
        const doc = await withLock(file, async () => {
          const next = applyOps(await readDoc(file), body.ops);
          await writeDoc(file, next);
          return next;
        });
        return json(res, 200, doc);
      }
      res.writeHead(405); return res.end();
    }
    let file = safe(url.pathname); if (!file) { res.writeHead(403); return res.end(); }
    if ((await fs.stat(file).catch(() => null))?.isDirectory()) file = path.join(file, 'index.html');
    const data = await fs.readFile(file);
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(file).toLowerCase()] || 'application/octet-stream', 'Cache-Control':'no-store' });
    res.end(data);
  } catch (e) {
    res.writeHead(e.code === 'ENOENT' ? 404 : 500); res.end(String(e.message));
  }
}).listen(PORT, () => console.log(`Prototypes from ${ROOT} on http://localhost:${PORT}  (review bar: circle button bottom-right, or ?review=1)`));
