# Regression Tests: Cross-Project Integration

> **Scope**: End-to-end flows spanning multiple projects (FAQ Chatbot, Bench LLM, Blooms.ai)
> **Documentation**: `product_documentation/faq_chatbot.md`, `product_documentation/bench_llm.md`
> **Stakeholder**: System-level health verification

---

## Test Tag Convention

Each test case is tagged with:
- **REQ** — Link to requirement in relevant product documentation
- **IMPL** — Link to implementation across projects
- **TC** — Test case identifier

---

## TC-INT-GATEWAY-001: Full Proxy Chain (Browser → nginx → Node.js → Docker)

| Field | Value |
|---|---|
| **Test ID** | `TC-INT-GATEWAY-001` |
| **Title** | FAQ Chatbot is reachable through the full proxy chain |
| **REQ** | [faq_chatbot: §5.3 - Deployment Architecture](../product_documentation/faq_chatbot.md#L209-L249), [faq_chatbot: §3.7 - Proxy Architecture](../product_documentation/faq_chatbot.md#L92-L95) |
| **IMPL** | [`blooms.ai/server.js:80-102`](../blooms.ai/server.js#L80-L102) (proxy), [`faq_chatbot/app/main.py`](../faq_chatbot/app/main.py) (Flask app) |
| **Precondition** | nginx running, Node.js running, FAQ Chatbot Docker container running |
| **Steps** | 1. Send `GET /blooms/demo/faq_chatbot/` through nginx (port 80)<br>2. Inspect response |
| **Expected** | HTTP 200. FAQ Chatbot UI is rendered correctly. This verifies: nginx → Node.js → Docker proxy chain. |
| **Pass Criteria** | Response body is the FAQ Chatbot HTML template. No 502, 404, or auth errors. |

---

## TC-INT-GATEWAY-002: Full Proxy Chain — Bench LLM

| Field | Value |
|---|---|
| **Test ID** | `TC-INT-GATEWAY-002` |
| **Title** | Bench LLM is reachable through the full proxy chain |
| **REQ** | [faq_chatbot: §5.3 - Deployment Architecture](../product_documentation/faq_chatbot.md#L209-L249) |
| **IMPL** | [`blooms.ai/server.js:80-102`](../blooms.ai/server.js#L80-L102) (proxy), [`bench_llm/app/main.py`](../bench_llm/app/main.py) (Flask app) |
| **Precondition** | nginx running, Node.js running, Bench LLM Docker container running |
| **Steps** | 1. Send `GET /blooms/demo/Model_Benchmark/` through nginx (port 80) with valid auth<br>2. Inspect response |
| **Expected** | HTTP 200. Bench LLM dashboard is rendered correctly. |
| **Pass Criteria** | Response body contains Bench LLM UI elements (Run Benchmark button, etc.). |

---

## TC-INT-AUTH-001: Basic Auth Enforces Across Demo

| Field | Value |
|---|---|
| **Test ID** | `TC-INT-AUTH-001` |
| **Title** | All demo paths require valid HTTP Basic Auth |
| **REQ** | [faq_chatbot: §1 - Authentication](../product_documentation/faq_chatbot.md#L37) |
| **IMPL** | [`blooms.ai/server.js:68-78`](../blooms.ai/server.js#L68-L78), [`blooms.ai/democonfig.json`](../blooms.ai/democonfig.json) |
| **Precondition** | Node.js server running |
| **Steps** | 1. Send `GET /demo/` without auth<br>2. Send `GET /demo/faq_chatbot/` without auth<br>3. Send `GET /demo/Model_Benchmark/` without auth |
| **Expected** | All return HTTP 401 with `WWW-Authenticate: Basic realm="Demo Apps"` header. |
| **Pass Criteria** | All demo paths are protected by Basic Auth. |

---

## TC-INT-OLLAMA-001: Shared Ollama Instance

| Field | Value |
|---|---|
| **Test ID** | `TC-INT-OLLAMA-001` |
| **Title** | FAQ Chatbot and Bench LLM both reach the same Ollama instance |
| **REQ** | [faq_chatbot: §3.3 - Ollama](../product_documentation/faq_chatbot.md#L72-L75), [bench_llm: §3.7 - Host-Networked Ollama Access](../product_documentation/bench_llm.md#L78-L81) |
| **IMPL** | [`faq_chatbot/config.yaml`](../faq_chatbot/config.yaml#L2), [`bench_llm/config.yaml`](../bench_llm/config.yaml#L2) |
| **Precondition** | Ollama running on host. Both containers running. |
| **Steps** | 1. Get Ollama model list (host)<br>2. From FAQ Chatbot container, verify `host.docker.internal:11434` is reachable<br>3. From Bench LLM container, verify `host.docker.internal:11434` is reachable |
| **Expected** | Both containers can reach Ollama at the same host. Model list includes `llama3.2:3b`, `nomic-embed-text`, and `gemma4:12b` (or configured models). |
| **Pass Criteria** | Both containers have connectivity to Ollama. Required models exist for both apps. |

---

## TC-INT-BENCHMARK-001: Bench LLM Can Benchmark FAQ Chatbot Model

| Field | Value |
|---|---|
| **Test ID** | `TC-INT-BENCHMARK-001` |
| **Title** | Bench LLM runs benchmark including the model used by FAQ Chatbot |
| **REQ** | [bench_llm: §1 - Multi-Model Benchmarking](../product_documentation/bench_llm.md#L14) |
| **IMPL** | [`bench_llm/config.yaml`](../bench_llm/config.yaml) (includes `faq_chatbot` app profile), [`bench_llm/app/benchmark_agent.py`](../bench_llm/app/benchmark_agent.py) |
| **Precondition** | Ollama running with `llama3.2:3b` (FAQ Chatbot model). Bench LLM running. |
| **Steps** | 1. Run a benchmark on Bench LLM that tests `llama3.2:3b`<br>2. Inspect results |
| **Expected** | `llama3.2:3b` appears in the results. `app_suggestions` includes a recommendation for `faq_chatbot` app. Metric scores are present for all 5 categories. |
| **Pass Criteria** | FAQ Chatbot's model is benchmarked. App recommendations include the `faq_chatbot` profile with weighted scores. |

---

## TC-INT-DATAFLOW-001: FAQ Chatbot RAG Pipeline End-to-End

| Field | Value |
|---|---|
| **Test ID** | `TC-INT-DATAFLOW-001` |
| **Title** | End-to-end document upload → index → query → response |
| **REQ** | [faq_chatbot: §4 - Request Flow](../product_documentation/faq_chatbot.md#L132-L144) |
| **IMPL** | [`faq_chatbot/app/document_loader.py`](../faq_chatbot/app/document_loader.py) → [`faq_chatbot/app/rag_engine.py`](../faq_chatbot/app/rag_engine.py) → [`faq_chatbot/app/main.py`](../faq_chatbot/app/main.py) |
| **Precondition** | FAQ Chatbot container running. Ollama accessible. |
| **Steps** | 1. `POST /api/start` → get session<br>2. Upload a test document (PDF with known content) via `POST /api/upload`<br>3. `POST /api/chat` with `{"question": "<question answerable from doc>"}`<br>4. Verify response |
| **Expected** | - Upload: `"Document indexed: <n> sections"`<br>- Chat: Response is grounded in the document content<br>- Response time within 120s timeout |
| **Pass Criteria** | Full RAG pipeline succeeds: document loaded → chunked → embedded → stored → queried → context retrieved → LLM generates answer. Answer is relevant and based on document. |

---

## TC-INT-DATAFLOW-002: Ollama Embedding + Generation Pipeline

| Field | Value |
|---|---|
| **Test ID** | `TC-INT-DATAFLOW-002` |
| **Title** | Ollama embedding and generation calls work correctly |
| **REQ** | [faq_chatbot: §3.3 - Ollama](../product_documentation/faq_chatbot.md#L72-L75), [bench_llm: §3.2 - LangChain ChatOllama](../product_documentation/bench_llm.md#L53-L56) |
| **IMPL** | [`faq_chatbot/app/rag_engine.py:16-25`](../faq_chatbot/app/rag_engine.py#L16-L25) (embeddings), [`faq_chatbot/app/main.py:42-55`](../faq_chatbot/app/main.py#L42-L55) (generation) |
| **Precondition** | Ollama running on host |
| **Steps** | 1. Call Ollama `/api/embed` with `nomic-embed-text` model and a test string<br>2. Call Ollama `/api/generate` with `llama3.2:3b` and a test prompt |
| **Expected** | Embedding returns a vector (array of floats). Generate returns a text response. Both within 120s timeout. |
| **Pass Criteria** | Both Ollama endpoints respond successfully with correct response types. |

---

## TC-INT-ENDPOINT-001: All Demo Apps Respond (Health Check)

| Field | Value |
|---|---|
| **Test ID** | `TC-INT-ENDPOINT-001` |
| **Title** | All configured demo apps return HTTP 200 |
| **REQ** | [faq_chatbot: §5.4 - API Reference](../product_documentation/faq_chatbot.md#L252-L261), [bench_llm: §5.4 - API Reference](../product_documentation/bench_llm.md#L231-L239) |
| **IMPL** | Cross-project health check |
| **Precondition** | All Docker containers running |
| **Steps** | 1. Check `http://localhost:5050/` (FAQ Chatbot health)<br>2. Check `http://localhost:5052/` (Bench LLM health)<br>3. Check `http://localhost:3369/` (Blooms.ai health) |
| **Expected** | All return HTTP 200 with appropriate HTML response. |
| **Pass Criteria** | All three services respond with 200. |

---

## Regression Test Summary: Integration

| Area | Test Count |
|---|---|
| Proxy Chain Tests | 2 |
| Auth Tests | 1 |
| Ollama Connectivity Tests | 1 |
| Cross-App Benchmark Tests | 1 |
| End-to-End Data Flow Tests | 2 |
| Health Check Tests | 1 |
| **Total** | **8** |
