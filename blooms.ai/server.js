const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');

const PORT = 3369;
const HOST = '127.0.0.1';
const LOG_FILE = '/tmp/blooms-analytics.ndjson';
const DEMO_CONFIG = path.join(__dirname, 'democonfig.json');

const MIME = {
  '.html': 'text/html',
  '.css': 'text/css',
  '.js': 'application/javascript',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
};

function readJSON(filePath) {
  try { return JSON.parse(fs.readFileSync(filePath, 'utf-8')); }
  catch { return null; }
}

function parseBody(req) {
  return new Promise((resolve) => {
    let body = '';
    req.on('data', (c) => { body += c; });
    req.on('end', () => {
      try { resolve(JSON.parse(body)); }
      catch { resolve(null); }
    });
  });
}

function serveFile(res, filePath) {
  const ext = path.extname(filePath);
  const contentType = MIME[ext] || 'application/octet-stream';
  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404, { 'Content-Type': 'text/html' });
      res.end('<h1>404 Not Found</h1>');
      return;
    }
    res.writeHead(200, { 'Content-Type': contentType });
    res.end(data);
  });
}

function readAnalytics() {
  try {
    const data = fs.readFileSync(LOG_FILE, 'utf-8').trim();
    if (!data) return [];
    return data.split('\n').map(l => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean);
  } catch { return []; }
}

function unauthorised(res) {
  res.writeHead(401, {
    'WWW-Authenticate': 'Basic realm="Demo Apps"',
    'Content-Type': 'text/html',
  });
  res.end('<h1>401 Unauthorized</h1>');
}

function checkAuth(req, config) {
  const header = req.headers['authorization'] || '';
  const parts = header.split(' ');
  if (parts.length !== 2 || parts[0] !== 'Basic') return false;
  const decoded = Buffer.from(parts[1], 'base64').toString();
  const colon = decoded.indexOf(':');
  if (colon === -1) return false;
  const user = decoded.slice(0, colon);
  const pass = decoded.slice(colon + 1);
  return user === config.username && pass === config.password;
}

function proxyRequest(req, res, targetUrl) {
  const target = new URL(targetUrl);
  const options = {
    hostname: target.hostname,
    port: target.port,
    path: target.pathname + target.search,
    method: req.method,
    headers: { ...req.headers },
  };
  delete options.headers['host'];

  const proxy = (target.protocol === 'https:' ? https : http).request(options, (proxyRes) => {
    res.writeHead(proxyRes.statusCode, proxyRes.headers);
    proxyRes.pipe(res);
  });

  proxy.on('error', () => {
    res.writeHead(502, { 'Content-Type': 'text/html' });
    res.end('<h1>502 Bad Gateway</h1><p>Demo app is not available.</p>');
  });

  req.pipe(proxy);
}

function getInternalUrl(config, displayName) {
  if (!config || !config.apps) return null;
  const app = config.apps.find(a => a.display === displayName);
  return app ? app.internal_url : null;
}

function serveDemoList(res, config) {
  const apps = (config && config.apps) || [];
  const cards = apps.map(a => `
      <a href="${a.display}/" class="demo-card">
      <h3>${a.display}</h3>
      <span class="demo-link">Open &rarr;</span>
    </a>
  `).join('');

  res.writeHead(200, { 'Content-Type': 'text/html' });
  res.end(`<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Demos &middot; Blooms.ai</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f5f5f8;color:#1a1a2e;padding:40px 24px;line-height:1.5;}
.wrap{max-width:720px;margin:0 auto;}
h1{font-size:1.3rem;font-weight:700;margin-bottom:8px;color:#7c3aed;}
p.sub{color:#888;margin-bottom:28px;}
.demos{display:grid;gap:16px;}
.demo-card{display:flex;align-items:center;justify-content:space-between;background:#fff;border:1px solid #e5e5ea;border-radius:10px;padding:20px 24px;text-decoration:none;color:inherit;transition:box-shadow .2s,border-color .2s;}
.demo-card:hover{box-shadow:0 4px 20px rgba(124,58,237,.1);border-color:#7c3aed;}
.demo-card h3{font-size:1rem;font-weight:600;}
.demo-link{font-size:.85rem;color:#7c3aed;font-weight:500;}
.empty{text-align:center;color:#888;padding:40px 0;}
</style>
</head>
<body>
<div class="wrap">
<h1>&#9670; Demo Applications</h1>
<p class="sub">${apps.length} app${apps.length === 1 ? '' : 's'} available</p>
<div class="demos">${cards || '<div class="empty">No demo apps configured yet.</div>'}</div>
</div>
</body>
</html>`);
}

