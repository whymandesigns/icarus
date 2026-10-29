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
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
const run = promisify(execFile);

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(process.argv[2] || path.join(HERE, '..', '..', 'features'));
const PORT = Number(process.argv[3] || process.env.PORT) || 5733;
const TYPES = { '.html':'text/html; charset=utf-8', '.js':'text/javascript', '.mjs':'text/javascript', '.css':'text/css', '.json':'application/json',
  '.svg':'image/svg+xml', '.png':'image/png', '.jpg':'image/jpeg', '.jpeg':'image/jpeg', '.gif':'image/gif', '.webp':'image/webp', '.ico':'image/x-icon',
  '.woff2':'font/woff2', '.woff':'font/woff', '.mp4':'video/mp4', '.webm':'video/webm', '.csv':'text/csv', '.txt':'text/plain' };

const safe = p => { const f = path.normalize(path.join(ROOT, decodeURIComponent(p))); return f.startsWith(ROOT) ? f : null; };
// A prototype that is still linked — not yet run through inline.py — asks for
// the design system at ../../designmd/…, which normalises to /designmd/… and
// lands outside ROOT. Serve those from the checkout this script lives in, so a
// linked prototype renders here exactly as it will once it is baked. Anything
// really under ROOT still wins; this is only consulted on a miss.
const DESIGNMD = path.resolve(HERE, '..');
const designmdFile = p => {
  const rel = decodeURIComponent(p).replace(/^\/designmd\//, '');
  if (rel === decodeURIComponent(p)) return null;
  const f = path.normalize(path.join(DESIGNMD, rel));
  return f.startsWith(DESIGNMD) ? f : null;
};
const json = (res, code, body) => { res.writeHead(code, { 'Content-Type':'application/json', 'Cache-Control':'no-store' }); res.end(JSON.stringify(body)); };
const readDoc = async file => { try { return JSON.parse(await fs.readFile(file, 'utf8')); } catch { return EMPTY(); } };

// `/api/version` mirrors the hosted route (api/version.js on Vercel): which
// commit of `dir` is being served. Read from git on every request so the badge
// follows the checkout as you commit; `dirty` flags uncommitted changes.
async function version() {
  const git = async (...a) => (await run('git', ['-C', ROOT, ...a])).stdout.trim();
  try {
    const [sha, ref, message, status, remote] = await Promise.all([
      git('rev-parse', 'HEAD'), git('branch', '--show-current'), git('log', '-1', '--format=%s'), git('status', '--porcelain'),
      git('remote', 'get-url', 'origin').catch(() => ''),
    ]);
    // "git@github.com:owner/repo.git" or "https://github.com/owner/repo.git" -> "owner/repo"
    const repo = remote.match(/github\.com[:/]([^/]+\/[^/]+?)(?:\.git)?$/)?.[1] || null;
    return { sha, short: sha.slice(0, 7), ref: ref || null, message, env: 'local', deployment: null, dirty: status.length > 0, repo };
  } catch {
    return { sha: null, short: null, ref: null, message: null, env: 'local', deployment: null, dirty: false, repo: null };
  }
}

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
    if (url.pathname === '/api/version') return json(res, 200, await version());
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
    let stat = await fs.stat(file).catch(() => null);
    if (!stat) {
      const alt = designmdFile(url.pathname);
      const altStat = alt && await fs.stat(alt).catch(() => null);
      if (altStat) { file = alt; stat = altStat; }
    }
    if (stat?.isDirectory()) file = path.join(file, 'index.html');
    const data = await fs.readFile(file);
    res.writeHead(200, { 'Content-Type': TYPES[path.extname(file).toLowerCase()] || 'application/octet-stream', 'Cache-Control':'no-store' });
    res.end(data);
  } catch (e) {
    res.writeHead(e.code === 'ENOENT' ? 404 : 500); res.end(String(e.message));
  }
}).listen(PORT, () => console.log(`Prototypes from ${ROOT} on http://localhost:${PORT}  (review bar: circle button bottom-right, or ?review=1)`));
