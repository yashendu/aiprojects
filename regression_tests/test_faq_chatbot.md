# Regression Tests: FAQ Chatbot

> **Product**: Document Q&A with RAG
> **Documentation**: `product_documentation/faq_chatbot.md`
> **Source**: `faq_chatbot/`

---

## Test Tag Convention

Each test case is tagged with:
- **REQ** — Link to requirement in product documentation
- **IMPL** — Link to implementation file and line number
- **TC** — Test case identifier

---

## TC-FC-API-001: Session Creation

| Field | Value |
|---|---|
| **Test ID** | `TC-FC-API-001` |
| **Title** | POST `/api/start` creates a new session and returns initial greeting |
| **REQ** | [§1 - Session Management](product_documentation/faq_chatbot.md#L30), [§5.2.1 - /api/start](product_documentation/faq_chatbot.md#L176) |
| **IMPL** | [`faq_chatbot/app/main.py:99-106`](../faq_chatbot/app/main.py#L99-L106), [`faq_chatbot/app/session_manager.py:8-15`](../faq_chatbot/app/session_manager.py#L8-L15) |
| **Precondition** | Docker container running, Ollama accessible |
| **Steps** | 1. Send `POST /api/start` with empty body<br>2. Inspect JSON response |
| **Expected** | Response body is `{"session_id": "<12-char hex>", "messages": [...], "suggestions": [...]}`. First message role is `"assistant"` with greeting text. A `Set-Cookie` header is present with the Flask session cookie. |
| **Pass Criteria** | Session ID is a 12-character hex string. Response contains both `messages` array and `suggestions` array. |

---

## TC-FC-API-002: Missing Session Returns Error

| Field | Value |
|---|---|
| **Test ID** | `TC-FC-API-002` |
| **Title** | Endpoints requiring session return 400 when no session cookie |
| **REQ** | [§5.4 - Auth: Session](product_documentation/faq_chatbot.md#L258-L261) |
| **IMPL** | [`faq_chatbot/app/main.py:111-113`](../faq_chatbot/app/main.py#L111-L113), [`189-193`](../faq_chatbot/app/main.py#L189-L193) |
| **Precondition** | No Flask session cookie present |
| **Steps** | 1. Send `POST /api/chat` with `{"question": "hello"}` without session cookie<br>2. Send `POST /api/upload` without session cookie<br>3. Send `POST /api/paste` without session cookie |
| **Expected** | Each returns HTTP 400 with `{"error": "No session"}` or `{"error": "No session. Please refresh."}` |
| **Pass Criteria** | All three endpoints return 400 with error message containing "No session". |

---

## TC-FC-API-003: Chat Without Document

| Field | Value |
|---|---|
| **Test ID** | `TC-FC-API-003` |
| **Title** | Chat returns document-not-loaded message when no document indexed |
| **REQ** | [§1 - Context-Only Answers](product_documentation/faq_chatbot.md#L33) |
| **IMPL** | [`faq_chatbot/app/main.py:205-211`](../faq_chatbot/app/main.py#L205-L211) |
| **Precondition** | Valid session exists, no document loaded |
| **Steps** | 1. `POST /api/start` to get session<br>2. `POST /api/chat` with `{"question": "What is the leave policy?"}` |
| **Expected** | Response contains `"response": "I don't have any document loaded yet. Please upload a document or paste text to get started."` |
| **Pass Criteria** | Response message matches the no-document-loaded template. |

---

## TC-FC-API-004: File Upload — Valid PDF

| Field | Value |
|---|---|
| **Test ID** | `TC-FC-API-004` |
| **Title** | Upload a valid PDF document and verify indexing |
| **REQ** | [§1 - Document Ingestion](product_documentation/faq_chatbot.md#L28), [§5.2.4 - PDF parsing](product_documentation/faq_chatbot.md#L198) |
| **IMPL** | [`faq_chatbot/app/main.py:109-152`](../faq_chatbot/app/main.py#L109-L152), [`faq_chatbot/app/rag_engine.py:46-71`](../faq_chatbot/app/rag_engine.py#L46-L71), [`faq_chatbot/app/document_loader.py:11-17`](../faq_chatbot/app/document_loader.py#L11-L17) |
| **Precondition** | Valid session exists. A small valid PDF file is available. |
| **Steps** | 1. Create minimal PDF with known text<br>2. `POST /api/upload` with `multipart/form-data` containing the PDF<br>3. Inspect response<br>4. `POST /api/chat` with a question that the PDF text answers |
| **Expected** | Upload response: `{"message": "Document indexed: <n> sections", "messages": [...], "suggestions": [...]}`. Chat response answers from the PDF content. |
| **Pass Criteria** | Upload returns 200 with `message` containing `"Document indexed"`. Chat response is grounded in the uploaded PDF text. |

---

## TC-FC-API-005: File Upload — Unsupported Extension

| Field | Value |
|---|---|
| **Test ID** | `TC-FC-API-005` |
| **Title** | Upload an unsupported file type returns 400 error |
| **REQ** | [§1 - Document Ingestion](product_documentation/faq_chatbot.md#L28), [§5.5 - File-type whitelist](product_documentation/faq_chatbot.md#L272) |
| **IMPL** | [`faq_chatbot/app/document_loader.py:39-51`](../faq_chatbot/app/document_loader.py#L39-L51), [`faq_chatbot/app/main.py:122-124`](../faq_chatbot/app/main.py#L122-L124) |
| **Precondition** | Valid session exists |
| **Steps** | 1. Create a file with `.exe` extension<br>2. `POST /api/upload` with the file<br>3. Create a file with `.zip` extension<br>4. `POST /api/upload` with the zip |
| **Expected** | Both return HTTP 400 with `{"error": "Unsupported file type: .exe. Supported: .pdf, .docx, ..."}` |
| **Pass Criteria** | Error message lists the unsupported extension and lists supported extensions. |

---

## TC-FC-API-006: File Upload — Exceeds Size Limit

| Field | Value |
|---|---|
| **Test ID** | `TC-FC-API-006` |
| **Title** | Upload a file exceeding 2 MB limit returns error |
| **REQ** | [§1 - Security: 2 MB upload limit](product_documentation/faq_chatbot.md#L40), [§5.5 - Large file uploads](product_documentation/faq_chatbot.md#L271) |
| **IMPL** | [`faq_chatbot/app/main.py:10`](../faq_chatbot/app/main.py#L10), [`129-130`](../faq_chatbot/app/main.py#L129-L130) |
| **Precondition** | Valid session exists |
| **Steps** | 1. Create a file larger than 2 MB<br>2. `POST /api/upload` with the oversized file |
| **Expected** | HTTP 400 or 413 with error indicating the file exceeds the limit |
| **Pass Criteria** | Server rejects files larger than 2 MB and returns a descriptive error. |

---

## TC-FC-API-007: Text Paste

| Field | Value |
|---|---|
| **Test ID** | `TC-FC-API-007` |
| **Title** | Paste text document and verify indexing |
| **REQ** | [§1 - Document Ingestion](product_documentation/faq_chatbot.md#L28), [§2 - Text Paste](product_documentation/faq_chatbot.md#L50) |
| **IMPL** | [`faq_chatbot/app/main.py:155-186`](../faq_chatbot/app/main.py#L155-L186) |
| **Precondition** | Valid session exists |
| **Steps** | 1. `POST /api/paste` with `{"text": "Company policy: Annual leave is 25 days per year."}`<br>2. Inspect response<br>3. `POST /api/chat` with `{"question": "How many annual leave days?"}` |
| **Expected** | Paste response: `{"message": "Text indexed: <n> sections", ...}`. Chat response: answers "25 days" from the pasted text. |
| **Pass Criteria** | Text is indexed successfully. Chat response references the pasted text content. |

---

## TC-FC-API-008: Text Paste — Exceeds Line Limit

| Field | Value |
|---|---|
| **Test ID** | `TC-FC-API-008` |
| **Title** | Paste text exceeding 10,000 lines returns error |
| **REQ** | [§1 - Limits: 10,000 line paste](product_documentation/faq_chatbot.md#L40), [§5.2.5 - Limits](product_documentation/faq_chatbot.md#L207) |
| **IMPL** | [`faq_chatbot/app/main.py:167-169`](../faq_chatbot/app/main.py#L167-L169) |
| **Precondition** | Valid session exists |
| **Steps** | 1. Create a string with 10,001 lines (e.g., "line\n" × 10001)<br>2. `POST /api/paste` with `{"text": "<10,001 lines>"}` |
| **Expected** | HTTP 400 with `{"error": "Text exceeds 10000 line limit (10001 lines)."}` |
| **Pass Criteria** | Server rejects text exceeding line limit with descriptive error. |

---

## TC-FC-API-009: Chat With Document Context

| Field | Value |
|---|---|
| **Test ID** | `TC-FC-API-009` |
| **Title** | Chat returns context-grounded answer from indexed document |
| **REQ** | [§1 - Retrieval-Augmented Generation](product_documentation/faq_chatbot.md#L29), [§1 - Context-Only Answers](product_documentation/faq_chatbot.md#L33) |
| **IMPL** | [`faq_chatbot/app/main.py:189-231`](../faq_chatbot/app/main.py#L189-L231), [`faq_chatbot/app/rag_engine.py:74-88`](../faq_chatbot/app/rag_engine.py#L74-L88) |
| **Precondition** | Valid session exists. Document is loaded via upload or paste. |
| **Steps** | 1. Load a document with specific content (e.g., "The office is closed on December 25th.")<br>2. `POST /api/chat` with `{"question": "Is the office open on Dec 25?"}`<br>3. `POST /api/chat` with `{"question": "What is the meaning of life?"}` (not in document) |
| **Expected** | Step 2: Answer references "closed" or "December 25th" from the document.<br>Step 3: Answer politely states the information is not in the document (e.g., "I'm sorry, I don't have information about that"). |
| **Pass Criteria** | In-document question answered correctly. Out-of-document question politely refused. |

---

## TC-FC-API-010: Session Restart

| Field | Value |
|---|---|
| **Test ID** | `TC-FC-API-010` |
| **Title** | POST `/api/restart` resets session and clears document |
| **REQ** | [§2 - New Chat](product_documentation/faq_chatbot.md#L55), [§5.2.1 - /api/restart](product_documentation/faq_chatbot.md#L181) |
| **IMPL** | [`faq_chatbot/app/main.py:234-245`](../faq_chatbot/app/main.py#L234-L245), [`faq_chatbot/app/session_manager.py:35-37`](../faq_chatbot/app/session_manager.py#L35-L37), [`faq_chatbot/app/rag_engine.py:91-95`](../faq_chatbot/app/rag_engine.py#L91-L95) |
| **Precondition** | Valid session exists. Document has been loaded and chat history exists. |
| **Steps** | 1. Load a document<br>2. Send a chat message<br>3. `POST /api/restart`<br>4. `POST /api/chat` with `{"question": "What was in the document?"}` |
| **Expected** | Step 3: Returns new `session_id` and fresh greeting message. Step 4: Returns "no document loaded" message. Old session's vectors on disk are removed. |
| **Pass Criteria** | After restart, session is fresh with no document and no history. ChromaDB directory for old session is deleted. |

---

## TC-FC-API-011: Follow-Up Suggestions Generated

| Field | Value |
|---|---|
| **Test ID** | `TC-FC-API-011` |
| **Title** | Chat response includes follow-up suggestion buttons after initial exchanges |
| **REQ** | [§2 - Follow-Up Suggestions](product_documentation/faq_chatbot.md#L54) |
| **IMPL** | [`faq_chatbot/app/main.py:58-72`](../faq_chatbot/app/main.py#L58-L72), [`229`](../faq_chatbot/app/main.py#L229) |
| **Precondition** | Valid session exists. Document loaded and some chat history exists. |
| **Steps** | 1. Load a document<br>2. Send several chat messages to build history<br>3. Send another chat message |
| **Expected** | Response includes `"suggestions"` array with up to 5 suggestion strings. Suggestions are relevant to the document context. |
| **Pass Criteria** | `suggestions` field is present and is a non-empty array of strings. |

---

## TC-FC-CHUNK-001: Chunk Size and Overlap

| Field | Value |
|---|---|
| **Test ID** | `TC-FC-CHUNK-001` |
| **Title** | Word-level chunking splits text correctly |
| **REQ** | [§3.4 - Word-Level Chunking](product_documentation/faq_chatbot.md#L77-L80) |
| **IMPL** | [`faq_chatbot/app/rag_engine.py:28-36`](../faq_chatbot/app/rag_engine.py#L28-L36) |
| **Precondition** | None (unit-level test) |
| **Steps** | 1. Call `chunk_text("word " × 1200, 500, 50)`<br>2. Inspect resulting chunks |
| **Expected** | - Chunk 1: words 1-500<br>- Chunk 2: words 451-950 (overlap of 50 words from previous chunk)<br>- Chunk 3: words 901-1200 (last chunk may be shorter)<br>- Total chunks = 3 |
| **Pass Criteria** | Chunk size is ≤ 500 words. Overlap between consecutive chunks is 50 words. All source words appear in at least one chunk. |

---

## TC-FC-CHUNK-002: Single Chunk

| Field | Value |
|---|---|
| **Test ID** | `TC-FC-CHUNK-002` |
| **Title** | Text shorter than chunk size produces one chunk |
| **REQ** | [§3.4 - Word-Level Chunking](product_documentation/faq_chatbot.md#L77-L80) |
| **IMPL** | [`faq_chatbot/app/rag_engine.py:28-36`](../faq_chatbot/app/rag_engine.py#L28-L36) |
| **Precondition** | None |
| **Steps** | 1. Call `chunk_text("hello world", 500, 50)` |
| **Expected** | Returns `["hello world"]` (single chunk) |
| **Pass Criteria** | Text shorter than chunk_size returns exactly one chunk. |

---

## TC-FC-SESS-001: Session Isolation

| Field | Value |
|---|---|
| **Test ID** | `TC-FC-SESS-001` |
| **Title** | Two concurrent sessions do not share state |
| **REQ** | [§3.5 - In-Memory Sessions](product_documentation/faq_chatbot.md#L82-L85) |
| **IMPL** | [`faq_chatbot/app/session_manager.py:4-37`](../faq_chatbot/app/session_manager.py#L4-L37) |
| **Precondition** | Server running |
| **Steps** | 1. Create Session A via `POST /api/start` (obtain cookie A)<br>2. Create Session B via `POST /api/start` (obtain cookie B)<br>3. Session A loads a document "Policy: Standard leave is 20 days."<br>4. Session B loads a document "Policy: Standard leave is 30 days."<br>5. Ask both sessions "How many leave days?" |
| **Expected** | Session A answers "20 days". Session B answers "30 days". Each session uses its own document context. |
| **Pass Criteria** | Responses differ and match each session's loaded document. |

---

## TC-FC-LOADER-001: Supported File Formats

| Field | Value |
|---|---|
| **Test ID** | `TC-FC-LOADER-001` |
| **Title** | All 11 supported file formats load correctly |
| **REQ** | [§1 - Document Ingestion](product_documentation/faq_chatbot.md#L28), [§5.2.4 - Extension-to-loader mapping](product_documentation/faq_chatbot.md#L198) |
| **IMPL** | [`faq_chatbot/app/document_loader.py:39-65`](../faq_chatbot/app/document_loader.py#L39-L65) |
| **Precondition** | Test fixtures for each format exist |
| **Steps** | 1. For each extension in `.txt, .md, .csv, .json, .xml, .html, .pdf, .docx, .doc, .pptx, .ppt`:<br>2. Create a small valid file<br>3. Call `load_document(tmp_path)`<br>4. Verify text is extracted |
| **Expected** | Each format returns a non-empty string with normalized whitespace. PDF preserves text. DOCX and PPTX extract text from paragraphs/slides. |
| **Pass Criteria** | All 11 formats are listed in `LOADERS` dict. Each format returns text without raising. |

---

## TC-FC-LOADER-002: Unsupported Extension Raises Error

| Field | Value |
|---|---|
| **Test ID** | `TC-FC-LOADER-002` |
| **Title** | Unsupported file extension raises ValueError |
| **REQ** | [§5.2.4 - Unsupported extensions](product_documentation/faq_chatbot.md#L200) |
| **IMPL** | [`faq_chatbot/app/document_loader.py:54-58`](../faq_chatbot/app/document_loader.py#L54-L58) |
| **Precondition** | None |
| **Steps** | 1. Call `load_document("test.xyz")` with an unsupported extension |
| **Expected** | Raises `ValueError("Unsupported file type: .xyz")` |
| **Pass Criteria** | ValueError is raised with the unsupported extension in the message. |

---

## TC-FC-UI-001: Page Renders Successfully

| Field | Value |
|---|---|
| **Test ID** | `TC-FC-UI-001` |
| **Title** | GET `/` returns HTML page with all required UI elements |
| **REQ** | [§2 - Chat Interface](product_documentation/faq_chatbot.md#L52-L56) |
| **IMPL** | [`faq_chatbot/app/templates/index.html`](../faq_chatbot/app/templates/index.html) |
| **Precondition** | Server running |
| **Steps** | 1. Send `GET /` (through proxy with Basic Auth if applicable)<br>2. Inspect response |
| **Expected** | HTTP 200. HTML contains: header with "FAQ Chatbot" text, input bar, send button, mode buttons (Upload, Paste), chat area, status bar. |
| **Pass Criteria** | HTML is valid. All UI sections present. |

---

## TC-FC-UI-002: Theme Toggle

| Field | Value |
|---|---|
| **Test ID** | `TC-FC-UI-002` |
| **Title** | Theme toggle switches between light and dark mode |
| **REQ** | [§2 - Responsive UI](product_documentation/faq_chatbot.md#L56) |
| **IMPL** | [`faq_chatbot/app/templates/index.html:557-563`](../faq_chatbot/app/templates/index.html#L557-L563) |
| **Precondition** | Page loaded in browser |
| **Steps** | 1. Click theme toggle button<br>2. Verify `data-theme` attribute on `<html>`<br>3. Refresh page |
| **Expected** | Theme toggles between light and dark. Setting persists across page refresh via `localStorage`. |
| **Pass Criteria** | `data-theme` attribute changes. `localStorage.getItem('theme')` matches. |

---

## TC-FC-SEC-001: No XSS in Message Rendering

| Field | Value |
|---|---|
| **Test ID** | `TC-FC-SEC-001` |
| **Title** | User messages with HTML are rendered as text, not executed |
| **REQ** | [§5.5 - XSS via pasted text](product_documentation/faq_chatbot.md#L274) |
| **IMPL** | [`faq_chatbot/app/templates/index.html:343-345`](../faq_chatbot/app/templates/index.html#L343-L345) |
| **Precondition** | Valid session exists |
| **Steps** | 1. `POST /api/chat` with `{"question": "<script>alert('xss')</script>"}` |
| **Expected** | Response text is rendered as plain text in the UI. The `<script>` tag is not executed. |
| **Pass Criteria** | HTML tags in user question are displayed as literal text, not interpreted. |

---

## TC-FC-SEC-002: Temp File Cleanup

| Field | Value |
|---|---|
| **Test ID** | `TC-FC-SEC-002` |
| **Title** | Uploaded temp files are removed after processing |
| **REQ** | [§5.5 - Temp file leakage](product_documentation/faq_chatbot.md#L273) |
| **IMPL** | [`faq_chatbot/app/main.py:150-152`](../faq_chatbot/app/main.py#L150-L152) |
| **Precondition** | Valid session exists |
| **Steps** | 1. Upload a file<br>2. Check `/tmp/` directory on the container for any `.hex` prefixed temp files |
| **Expected** | The temp file created during upload is removed after the `finally` block executes. |
| **Pass Criteria** | No orphaned temp files remain in `/tmp/` after upload completes. |

---

## TC-FC-DEPLOY-001: Container Health Check

| Field | Value |
|---|---|
| **Test ID** | `TC-FC-DEPLOY-001` |
| **Title** | Docker container starts and serves on expected port |
| **REQ** | [§1 - Deployment](product_documentation/faq_chatbot.md#L36) |
| **IMPL** | [`faq_chatbot/Dockerfile`](../faq_chatbot/Dockerfile), [`faq_chatbot/docker-compose.yml`](../faq_chatbot/docker-compose.yml) |
| **Precondition** | Docker and docker-compose installed |
| **Steps** | 1. `docker compose up -d` from `faq_chatbot/`<br>2. `docker compose ps`<br>3. `curl -s -o /dev/null -w "%{http_code}" http://localhost:5050/` |
| **Expected** | Container state is "Up". HTTP request returns 200. |
| **Pass Criteria** | Container is running and port 5050 responds. |

---

## TC-FC-DEPLOY-002: Ollama Connectivity

| Field | Value |
|---|---|
| **Test ID** | `TC-FC-DEPLOY-002` |
| **Title** | Container can reach Ollama on host |
| **REQ** | [§3.3 - Ollama (Local LLM)](product_documentation/faq_chatbot.md#L72-L75) |
| **IMPL** | [`faq_chatbot/config.yaml`](../faq_chatbot/config.yaml#L2) |
| **Precondition** | Both containers running, Ollama running on host |
| **Steps** | 1. `docker exec faq_chatbot curl -s http://host.docker.internal:11434/api/tags` |
| **Expected** | Returns JSON with available models. `llama3.2:3b` and `nomic-embed-text` models are present. |
| **Pass Criteria** | Ollama API responds with model list containing required models. |

---

## Regression Test Summary: FAQ Chatbot

| Area | Test Count |
|---|---|
| API Endpoint Tests | 11 |
| Chunking Logic Tests | 2 |
| Session Management Tests | 1 |
| Document Loader Tests | 2 |
| UI Tests | 2 |
| Security Tests | 2 |
| Deployment Tests | 2 |
| **Total** | **22** |