http.createServer(async (req, res) => {
  const url = req.url;

  // POST /api/analytics - collect page view
  if (req.method === 'POST' && url === '/api/analytics') {
    const body = await parseBody(req);
    if (!body) { res.writeHead(400); res.end('Bad Request'); return; }
    const entry = { t: Date.now(), u: body.url || '', r: body.ref || '', w: body.w || 0, h: body.h || 0, lang: body.lang || '' };
    try { fs.appendFileSync(LOG_FILE, JSON.stringify(entry) + '\n'); } catch {}
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ ok: true }));
    return;
  }

  // GET /api/analytics/data - return aggregated stats
  if (req.method === 'GET' && url === '/api/analytics/data') {
    const entries = readAnalytics();
    const total = entries.length;
    const now = Date.now();
    const day = 86400000;
    const last24h = entries.filter(e => e.t > now - day).length;
    const last7d = entries.filter(e => e.t > now - day * 7).length;
    const pages = {};
    const referrers = {};
    entries.forEach(e => {
      if (e.u) { const p = e.u.split('?')[0].split('#')[0]; pages[p] = (pages[p] || 0) + 1; }
      if (e.r) { try { const host = new URL(e.r).hostname; if (host && !host.includes('106.51.105.16') && !host.includes('localhost')) referrers[host] = (referrers[host] || 0) + 1; } catch {} }
    });
    const sortedPages = Object.entries(pages).sort((a, b) => b[1] - a[1]).slice(0, 20);
    const sortedRefs = Object.entries(referrers).sort((a, b) => b[1] - a[1]).slice(0, 10);
    const hourly = {};
    entries.forEach(e => { if (e.t > now - day) { const h = new Date(e.t).toISOString().slice(0, 13); hourly[h] = (hourly[h] || 0) + 1; } });
    const timeline = Object.entries(hourly).sort();
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ total, last24h, last7d, pages: sortedPages, referrers: sortedRefs, timeline }));
    return;
  }

  // Analytics dashboard
  if (url === '/analytics') {
    serveFile(res, path.join(__dirname, 'analytics.html'));
    return;
  }

  // Demo section
  if (url.startsWith('/demo')) {
    const config = readJSON(DEMO_CONFIG);
    if (!checkAuth(req, config || { username: '', password: '' })) {
      unauthorised(res);
      return;
    }

    // /demo/ or /demo — list all apps
    if (url === '/demo' || url === '/demo/') {
      serveDemoList(res, config);
      return;
    }

    // /demo/<displayName>[/...]
    const parts = url.slice(6).split('/'); // after "/demo/"
    const displayName = decodeURIComponent(parts[0]);
    const restPath = '/' + parts.slice(1).join('/');

    // Redirect bare demo names (no sub-path, no trailing slash) so relative URLs resolve correctly
    // The /blooms prefix matches nginx's location block — kept in sync manually
    if (restPath === '/' && !req.url.endsWith('/')) {
      res.writeHead(302, { 'Location': '/blooms' + req.url + '/' });
      res.end();
      return;
    }

    const internalUrl = getInternalUrl(config, displayName);
    if (!internalUrl) {
      res.writeHead(404, { 'Content-Type': 'text/html' });
      res.end('<h1>404 Not Found</h1><p>Demo app not found.</p>');
      return;
    }

    // Build target URL with remaining path
    const base = internalUrl.replace(/\/+$/, '');
    const target = base + restPath;
    proxyRequest(req, res, target);
    return;
  }

  // Static files
  let filePath = path.join(__dirname, url === '/' ? 'index.html' : url);
  serveFile(res, filePath);
}).listen(PORT, HOST, () => {
  console.log(`Server running at http://${HOST}:${PORT}/`);
});
