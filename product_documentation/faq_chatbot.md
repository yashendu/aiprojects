# FAQ Chatbot — Document Q&A with RAG

**Secure Local Intelligence: Enterprise AI Without the Cloud Risk**

For organizations handling strict regulatory compliance, proprietary IP, and highly confidential workforce records, public cloud LLMs are a non-starter.

Our enterprise-grade AI platform brings the power of advanced generative intelligence entirely within your controlled perimeter. By deploying on-premise, your data never transits external networks, never trains public models, and remains completely isolated from third-party exposure.

Powered by the latest open-weights breakthrough, Llama 3.2, our architecture balances low-latency processing with exceptional instruction-following accuracy—delivering hyper-secure, cloud-independent AI directly onto your infrastructure.

### Core Enterprise Use Cases

Organizations leverage this local AI platform to safely automate high-risk knowledge retrieval across departments:

**Human Resources & Operations:** Securely query sensitive internal employee handbooks, payroll policies, and health insurance guidelines without exposing internal workforce details to the web.

**Legal & Compliance Audit:** Rapidly parse complex vendor contracts, historical litigation files, and local regulatory updates to check for compliance risks in minutes rather than days.

**Information Security & IT Support:** Provide an internal tech support or documentation assistant that handles proprietary network configurations, software codebases, and infrastructure schema completely offline.

**Financial & Intellectual Property Analysis:** Query highly confidential earnings reports, proprietary research papers, and market strategy briefs with zero risk of leakages.

---

## 1. Requirements

### Functional Requirements
- **Document Ingestion**: Accept documents via file upload (PDF, DOCX, PPTX, TXT, MD, CSV, JSON, XML, HTML), raw text paste, or pre-loaded sample document.
- **Retrieval-Augmented Generation**: Parse user questions against indexed document content and answer strictly from that context.
- **Session Management**: Maintain per-user chat history and document state across API calls.
- **Sample Document**: Provide a pre-loaded HR policy manual (270-page PDF) for immediate demo without upload.
- **Chat Interface**: Single-page web UI with message history, typing indicators, and follow-up suggestions.
- **Context-Only Answers**: LLM must refuse to answer questions whose answer is not in the loaded document, with a polite out-of-context message.

### Non-Functional Requirements
- **Deployment**: Containerized via Docker, served behind an nginx reverse proxy at `/blooms/demo/faq_chatbot/`.
- **Authentication**: HTTP Basic Auth enforced at the proxy layer (shared demo credentials).
- **Latency**: Embedding generation and LLM inference happen locally via Ollama (no cloud dependency).
- **Scalability**: Single-worker gunicorn, in-memory sessions (not suitable for horizontal scaling without a shared session store).
- **Security**: 2 MB upload limit, file-type whitelist, temp-file cleanup, no persistent storage of user uploads.

---

## 2. Product Features

| Feature | Description |
|---|---|
| **Sample Document** | One-click load of a 270-page HR policy manual (131 indexed sections) for instant demo. |
| **File Upload** | Drag-and-select upload with support for 11 file formats. Max 2 MB per file. |
| **Text Paste** | Paste raw text up to 10,000 lines for ad-hoc Q&A. |
| **RAG Q&A** | Ask natural-language questions; answers are grounded in the loaded document only. |
| **Chat History** | Session-persistent message history displayed in the UI. |
| **Typing Indicator** | Animated dots during LLM inference. |
| **Follow-Up Suggestions** | After the first few exchanges, the LLM generates 3 suggested questions based on document context. |
| **New Chat** | Reset session and clear document index. |
| **Responsive UI** | Purple-themed design adapting to desktop, tablet, and mobile viewports. |

---

## 3. Design Choices

### 3.1 RAG over Fine-Tuning
- **Choice**: Retrieval-Augmented Generation instead of fine-tuning the LLM on each document.
- **Rationale**: Documents are user-provided and ephemeral. Fine-tuning would be impractical per session. RAG allows arbitrary documents to be queried without model retraining.
- **Trade-off**: Requires a vector database (ChromaDB) and embedding step per document; increases latency on first query vs. pre-fine-tuned models.

