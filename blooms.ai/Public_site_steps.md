# Public Site Deployment: blooms.ai

**URL:** http://106.51.105.16/blooms/
**Date:** 2026-06-17

---

## Architecture

```
Internet → Router (port 80 fwd) → nginx (port 80) → Node.js (127.0.0.1:3369) → Static files
```

- **Router** at 192.168.0.1 forwards port 80 → 192.168.0.109
- **nginx** (port 80) acts as reverse proxy; the active config is `/etc/nginx/sites-enabled/lms`
- **Node.js** HTTP server on `127.0.0.1:3369` serves static files from `blooms.ai/`

---

## Changes Made

### 1. Node.js backend server
**File:** `/home/bloomsmobility/lab/aiprojects/blooms.ai/server.js`
- Simple HTTP static file server
- Binds to `127.0.0.1:3369` (localhost only — not exposed to network)
- Serves: `index.html`, `css/`, `js/`, `web_conf.json`

### 2. nginx reverse proxy config
**File:** `/etc/nginx/sites-available/lms` (lines 18–25)
```nginx
location /blooms/ {
    proxy_pass http://127.0.0.1:3369/;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```
- Request `http://IP/blooms/foo` → proxied to `http://127.0.0.1:3369/foo`
- Active via symlink `/etc/nginx/sites-enabled/lms → sites-available/lms`

### 3. Leftover (inactive) file
**File:** `/tmp/nginx-default.conf` — a pre-built config with the same location block, intended for `/etc/nginx/sites-available/default`. Can be deleted.

---

## Security Risks & Remediation

