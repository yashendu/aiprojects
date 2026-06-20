# Regression Tests: i_extract

> **Product**: Local LLM Document Data Extraction
> **Documentation**: `product_documentation/i_extract.md`
> **Source**: `i_extract/`

---

## TC-IE-API-001: Page Renders

| Field | Value |
|---|---|
| **Test ID** | `TC-IE-API-001` |
| **Title** | GET `/` returns extraction UI |
| **REQ** | [§1 - Split-View Display](product_documentation/i_extract.md) |
| **IMPL** | [`i_extract/app/main.py`](../i_extract/app/main.py), [`i_extract/app/templates/index.html`](../i_extract/app/templates/index.html) |
| **Precondition** | Docker container running |
| **Steps** | 1. Send `GET /` |
| **Expected** | HTTP 200. HTML contains: upload bar with file input, document pane, extraction pane with table, CSV download button. |
| **Pass Criteria** | All UI sections present. |

---

## TC-IE-API-002: Upload PDF — Successful Extraction

| Field | Value |
|---|---|
| **Test ID** | `TC-IE-API-002` |
| **Title** | Upload a PDF with labeled data and verify extraction |
| **REQ** | [§1 - Key-Value Extraction](product_documentation/i_extract.md) |
| **IMPL** | [`i_extract/app/main.py`](../i_extract/app/main.py), [`i_extract/app/extractor.py`](../i_extract/app/extractor.py) |
| **Precondition** | Container running, Ollama reachable |
| **Steps** | 1. Create a PDF with text like "Name: John Doe, Age: 30, Amount: $500"<br>2. `POST /api/upload` with the PDF |
| **Expected** | Response `extracted` array contains objects with `label` and `value` fields. `document_html` contains the rendered PDF text. |
| **Pass Criteria** | At least one key-value pair extracted. Response includes `document_html` and `message`. |

---

## TC-IE-API-003: Upload JPEG — Successful Extraction

| Field | Value |
|---|---|
| **Test ID** | `TC-IE-API-003` |
| **Title** | Upload a JPEG image with visible text |
| **REQ** | [§1 - JPEG Upload](product_documentation/i_extract.md) |
| **IMPL** | [`i_extract/app/main.py`](../i_extract/app/main.py), [`i_extract/app/extractor.py`](../i_extract/app/extractor.py) |
| **Precondition** | Vision-capable model (qwen3.5:4b) available in Ollama |
| **Steps** | 1. Create a JPEG with text containing key-value pairs<br>2. `POST /api/upload` with the JPEG |
| **Expected** | Response `extracted` array contains extracted pairs. |
| **Pass Criteria** | Key-value pairs extracted from the image. |

---

## TC-IE-API-004: Upload — Unsupported Extension

| Field | Value |
|---|---|
| **Test ID** | `TC-IE-API-004` |
| **Title** | Upload unsupported file type returns 400 |
| **REQ** | [§1 - File Upload](product_documentation/i_extract.md) |
| **IMPL** | [`i_extract/app/main.py`](../i_extract/app/main.py) |
| **Precondition** | Container running |
| **Steps** | 1. `POST /api/upload` with a `.png` file |
| **Expected** | HTTP 400 with `{"error": "Unsupported file type: .png. Supported: .pdf, .jpeg, .jpg"}` |
| **Pass Criteria** | Error message lists supported extensions. |

---

## TC-IE-API-005: Upload — Exceeds Size Limit

| Field | Value |
|---|---|
| **Test ID** | `TC-IE-API-005` |
| **Title** | Upload file exceeding 2 MB returns error |
| **REQ** | [§1 - File Upload](product_documentation/i_extract.md) |
| **IMPL** | [`i_extract/app/main.py`](../i_extract/app/main.py) |
| **Precondition** | Container running |
| **Steps** | 1. Create a file > 2 MB<br>2. `POST /api/upload` with it |
| **Expected** | HTTP 400 with error about exceeding limit |
| **Pass Criteria** | Server rejects oversized files. |

---

## TC-IE-API-006: Upload — No File Provided

| Field | Value |
|---|---|
| **Test ID** | `TC-IE-API-006` |
| **Title** | POST without file returns 400 |
| **REQ** | [§5.4 - API Reference](product_documentation/i_extract.md) |
| **IMPL** | [`i_extract/app/main.py`](../i_extract/app/main.py) |
| **Precondition** | Container running |
| **Steps** | 1. `POST /api/upload` with empty body |
| **Expected** | HTTP 400 with `{"error": "No file provided"}` |
| **Pass Criteria** | Error message returned. |

---

## TC-IE-API-007: Export CSV