### 3.2 ChromaDB (PersistentClient)
- **Choice**: Local ChromaDB with `PersistentClient`, one collection per session.
- **Rationale**: Lightweight, no separate server process, stores vectors on disk at `/app/chroma/<session_id>/`. Session isolation prevents cross-contamination.
- **Trade-off**: Not distributed; data volume grows with active sessions. Since sessions are cleaned on "New Chat", this is acceptable for single-instance deployment.

### 3.3 Ollama (Local LLM)
- **Choice**: `gemma4:12b` for generation, `nomic-embed-text` for embeddings, both served by a local Ollama instance on the host.
- **Rationale**: Zero cloud cost, no data leaves the server, low latency (no network hop to external API).
- **Trade-off**: `gemma4:12b` is ~12B parameters → ~30-50s inference time on CPU-bound hardware. The 12B model was chosen for better answer quality over smaller alternatives.

### 3.4 Word-Level Chunking
- **Choice**: Split document text into word-based chunks (500 words, 50-word overlap).
- **Rationale**: Simple, language-agnostic, works equally well for all supported file formats. Overlap preserves context across chunk boundaries.
- **Trade-off**: Not as semantically aware as sentence- or paragraph-level splitting; may truncate mid-sentence. Acceptable given chunk overlap mitigates information loss.

### 3.5 In-Memory Sessions
- **Choice**: Python dict-based `SessionManager` with Flask signed cookies for session ID.
- **Rationale**: Simple, zero-dependency, sufficient for single-worker deployment. Flask's `session` object provides tamper-proof cookie storage.
- **Trade-off**: Lost on container restart; does not scale across multiple workers/instances.

### 3.6 Gunicorn Single Worker
- **Choice**: 1 gunicorn worker with 120s timeout.
- **Rationale**: In-memory session state requires single worker to avoid request-routing inconsistencies. 120s timeout accommodates slow LLM inference.
- **Trade-off**: No concurrency for multiple simultaneous users; requests queue behind the single worker.

### 3.7 Proxy Architecture (nginx → Node.js → Docker)
- **Choice**: nginx proxies `/blooms/` → Node.js server (port 3369) → proxies `/demo/` paths to Docker containers.
- **Rationale**: nginx handles port 80 (only port open on router). Node.js provides auth enforcement, demo routing, analytics, and static file serving in one process.
- **Trade-off**: Extra hop adds latency; both proxies must be configured with matching timeout values to avoid premature connection drops.

### 3.8 Frontend: Vanilla JS + CSS
- **Choice**: Single HTML file with no framework (no React, Vue, etc.).
- **Rationale**: No build step, no npm dependencies, deploys as a single file. The UI is simple enough that a framework adds unnecessary complexity.
- **Trade-off**: Harder to maintain as complexity grows; no component model.

---

## 4. High-Level Design

```
┌─────────┐      ┌──────────┐      ┌───────────┐      ┌────────┐
│ Browser │ ───→ │  nginx   │ ───→ │  Node.js  │ ───→ │  Flask │
│  (User) │ ←─── │ port 80  │ ←─── │ port 3369 │ ←─── │ :5050  │
└─────────┘      └──────────┘      └───────────┘      └────────┘
                                       │    ↑              │
                                       │    │              │
                                       │  ┌─┴────────┐    │
                                       │  │ ChromaDB │    │
                                       │  │ (on-disk │    │
                                       │  │  vectors)│    │
                                       │  └──────────┘    │
                                       │                   │
                                       │  ┌───────────────┐│
                                       │  │   Ollama      ││
                                       │  │  (host)       ││
                                       │  │ gemma4:12b    ││
                                       │  │ nomic-embed   ││
                                       │  └───────────────┘│
                                       ↓                   ↓
                                  ┌─────────────────────────┐
                                  │  Static Files / Analytics│
                                  │      (server.js)         │
                                  └─────────────────────────┘
```

