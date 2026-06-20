# Regression Tests: Blooms.ai

> **Product**: Company Website & Demo Application Gateway
> **Documentation**: (Derived from source — no dedicated product doc yet)
> **Source**: `blooms.ai/`

---

## Test Tag Convention

Each test case is tagged with:
- **REQ** — Requirement description (inline, no formal doc yet)
- **IMPL** — Link to implementation file and line number
- **TC** — Test case identifier

---

## TC-BA-API-001: Landing Page Serves HTML

| Field | Value |
|---|---|
| **Test ID** | `TC-BA-API-001` |
| **Title** | GET `/` returns landing page HTML |
| **REQ** | Serve company landing page with hero, about, services, contact |
| **IMPL** | [`blooms.ai/server.js:236-237`](../blooms.ai/server.js#L236-L237), [`blooms.ai/index.html`](../blooms.ai/index.html) |
| **Precondition** | Node.js server running on port 3369 |
| **Steps** | 1. Send `GET /`<br>2. Inspect response headers and body |
| **Expected** | HTTP 200. `Content-Type: text/html`. Body contains: `<section id="hero">`, `<section id="about">`, `<section id="services">`, `<section id="contact">`. Theme toggle button present. Navigation links present (About, Services, Contact, Demos). |
| **Pass Criteria** | All sections are present in the HTML. |

---

## TC-BA-API-002: Dynamic Content from web_conf.json

| Field | Value |
|---|---|
| **Test ID** | `TC-BA-API-002` |
| **Title** | Landing page populates content from `web_conf.json` via JavaScript |
| **REQ** | Site content is loaded dynamically from JSON configuration |
| **IMPL** | [`blooms.ai/js/app.js:24-78`](../blooms.ai/js/app.js#L24-L78), [`blooms.ai/web_conf.json`](../blooms.ai/web_conf.json) |
| **Precondition** | Browser/client executing JavaScript |
| **Steps** | 1. Load `/` in a browser or headless client<br>2. Check that `web_conf.json` is fetched<br>3. Verify company name, tagline, description, services populate the DOM |
| **Expected** | Page title is "Blooms.ai". Hero tagline is "Modernizing enterprise systems with responsible AI". About section contains the full description HTML. Three service cards are rendered (AI Consulting, AI Development, AI QA). Contact email and phone are displayed. |
| **Pass Criteria** | All 3 services rendered. Company name, tagline, contact info present. |

---

## TC-BA-API-003: Static File Serving — CSS

| Field | Value |
|---|---|
| **Test ID** | `TC-BA-API-003` |
| **Title** | GET `/css/styles.css` returns valid CSS |
| **REQ** | Serve static assets with correct MIME types |
| **IMPL** | [`blooms.ai/server.js:38-50`](../blooms.ai/server.js#L38-L50), [`blooms.ai/css/styles.css`](../blooms.ai/css/styles.css) |
| **Precondition** | Server running |
| **Steps** | 1. Send `GET /css/styles.css` |
| **Expected** | HTTP 200. `Content-Type: text/css`. Body is valid CSS (contains `:root`, `body`, etc.). |
| **Pass Criteria** | CSS file is served with correct MIME type. |

---

## TC-BA-API-004: Static File Serving — JavaScript

| Field | Value |
|---|---|
| **Test ID** | `TC-BA-API-004` |
| **Title** | GET `/js/app.js` returns valid JavaScript |
| **REQ** | Serve static assets with correct MIME types |
| **IMPL** | [`blooms.ai/server.js:38-50`](../blooms.ai/server.js#L38-L50), [`blooms.ai/js/app.js`](../blooms.ai/js/app.js) |
| **Precondition** | Server running |
| **Steps** | 1. Send `GET /js/app.js` |
| **Expected** | HTTP 200. `Content-Type: application/javascript`. Body contains exports/service card rendering logic. |
| **Pass Criteria** | JS file is served with correct MIME type. |

---

## TC-BA-API-005: 404 for Unknown Paths

| Field | Value |
|---|---|
| **Test ID** | `TC-BA-API-005` |
| **Title** | GET `/nonexistent` returns 404 |
| **REQ** | Return 404 for unknown static file paths |
| **IMPL** | [`blooms.ai/server.js:41-46`](../blooms.ai/server.js#L41-L46) |
| **Precondition** | Server running |
| **Steps** | 1. Send `GET /nonexistent.html`<br>2. Send `GET /css/nonexistent.css` |
| **Expected** | Both return HTTP 404 with `Content-Type: text/html` and `<h1>404 Not Found</h1>` |
| **Pass Criteria** | Unknown paths return 404 with HTML error message. |

---

## TC-BA-DEMO-001: Demo Listing — Authenticated

| Field | Value |
|---|---|
| **Test ID** | `TC-BA-DEMO-001` |
| **Title** | GET `/demo/` with valid credentials returns demo app listing |
| **REQ** | Demo listing page shows configured apps |
| **IMPL** | [`blooms.ai/server.js:195-206`](../blooms.ai/server.js#L195-L206), [`blooms.ai/server.js:110-148`](../blooms.ai/server.js#L110-L148) |
| **Precondition** | Server running. Valid Basic Auth credentials known (demo / Oo&6Kjl1Bh). |
| **Steps** | 1. Send `GET /demo/` with `Authorization: Basic <base64(demo:Oo&6Kjl1Bh)>` |
| **Expected** | HTTP 200. HTML contains: heading "Demo Applications", links to `faq_chatbot/` and `Model_Benchmark/` as demo cards. Each card shows the app display name and an "Open →" link. |
| **Pass Criteria** | All apps from `democonfig.json` are rendered as cards. Page title contains "Demos". |

---

## TC-BA-DEMO-002: Demo Listing — Unauthenticated

| Field | Value |
|---|---|
| **Test ID** | `TC-BA-DEMO-002` |
| **Title** | GET `/demo/` without valid credentials returns 401 |
| **REQ** | HTTP Basic Auth required for demo section |
| **IMPL** | [`blooms.ai/server.js:60-66`](../blooms.ai/server.js#L60-L66), [`196-200`](../blooms.ai/server.js#L196-L200) |
| **Precondition** | Server running |
| **Steps** | 1. Send `GET /demo/` without Authorization header<br>2. Send `GET /demo/` with invalid `Authorization: Basic <bad_base64>` |
| **Expected** | Both return HTTP 401. `WWW-Authenticate: Basic realm="Demo Apps"` header present. Body is `<h1>401 Unauthorized</h1>`. |
| **Pass Criteria** | 401 returned with WWW-Authenticate header. |

---

## TC-BA-DEMO-003: Demo App Proxy — Running Container

| Field | Value |
|---|---|
| **Test ID** | `TC-BA-DEMO-003` |
| **Title** | GET `/demo/faq_chatbot/` proxies to running FAQ Chatbot container |
| **REQ** | Proxy to internal Docker containers |
| **IMPL** | [`blooms.ai/server.js:80-102`](../blooms.ai/server.js#L80-L102), [`208-232`](../blooms.ai/server.js#L208-L232), [`democonfig.json`](../blooms.ai/democonfig.json) |
| **Precondition** | FAQ Chatbot Docker container running on port 5050. Valid auth provided. |
| **Steps** | 1. Send `GET /demo/faq_chatbot/` with valid credentials<br>2. Inspect response |
| **Expected** | HTTP 200. Response body is the FAQ Chatbot HTML page (contains "FAQ Chatbot" header, chat area, input bar). Response is proxied from the internal container. |
| **Pass Criteria** | FAQ Chatbot UI is served through the proxy. |

---

## TC-BA-DEMO-004: Demo App Proxy — Unavailable Container

| Field | Value |
|---|---|
| **Test ID** | `TC-BA-DEMO-004` |
| **Title** | GET `/demo/faq_chatbot/` when container is down returns 502 |
| **REQ** | Return 502 Bad Gateway when proxied app is unavailable |
| **IMPL** | [`blooms.ai/server.js:96-99`](../blooms.ai/server.js#L96-L99) |
| **Precondition** | FAQ Chatbot container is NOT running. Valid auth provided. |
| **Steps** | 1. Stop FAQ Chatbot container<br>2. Send `GET /demo/faq_chatbot/` with valid credentials |
| **Expected** | HTTP 502. Body contains `<h1>502 Bad Gateway</h1>` and "Demo app is not available." |
| **Pass Criteria** | Unavailable proxied app returns 502 with descriptive error. |

---

## TC-BA-DEMO-005: Demo App — Not Found

| Field | Value |
|---|---|
| **Test ID** | `TC-BA-DEMO-005` |
| **Title** | GET `/demo/nonexistent_app/` returns 404 |
| **REQ** | Return 404 for unknown demo app names |
| **IMPL** | [`blooms.ai/server.js:221-226`](../blooms.ai/server.js#L221-L226) |
| **Precondition** | Valid auth provided |
| **Steps** | 1. Send `GET /demo/nonexistent_app/` with valid credentials |
| **Expected** | HTTP 404. Body contains "Demo app not found." |
| **Pass Criteria** | Unknown demo app returns 404. |

---

## TC-BA-DEMO-006: Trailing Slash Redirect

| Field | Value |
|---|---|
| **Test ID** | `TC-BA-DEMO-006` |
| **Title** | GET `/demo/faq_chatbot` (no trailing slash) redirects to `/demo/faq_chatbot/` |
| **REQ** | Redirect bare demo paths to trailing-slash version for correct relative URL resolution |
| **IMPL** | [`blooms.ai/server.js:215-219`](../blooms.ai/server.js#L215-L219) |
| **Precondition** | Valid auth provided |
| **Steps** | 1. Send `GET /demo/faq_chatbot` with valid credentials (no trailing slash)<br>2. Do NOT follow redirect |
| **Expected** | HTTP 302. `Location` header contains `/blooms/demo/faq_chatbot/`. |
| **Pass Criteria** | Redirect to trailing-slash URL occurs. |

---

## TC-BA-ANALYTICS-001: Record Page View

| Field | Value |
|---|---|
| **Test ID** | `TC-BA-ANALYTICS-001` |
| **Title** | POST `/api/analytics` records a page view |
| **REQ** | Analytics collection via POST API |
| **IMPL** | [`blooms.ai/server.js:154-162`](../blooms.ai/server.js#L154-L162) |
| **Precondition** | Server running |
| **Steps** | 1. Send `POST /api/analytics` with `{"url": "http://test.com/page", "ref": "http://referrer.com", "w": 1920, "h": 1080, "lang": "en"}` |
| **Expected** | HTTP 200. `{"ok": true}`. Entry is appended to `/tmp/blooms-analytics.ndjson`. |
| **Pass Criteria** | Response is `{"ok": true}`. Analytics log file contains the new entry. |

---

## TC-BA-ANALYTICS-002: Get Analytics Data

| Field | Value |
|---|---|
| **Test ID** | `TC-BA-ANALYTICS-002` |
| **Title** | GET `/api/analytics/data` returns aggregated analytics |
| **REQ** | Analytics aggregation endpoint |
| **IMPL** | [`blooms.ai/server.js:165-186`](../blooms.ai/server.js#L165-L186) |
| **Precondition** | At least one analytics entry exists |
| **Steps** | 1. Record a few analytics entries via POST<br>2. Send `GET /api/analytics/data` |
| **Expected** | JSON response with: `total` (integer), `last24h` (integer), `last7d` (integer), `pages` (array of [url, count]), `referrers` (array of [host, count]), `timeline` (array of [hour, count]). |
| **Pass Criteria** | `total` matches number of recorded entries. `pages` lists the tracked URLs. |

---

## TC-BA-ANALYTICS-003: Analytics Dashboard

| Field | Value |
|---|---|
| **Test ID** | `TC-BA-ANALYTICS-003` |
| **Title** | GET `/analytics` returns analytics dashboard HTML |
| **REQ** | Analytics dashboard page |
| **IMPL** | [`blooms.ai/server.js:189-192`](../blooms.ai/server.js#L189-L192), [`blooms.ai/analytics.html`](../blooms.ai/analytics.html) |
| **Precondition** | Server running |
| **Steps** | 1. Send `GET /analytics` |
| **Expected** | HTTP 200. `Content-Type: text/html`. Body contains analytics dashboard structure. |
| **Pass Criteria** | HTML is returned successfully. |

---

## TC-BA-CONFIG-001: democonfig.json Loads Correctly

| Field | Value |
|---|---|
| **Test ID** | `TC-BA-CONFIG-001` |
| **Title** | democonfig.json is valid and contains expected apps |
| **REQ** | Demo routing configuration |
| **IMPL** | [`blooms.ai/democonfig.json`](../blooms.ai/democonfig.json), [`blooms.ai/server.js:22-25`](../blooms.ai/server.js#L22-L25) |
| **Precondition** | Server running |
| **Steps** | 1. Read `democonfig.json`<br>2. Inspect structure |
| **Expected** | Valid JSON with `username`, `password`, and `apps` array. Apps array contains at least `faq_chatbot` (→ `http://localhost:5050`) and `Model_Benchmark` (→ `http://localhost:5052`). |
| **Pass Criteria** | JSON is valid. Apps are correctly configured with internal URLs. |

---

## TC-BA-CONFIG-002: web_conf.json Loads Correctly

| Field | Value |
|---|---|
| **Test ID** | `TC-BA-CONFIG-002` |
| **Title** | web_conf.json is valid and contains all required fields |
| **REQ** | Site content configuration |
| **IMPL** | [`blooms.ai/web_conf.json`](../blooms.ai/web_conf.json), [`blooms.ai/js/app.js`](../blooms.ai/js/app.js) |
| **Precondition** | None |
| **Steps** | 1. Read `web_conf.json`<br>2. Inspect structure |
| **Expected** | Valid JSON with: `company_name`, `tagline`, `description`, `contact` (email, phone), `services` (array of 3 with title, desc, icon), `demo` (url, username, password), `social_links`. |
| **Pass Criteria** | All required fields present. Services array has 3 entries. |

---

## TC-BA-UI-001: Theme Toggle Persistence

| Field | Value |
|---|---|
| **Test ID** | `TC-BA-UI-001` |
| **Title** | Theme toggle switches dark/light mode and persists |
| **REQ** | Dark/light theme with localStorage persistence |
| **IMPL** | [`blooms.ai/js/app.js:84-97`](../blooms.ai/js/app.js#L84-L97) |
| **Precondition** | Page loaded in browser |
| **Steps** | 1. Click theme toggle button<br>2. Verify `data-theme` attribute on `<html>`<br>3. Refresh page<br>4. Close browser, reopen page |
| **Expected** | Theme toggles between light and dark. `data-theme` attribute matches. Theme persists across page refresh and browser restart via `localStorage`. |
| **Pass Criteria** | `localStorage.getItem('theme')` matches active theme. Toggle switches correctly. |

---

## TC-BA-SEC-001: Path Traversal Prevention

| Field | Value |
|---|---|
| **Test ID** | `TC-BA-SEC-001` |
| **Title** | Path traversal attacks return 404, not sensitive files |
| **REQ** | Prevent directory traversal via URL manipulation |
| **IMPL** | [`blooms.ai/server.js:236-237`](../blooms.ai/server.js#L236-L237) |
| **Precondition** | Server running |
| **Steps** | 1. Send `GET /../../../etc/passwd`<br>2. Send `GET /..%2f..%2f..%2fetc/passwd`<br>3. Send `GET /%2e%2e%2f%2e%2e%2fetc/passwd` |
| **Expected** | All return HTTP 404. System files are not exposed. |
| **Pass Criteria** | Path traversal attempts return 404, not files outside the web root. |

---

## Regression Test Summary: Blooms.ai

| Area | Test Count |
|---|---|
| API / Static File Tests | 5 |
| Demo Auth & Proxy Tests | 6 |
| Analytics Tests | 3 |
| Configuration Tests | 2 |
| UI Tests | 1 |
| Security Tests | 1 |
| **Total** | **18** |