| Field | Value |
|---|---|
| **Test ID** | `TC-IE-API-007` |
| **Title** | POST `/api/export_csv` returns valid CSV |
| **REQ** | [§1 - CSV Export](product_documentation/i_extract.md) |
| **IMPL** | [`i_extract/app/main.py`](../i_extract/app/main.py) |
| **Precondition** | Container running |
| **Steps** | 1. `POST /api/export_csv` with `{"rows": [{"label": "Name", "value": "John"}, {"label": "Age", "value": "30"}]}` |
| **Expected** | HTTP 200. `Content-Type: text/csv`. Body is CSV with headers `Serial No.,Label,Value` and 2 data rows. |
| **Pass Criteria** | CSV is valid, has headers, has correct data. |

---

## TC-IE-API-008: Learning Stats

| Field | Value |
|---|---|
| **Test ID** | `TC-IE-API-008` |
| **Title** | GET `/api/learning/stats` returns sample count |
| **REQ** | [§5.2.4 - Learning Store](product_documentation/i_extract.md) |
| **IMPL** | [`i_extract/app/learning_store.py`](../i_extract/app/learning_store.py) |
| **Precondition** | Container running, at least one extraction performed |
| **Steps** | 1. Send `GET /api/learning/stats` |
| **Expected** | `{"sample_count": N}` where N > 0 after an extraction. |
| **Pass Criteria** | Response includes integer `sample_count`. |

---

## TC-IE-API-009: Gibberish Handling

| Field | Value |
|---|---|
| **Test ID** | `TC-IE-API-009` |
| **Title** | Non-extractable text returns descriptive message |
| **REQ** | [§1 - Gibberish/Non-Extractable](product_documentation/i_extract.md) |
| **IMPL** | [`i_extract/app/extractor.py`](../i_extract/app/extractor.py) |
| **Precondition** | Container running, Ollama reachable |
| **Steps** | 1. Upload a PDF with purely narrative text (no labeled data)<br>2. Inspect response |
| **Expected** | `extracted` is empty array. `message` describes why no pairs were found. |
| **Pass Criteria** | User gets a clear explanation instead of an empty table. |

---

## TC-IE-LEARN-001: Sample Saved After Extraction

| Field | Value |
|---|---|
| **Test ID** | `TC-IE-LEARN-001` |
| **Title** | Successful extraction creates a learning sample |
| **REQ** | [§3.3 - Few-Shot Learning Loop](product_documentation/i_extract.md) |
| **IMPL** | [`i_extract/app/learning_store.py`](../i_extract/app/learning_store.py) |
| **Precondition** | Container running |
| **Steps** | 1. Upload a document with extractable data<br>2. Check `/api/learning/stats`<br>3. Check `knowledge/samples/` directory for new JSON files |
| **Expected** | Sample count increments by 1. New file appears in `knowledge/samples/`. |
| **Pass Criteria** | Learning store persists the extraction. |

---

## TC-IE-LEARN-002: Similar Samples Retrieved

| Field | Value |
|---|---|
| **Test ID** | `TC-IE-LEARN-002` |
| **Title** | Similar past extractions are used as few-shot examples |
| **REQ** | [§3.3 - Few-Shot Learning Loop](product_documentation/i_extract.md) |
| **IMPL** | [`i_extract/app/learning_store.py`](../i_extract/app/learning_store.py) |
| **Precondition** | At least 2 extractions performed |
| **Steps** | 1. Call `get_similar_samples(text)` programmatically<br>2. Inspect returned samples |
| **Expected** | Returns up to `similarity_top_k` samples with word overlap > 0. |
| **Pass Criteria** | Similar samples are returned. |

---

## TC-IE-UI-001: Theme Toggle

| Field | Value |
|---|---|
| **Test ID** | `TC-IE-UI-001` |
| **Title** | Theme toggle switches light/dark mode |
| **REQ** | [§2 - Dark/Light Theme](product_documentation/i_extract.md) |
| **IMPL** | [`i_extract/app/templates/index.html`](../i_extract/app/templates/index.html) |
| **Precondition** | Page loaded in browser |
| **Steps** | 1. Click theme toggle<br>2. Verify `data-theme` attribute |
| **Expected** | Theme toggles and persists via localStorage. |
| **Pass Criteria** | Theme toggle works and persists. |

---

## TC-IE-DEPLOY-001: Container Health

| Field | Value |
|---|---|
| **Test ID** | `TC-IE-DEPLOY-001` |
| **Title** | Docker container starts and serves on expected port |
| **REQ** | [§1 - Deployment](product_documentation/i_extract.md) |
| **IMPL** | [`i_extract/Dockerfile`](../i_extract/Dockerfile), [`i_extract/docker-compose.yml`](../i_extract/docker-compose.yml) |
| **Precondition** | Docker and docker-compose installed |
| **Steps** | 1. `docker compose up -d`<br>2. `curl -s -o /dev/null -w "%{http_code}" http://localhost:5053/` |
| **Expected** | Container is "Up". HTTP 200. |
| **Pass Criteria** | Container running and port 5053 responds. |

---

## Regression Test Summary: i_extract

| Area | Test Count |
|---|---|
| API Endpoint Tests | 9 |
| Learning Store Tests | 2 |
| UI Tests | 1 |
| Deployment Tests | 1 |
| **Total** | **13** |