### Request Flow (Chat)
1. Browser sends `POST /api/chat` → nginx strips `/blooms/` prefix → Node.js
2. Node.js checks Basic Auth (democonfig.json) → 401 if missing
3. Node.js proxies to Flask container (`http://localhost:5050/api/chat`)
4. Flask reads session cookie → validates → retrieves session ID
5. Flask calls `query_document(question, sid)`:
   - ChromaDB reads persisted vectors from `/app/chroma/<sid>/`
   - Ollama embeds the question via `nomic-embed-text`
   - ChromaDB returns top-4 relevant chunks
6. Flask constructs prompt (system template + context + history + question)
7. Flask calls Ollama's `/api/generate` with `gemma4:12b`
8. LLM returns answer → Flask saves to session history → returns JSON
9. Response flows back: Flask → Node.js → nginx → Browser

---

## 5. Product Architecture

### 5.1 Directory Structure

```
faq_chatbot/
├── app/
│   ├── __init__.py              # Package marker (empty)
│   ├── main.py                  # Flask app: routes, Ollama calls, orchestration
│   ├── rag_engine.py            # ChromaDB client, embedding, chunking, indexing, query
│   ├── session_manager.py       # In-memory SessionManager class
│   ├── document_loader.py       # Multi-format document parser (PDF, DOCX, PPTX, TXT, …)
│   └── templates/
│       └── index.html           # Single-page frontend (vanilla JS + CSS)
├── config.yaml                  # All config: Ollama, chunking, limits, sample path
├── Dockerfile                   # Python 3.11-slim, gunicorn entrypoint
├── docker-compose.yml           # Service definition, port mapping, volume mounts
├── requirements.txt             # Python dependencies
└── samples/
    └── policy/
        └── HR_Policy_Manual.pdf # Pre-loaded 270-page sample document
```

### 5.2 Component Breakdown

#### 5.2.1 `app/main.py` — Flask Application
- **Routes**:
  - `GET /` — Renders the chat UI template with sample availability status.
  - `POST /api/start` — Creates new session, returns session ID and greeting.
  - `POST /api/load_sample` — Loads and indexes the configured sample PDF.
  - `POST /api/upload` — Accepts multipart file upload, validates extension and size, saves to temp, loads, indexes, cleans up.
  - `POST /api/paste` — Accepts JSON body with `text`, validates line count, indexes.
  - `POST /api/chat` — Core RAG: retrieves context, queries Ollama, returns answer + suggestions.
  - `POST /api/restart` — Clears old session+vectors, creates new session.
- **Key Design**: `call_ollama()` wraps the `/api/generate` endpoint with 120s timeout. Error handling returns user-facing messages for timeout, connection failure, and generic errors.

#### 5.2.2 `app/rag_engine.py` — Retrieval Pipeline
- **`embed_texts(texts, config)`**: Batches texts and calls Ollama `/api/embed` with `nomic-embed-text`. 120s timeout.
- **`chunk_text(text, chunk_size, chunk_overlap)`**: Word-level splitting. Configurable via `config.yaml`.
- **`index_document(text, session_id, config)`**: Creates/recreates ChromaDB collection per session. Embeds chunks, stores with sequential IDs.
- **`query_document(question, session_id, config)`**: Embeds the question, queries ChromaDB for top-k chunks, returns document texts.
- **`clear_document(session_id)`**: Removes the on-disk ChromaDB persistence directory.

#### 5.2.3 `app/session_manager.py` — State Management
- `SessionManager` singleton wraps a `dict[sid → Session]`.
- Each `Session` holds: `history` (list of `{role, text}`), `document_loaded` (bool), `document_name` (str).
- Session ID is a 12-char hex UUID (`uuid.uuid4().hex[:12]`).
- Flask's signed cookie (`session['sid']`) persists the session ID across requests.

#### 5.2.4 `app/document_loader.py` — File Parsing
- Extension-to-loader mapping supports: `.txt`, `.md`, `.csv`, `.json`, `.xml`, `.html` (plain text), `.pdf` (PyMuPDF/fitz), `.docx`/`.doc` (python-docx), `.pptx`/`.ppt` (python-pptx).
- All text is normalized (whitespace collapsed) before return.
- Unsupported extensions raise `ValueError`.

