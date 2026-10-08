// serve.mjs — static dev server for prototypes + the review bar's feedback API.
//
//   node tools/serve.mjs [dir] [port]      (defaults: ../features next to this repo, 5733)
//
// Serves `dir` as plain files. Any `<folder>/api/feedback` route reads/writes
// `<folder>/feedback.json`, which is where the review bar (review.js, enabled
// with ?review=1) keeps a prototype's comments and inline text edits.
import http from 'node:http';
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(process.argv[2] || path.join(HERE, '..', '..', 'features'));
const PORT = Number(process.argv[3] || process.env.PORT) || 5733;
const EMPTY = '{"edits":{},"comments":[]}\n';
const TYPES = { '.html':'text/html; charset=utf-8', '.js':'text/javascript', '.mjs':'text/javascript', '.css':'text/css', '.json':'application/json',
  '.svg':'image/svg+xml', '.png':'image/png', '.jpg':'image/jpeg', '.jpeg':'image/jpeg', '.gif':'image/gif', '.webp':'image/webp', '.ico':'image/x-icon',
  '.woff2':'font/woff2', '.woff':'font/woff', '.mp4':'video/mp4', '.webm':'video/webm', '.csv':'text/csv', '.txt':'text/plain' };

const safe = p => { const f = path.normalize(path.join(ROOT, decodeURIComponent(p))); return f.startsWith(ROOT) ? f : null; };

http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://x');
  try {
    const api = url.pathname.match(/^(.*\/)api\/feedback$/);
    if (api) {
      const file = safe(api[1] + 'feedback.json'); if (!file) { res.writeHead(403); return res.end(); }
      if (req.method === 'GET') {
        const data = await fs.readFile(file, 'utf8').catch(() => EMPTY);
        res.writeHead(200, { 'Content-Type':'application/json', 'Cache-Control':'no-store' }); return res.end(data);
      }
      if (req.method === 'POST') {
        let body = ''; for await (const c of req) body += c;
        const parsed = JSON.parse(body);                       // validate before writing
        await fs.writeFile(file, JSON.stringify(parsed, null, 2) + '\n');
        res.writeHead(200, { 'Content-Type':'application/json' }); return res.end('{"ok":true}');
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
}).listen(PORT, () => console.log(`Prototypes from ${ROOT} on http://localhost:${PORT}  (add ?review=1 to a prototype URL for the review bar)`));