| # | Risk | Severity | Details | Remediation |
|---|------|----------|---------|-------------|
| 1 | **No HTTPS (HTTP-only)** | **HIGH** | All traffic unencrypted. Credentials, content, and data in transit are visible to anyone on the network path (MITM). | Obtain an SSL certificate (Let's Encrypt via certbot) and serve on port 443. Or set up Cloudflare Tunnel for automatic HTTPS. |
| 2 | **Path traversal in Node.js** | **HIGH** | `server.js` uses `path.join(__dirname, req.url)` without sanitization. Although nginx normalizes paths before proxying, direct access to port 3369 (localhost) allows reading arbitrary files the user has access to (confirmed: `.git/config` readable). | Add path validation: check that the resolved path starts with `__dirname`. Use `path.resolve` + `path.startsWith` guard. Or switch to serving static files directly via nginx (eliminates the backend entirely). |
| 3 | **nginx version exposed** | **LOW** | `Server: nginx/1.18.0 (Ubuntu)` header reveals exact version, helping attackers target known CVEs. | Add `server_tokens off;` in `/etc/nginx/nginx.conf` http block. |
| 4 | **No process manager for Node.js** | **MEDIUM** | Node.js runs under `nohup` — no auto-restart on crash, no logging to journald, no monitoring. | Use systemd service, pm2, or supervisor to manage the process. Example systemd unit below. |
| 5 | **No access logging on backend** | **LOW** | nginx logs access, but the Node.js server has no logging. Debugging issues requires correlating nginx logs with backend behavior. | Add `morgan` or simple request logging to `server.js`. |
| 6 | **No rate limiting** | **MEDIUM** | nginx has no `limit_req_zone` or `limit_conn_zone`. The site is vulnerable to brute-force or DoS attacks. | Add rate limiting in nginx config (see example below). |
| 7 | **No proxy timeouts** | **LOW** | `proxy_read_timeout`, `proxy_connect_timeout` not set. Slow clients could hold connections open. | Add sensible timeouts in the location block. |
| 8 | **Large body size limit** | **LOW** | `client_max_body_size 50M` in `/etc/nginx/nginx.conf` is large for a static site. | Reduce to `1M` since the site only serves static content. |
| 9 | **`web_conf.json` publicly exposed** | **LOW** | Contact email and phone number are accessible at `/blooms/web_conf.json`. Intended behaviour, but worth noting for awareness. | No action needed if contact info is meant to be public. |
| 10 | **Router port 80 forwarding** | **INFO** | Only port 80 is forwarded. All other ports are blocked by the router. This limits exposure but means HTTPS requires either port 443 forwarding or a tunnel service. | Forward port 443 if/when SSL is set up. |

---

## Rollback Instructions

### To remove the site entirely:

```bash
# 1. Stop the Node.js server
kill $(pgrep -f "node.*server.js")

# 2. Remove the server file
rm /home/bloomsmobility/lab/aiprojects/blooms.ai/server.js

# 3. Remove the nginx location block
# Edit /etc/nginx/sites-available/lms and delete the location /blooms/ block (lines 18-25)
sudo sed -i '/location \/blooms\//,/^    }/d' /etc/nginx/sites-available/lms

# 4. Test and reload nginx
sudo nginx -t && sudo systemctl reload nginx

# 5. (Optional) Delete this doc
rm /home/bloomsmobility/lab/aiprojects/blooms.ai/Public_site_steps.md

# 6. (Optional) Delete leftover temp file
rm /tmp/nginx-default.conf
```

### To pause the site (keep config, stop serving):

```bash
kill $(pgrep -f "node.*server.js")
# nginx will return 502 for /blooms/ until the backend is restarted
```

### To restart the backend:

```bash
cd /home/bloomsmobility/lab/aiprojects/blooms.ai
nohup node server.js > /tmp/blooms-backend.log 2>&1 &
```

---

## Recommended nginx hardening additions

Add to the `location /blooms/` block in `/etc/nginx/sites-available/lms`:

```nginx
proxy_connect_timeout 5s;
proxy_read_timeout 10s;
proxy_send_timeout 10s;
```

Add to the `http` block in `/etc/nginx/nginx.conf`:

```nginx
server_tokens off;

# Rate limiting
limit_req_zone $binary_remote_addr zone=blooms:10m rate=10r/s;
```

Then in the location block:

```nginx
limit_req zone=blooms burst=20 nodelay;
```

---

## systemd service example

Create `/etc/systemd/system/blooms-backend.service`:

```ini
[Unit]
Description=Blooms.ai static file server
After=network.target

[Service]
Type=simple
User=bloomsmobility
WorkingDirectory=/home/bloomsmobility/lab/aiprojects/blooms.ai
ExecStart=/usr/bin/node server.js
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable: `sudo systemctl enable --now blooms-backend.service`

---

---

## Demo Apps Section

**URL:** `http://106.51.105.16/blooms/demo/`
**Auth:** HTTP Basic Auth (browser popup)
**Username:** `demo`
**Password:** `Oo&6Kjl1Bh` (stored in `web_conf.json` and `democonfig.json`)

### Architecture

```
Browser → /blooms/demo/ → nginx proxy → server.js → auth check → docker container
```

- All `/demo/` paths are protected by HTTP Basic Auth
- `server.js` checks credentials against `democonfig.json`
- The demo list page at `/demo/` shows all configured apps
- Each app is proxied to its internal docker URL

### Adding a new demo app

Edit `democonfig.json` (`/home/bloomsmobility/lab/aiprojects/blooms.ai/democonfig.json`) and add an entry to the `apps` array:

```json
{
  "username": "demo",
  "password": "Oo&6Kjl1Bh",
  "apps": [
    {
      "display": "My App Name",
      "internal_url": "http://localhost:3000"
    }
  ]
}
```

- `display` — name shown on the demo list and used in the URL (`/demo/My App Name`)
- `internal_url` — the docker container's internal URL (must be reachable from this machine)
- After editing, restart the Node.js server: `kill $(pgrep -f "node.*server.js") && cd /home/bloomsmobility/lab/aiprojects/blooms.ai && nohup node server.js > /tmp/blooms-backend.log 2>&1 &`

### Auth credentials

Stored in:
- `/home/bloomsmobility/lab/aiprojects/blooms.ai/democonfig.json` — used by server.js for auth
- `/home/bloomsmobility/lab/aiprojects/blooms.ai/web_conf.json` — reference copy

To change the password, update both files. Username is always `demo`.

### Health & security

- If a docker container is unreachable, the proxy returns a 502 Bad Gateway page
- Auth is checked on every request (no sessions or cookies)
- Password should be rotated periodically

## HTTPS setup (future work)

1. Install certbot: `sudo apt install certbot python3-certbot-nginx`
2. Obtain cert: `sudo certbot --nginx -d your-domain.com`
3. Forward port 443 on router (192.168.0.1) → 192.168.0.109
4. Update nginx config to handle HTTPS and redirect HTTP → HTTPS