#### 5.2.5 `config.yaml` — Configuration
- **Ollama**: host URL, generation model (`gemma4:12b`), embedding model (`nomic-embed-text`).
- **Generation**: temperature 0.1, top_p 0.9, max_tokens 2048, repeat_penalty 1.1.
- **Chunking**: 500-word chunks, 50-word overlap, top-4 retrieval.
- **Limits**: 2 MB upload, 10,000 line paste.
- **Sample**: path to PDF, display description, original URL.

### 5.3 Deployment Architecture

```
                            Internet
                               │
                        ┌──────┴──────┐
                        │   Router    │
                        │  (port 80)  │
                        └──────┬──────┘
                               │
                        ┌──────┴──────┐
                        │   nginx     │  ← /etc/nginx/sites-available/lms
                        │  port 80    │     proxy_read_timeout 300s
                        └──────┬──────┘
                               │ /blooms/ → http://127.0.0.1:3369/
                        ┌──────┴──────┐
                        │  Node.js    │  ← server.js, port 3369
                        │  (server.js)│     auth → democonfig.json
                        └──────┬──────┘     proxy demo/* → docker
                               │
                    ┌──────────┴──────────┐
                    │                     │
           /demo/faq_chatbot/      Static files (/, /analytics)
                    │
             ┌──────┴──────┐
             │  Docker     │
             │  :5050→:5000│
             └──────┬──────┘
                    │
             ┌──────┴──────┐
             │   Flask     │  ← gunicorn, 1 worker, 120s timeout
             │   :5000     │
             └──────┬──────┘
                    │
        ┌───────────┴───────────┐
        │                       │
  ChromaDB (disk)          Ollama (host)
  /app/chroma/<sid>/       host.docker.internal:11434
                              gemma4:12b
                              nomic-embed-text
```

### 5.4 API Reference

| Endpoint | Method | Auth | Payload | Response |
|---|---|---|---|---|
| `/` | GET | Basic | — | HTML page |
| `/api/start` | POST | Basic | — | `{session_id, messages}` |
| `/api/load_sample` | POST | Session | — | `{message, messages}` |
| `/api/upload` | POST | Session | `multipart/form-data` (file) | `{message, messages}` |
| `/api/paste` | POST | Session | `{"text": "..."}` | `{message, messages}` |
| `/api/chat` | POST | Session | `{"question": "..."}` | `{response, messages, suggestions}` |
| `/api/restart` | POST | Session | — | `{session_id, messages}` |

> **Auth**: "Basic" means HTTP Basic Auth checked by Node.js proxy. "Session" means a valid Flask session cookie is required (obtained via `/api/start`).

### 5.5 Security Considerations

| Concern | Mitigation |
|---|---|
| Unauthorized access | HTTP Basic Auth at Node.js proxy layer |
| Large file uploads | 2 MB limit enforced by Flask config |
| Arbitrary file types | Extension whitelist in `document_loader.py` |
| Temp file leakage | `try/finally` cleanup in upload handler |
| XSS via pasted text | `textContent` (not `innerHTML`) for message rendering |
| Session forgery | Flask signed cookies with random `secret_key` per container start |
| ChromaDB telemetry | Disabled via `Settings(anonymized_telemetry=False)` |
| Out-of-context answers | System prompt rules enforced; no external knowledge injected |

### 5.6 Known Limitations

- **Latency**: gemma4:12b takes 30-50s per answer on current hardware. The nginx proxy timeout was increased to 300s to accommodate this.
- **Single Worker**: No concurrent request handling; requests queue behind gunicorn's single sync worker.
- **Ephemeral Sessions**: Sessions and vector indexes are lost on container restart. Sample must be re-loaded.
- **No Streaming**: LLM responses are generated fully before returning to the client. No token-by-token streaming.
- **Chunking Granularity**: Word-level 500-word chunks may not align with semantic boundaries (paragraphs, sections).
