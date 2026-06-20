# i_extract — Local LLM Document Data Extraction

**Extract Structured Data from Documents with Zero Cloud Exposure**

Upload PDFs or JPEG images and extract structured key-value pairs (names, dates, amounts, IDs, etc.) using a local LLM — completely offline. Every extraction is logged into a learning store that improves future results through few-shot retrieval.

---

## 1. Requirements

### Functional Requirements
- **File Upload**: Accept PDF and JPEG files up to 2 MB for data extraction.
- **Key-Value Extraction**: Identify labeled data fields from document text (e.g., Name, Age, Amount, Date) and present them in a structured table.
- **Split-View Display**: Show the original document on the left and extracted fields in an editable table on the right.
- **Row-to-Document Highlighting**: Clicking an extracted row highlights the corresponding text in the document pane.
- **Editable Fields**: Both labels and values are editable inline so users can correct extraction errors.
- **CSV Export**: Download extracted data as a CSV file with columns Serial No., Label, Value.
- **Gibberish/Non-Extractable Handling**: Display a clear message when no key-value pairs can be found (gibberish, narrative-only, blank image).
- **Learning Loop**: Successful extractions are stored and used as few-shot examples to improve future extraction accuracy.

### Non-Functional Requirements
- **Deployment**: Containerized via Docker, served by Gunicorn on port 5053.
- **Privacy**: All processing via local Ollama — no data leaves the host.
- **Latency**: LLM extraction calls with 120s timeout; 300s gunicorn timeout for large documents.
- **Security**: 2 MB upload limit, temp file cleanup after processing, file-type whitelist.

---

## 2. Product Features

| Feature | Description |
|---|---|
| **PDF Upload** | Extract text from PDF documents using PyMuPDF. |
| **JPEG Upload** | Extract text from images using a vision-capable LLM (qwen3.5:4b). |
| **Key-Value Extraction** | LLM identifies labeled fields and returns them as structured JSON. |
| **Split-View UI** | Document on left, extraction table on right in a side-by-side layout. |
| **Row Highlighting** | Click a row to highlight its value text in the document viewer. |
| **Inline Editing** | Edit any label or value directly in the table cells. |
| **Add/Delete Rows** | Manually add or remove extracted fields. |
| **CSV Download** | One-click export of all extracted fields to CSV. |
| **Gibberish Detection** | LLM pre-checks if text contains extractable data; shows explanation when none found. |
| **Learning Loop** | Extractions stored as reference samples; similar past extractions used as few-shot examples. |
| **Dark/Light Theme** | Theme toggle persisted via localStorage. |

---

## 3. Design Choices

### 3.1 LLM-Based Extraction over Regex
- **Choice**: Use an LLM to identify and extract key-value pairs instead of hand-crafted regex patterns.
- **Rationale**: Documents vary wildly in structure. Regex is brittle for real-world documents. An LLM can understand context, adapt to different formats, and handle variations in labeling.
- **Trade-off**: Slower than regex (2-10s per extraction), depends on LLM quality, requires Ollama availability.

### 3.2 Two-Phase Analysis (Check + Extract)
- **Choice**: First check if text is extractable, then extract pairs.
- **Rationale**: Avoids wasting LLM time and user confusion on documents with no structured data. The gibberish check provides a clear explanation.
- **Trade-off**: Two LLM calls instead of one; doubles latency for non-extractable content.

### 3.3 Few-Shot Learning Loop
- **Choice**: Store successful extractions and retrieve similar past ones as few-shot examples.
- **Rationale**: Over time, the system improves at extracting the kinds of documents the user typically uploads. Similarity is based on word overlap.
- **Trade-off**: Only as good as stored samples; word-overlap similarity is primitive. Storage grows with usage (capped at 100 samples).

### 3.4 Vision Model for JPEG
- **Choice**: Use `qwen3.5:4b` (vision-capable) to extract text from uploaded images via Ollama's image input.
- **Rationale**: Eliminates need for a separate OCR engine. The vision model reads text directly from the image.
- **Trade-off**: Slower than dedicated OCR (Tesseract). Requires a vision-capable model. Image quality affects accuracy.

### 3.5 Split-View UI
- **Choice**: Side-by-side document (left) and extraction table (right) with row-to-document highlighting.
- **Rationale**: Users need to verify extracted data against the source. The split view enables quick visual validation.
- **Trade-off**: Requires horizontal space; collapses to stacked layout on narrow screens (<900px).

### 3.6 Inline Editable Table
- **Choice**: Editable input fields directly in the table cells rather than a separate edit mode.
- **Rationale**: Reduces friction for corrections. Users can fix extraction errors immediately without switching contexts.
- **Trade-off**: Harder to implement undo; accidental edits are immediate.

### 3.7 JSON Output Format
- **Choice**: LLM returns extraction as a JSON array of `{"label", "value"}` objects.
- **Rationale**: Structured, parseable, easy to validate and display. Enables strict error handling for malformed responses.
- **Trade-off**: Requires strict prompt engineering; some models may produce invalid JSON (fallback regex parsing included).

---

## 4. High-Level Design

```
┌─────────────────────────────────────────────────────────┐
│                   Docker Container                       │
│  ┌─────────────────────────────────────────────────────┐│
│  │               Gunicorn (1 worker, 300s timeout)     ││
│  │               port 5000                              ││
│  │  ┌─────────────────────────────────────────────────┐ ││
│  │  │           Flask Application                      │ ││
│  │  │                                                  │ ││
│  │  │  ┌──────────────┐  ┌──────────────────┐        │ ││
│  │  │  │ main.py      │  │ document_        │        │ ││
│  │  │  │ (routes)     │  │ processor.py     │        │ ││
│  │  │  └──────┬───────┘  │ (PDF/JPEG parse) │        │ ││
│  │  │         │          └──────────────────┘        │ ││
│  │  │  ┌──────▼───────┐  ┌──────────────────┐        │ ││
│  │  │  │ extractor.py │  │ learning_store   │        │ ││
│  │  │  │ (LLM calls)  │──│ .py              │        │ ││
│  │  │  └──────────────┘  │ (RAG storage)    │        │ ││
│  │  │                    └──────────────────┘        │ ││
│  │  │  ┌──────────────────────────────────────┐      │ ││
│  │  │  │ templates/index.html (Jinja2 UI)     │      │ ││
│  │  │  └──────────────────────────────────────┘      │ ││
│  │  └─────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────┘│
│                                                          │
│  Volumes:                                                │
│    config.yaml  ──>  /app/config.yaml                    │
│    prompts.yaml ──>  /app/prompts.yaml                   │
│    knowledge/   ──>  /app/knowledge/                     │
│                                                          │
│  Communicates with:                                      │
│    host.docker.internal:11434  (Ollama on host)          │
└─────────────────────────────────────────────────────────┘
```

### Request Flow (Extraction)
1. User uploads PDF/JPEG → browser sends `POST /api/upload` with multipart form data
2. Flask validates extension (`.pdf` or `.jpg`/`.jpeg`) and size (≤2 MB)
3. File saved to temp → parsed:
   - **PDF**: PyMuPDF extracts text page-by-page
   - **JPEG**: Vision LLM (`qwen3.5:4b`) extracts text from image
4. Text normalized → gibberish check via LLM (`check_extractable`)
5. If extractable: retrieve similar past extractions from LearningStore → build few-shot prompt
6. LLM extracts key-value pairs → returns JSON array
7. Result saved to LearningStore for future improvement
8. Temp file cleaned up → JSON response returned to browser
9. Frontend renders split view: document HTML left, editable table right

---

## 5. Product Architecture

### 5.1 Directory Structure

```
i_extract/
├── app/
│   ├── __init__.py              # Package marker (empty)
│   ├── main.py                  # Flask app: routes, upload handling, orchestration
│   ├── document_processor.py    # PDF/JPEG parsing, HTML rendering, text normalization
│   ├── extractor.py             # LLM calls: gibberish check, key-value extraction, image analysis
│   ├── learning_store.py        # Few-shot sample storage, similarity retrieval, pruning
│   └── templates/
│       └── index.html           # Single-page frontend (vanilla JS + CSS)
├── config.yaml                  # Ollama, generation, limits, learning config
├── prompts.yaml                 # Prompt catalog with version history and change trail
├── Dockerfile                   # Python 3.11-slim, gunicorn entrypoint
├── docker-compose.yml           # Service definition, port mapping, volume mounts
├── requirements.txt             # Python dependencies
└── knowledge/
    └── samples/                 # Stored extraction samples for few-shot learning
```

### 5.2 Component Breakdown

#### 5.2.1 `app/main.py` — Flask Application
- **Routes**:
  - `GET /` — Renders the extraction UI.
  - `POST /api/upload` — Accepts file upload, validates extension/size, triggers extraction pipeline, returns document HTML + extracted pairs.
  - `POST /api/export_csv` — Accepts JSON array of rows, returns CSV file download.
  - `GET /api/learning/stats` — Returns count of stored learning samples.
  - `GET /api/prompts` — Returns the full prompt catalog.
- **Key Design**: Upload handler follows try/finally temp file cleanup. LearningStore is initialized from config at import time.

#### 5.2.2 `app/document_processor.py` — Document Parsing
- **`load_pdf(filepath)`**: Uses PyMuPDF to extract text per page. Returns list of `{page, text, width, height}`.
- **`load_image(filepath)`**: Uses Pillow to read image dimensions. Text extraction is handled by the vision LLM in the extractor.
- **`render_document_html(pages)`**: Converts parsed pages to HTML with `<span class="doc-line">` elements for row highlighting. Images are base64-encoded inline.
- **`normalize_text(text)`**: Collapses whitespace.

#### 5.2.3 `app/extractor.py` — LLM Integration
- **`load_prompts()`**: Reads `prompts.yaml` which catalogs all prompt templates with versioning.
- **`call_ollama(host, model, system, prompt, ...)`**: Generic Ollama `/api/generate` wrapper with timeout and image support.
- **`check_extractable(host, model, text, config)`**: Sends text to LLM to determine if it contains structured key-value data. Returns `(is_extractable, reason)`.
- **`extract_pairs(host, model, text, config, similar_samples)`**: Builds few-shot prompt from past extractions, calls LLM, parses JSON response, validates result.
- **`extract_text_from_image(host, model, image_path, config)`**: Sends image to vision LLM for OCR. Returns extracted text.
- **`_parse_json(text)`**: Attempts JSON parse with regex fallback for malformed responses.

#### 5.2.4 `app/learning_store.py` — Few-Shot Learning Store
- **`save_sample(filename, text, pairs, model)`**: Stores extraction as JSON in `knowledge/samples/`. Caps at `max_samples` (100), keeping highest-pair-count samples.
- **`get_similar_samples(text, top_k)`**: Returns top-K past samples by word-overlap similarity for few-shot prompting.
- **`_trim()`**: Prunes excess samples keeping the most useful ones (most pairs extracted).
- **`count()`**: Returns total stored samples.

#### 5.2.5 `config.yaml` — Configuration
- **Ollama**: host URL, generation model, vision model, embedding model.
- **Generation**: temperature 0.1, top_p 0.9, max_tokens 4096.
- **Limits**: 2 MB upload, supported extensions.
- **Learning**: max 100 samples, top-3 similar for few-shot.
- **Extraction**: min_confidence 0.3, max_pairs 50.

#### 5.2.6 `prompts.yaml` — Prompt Catalog
- All LLM prompts stored with version numbers and creation dates.
- Sections: `extraction_v1`, `gibberish_v1`, `image_analysis_v1`, `csv_export_v1`.
- Change trail at the bottom records all modifications with dates and descriptions.

### 5.3 Deployment Architecture

```
                            Docker Host
                               │
                     ┌─────────┴──────────┐
                     │                    │
              ┌──────┴──────┐     ┌──────┴──────┐
              │  Ollama     │     │  i_extract  │
              │  (host)     │     │  :5053→:5000│
              │  :11434     │     │  (container) │
              └─────────────┘     └──────┬──────┘
                                         │
                                    ┌────┴────┐
                                    │ Browser │
                                    │ (User)  │
                                    └─────────┘
```

### 5.4 API Reference

| Endpoint | Method | Payload | Response |
|---|---|---|---|
| `/` | GET | — | HTML page |
| `/api/upload` | POST | `multipart/form-data` (file) | `{extracted, document_html, message}` |
| `/api/export_csv` | POST | `{"rows": [{"label", "value"}, ...]}` | CSV file download |
| `/api/learning/stats` | GET | — | `{"sample_count": N}` |
| `/api/prompts` | GET | — | Full prompts.yaml as JSON |

### 5.5 Security Considerations

| Concern | Mitigation |
|---|---|
| Large file uploads | 2 MB limit enforced by Flask config |
| Arbitrary file types | Extension whitelist (.pdf, .jpg, .jpeg) |
| Temp file leakage | `try/finally` cleanup in upload handler |
| Data privacy | All processing via local Ollama; no external calls |
| Prompt injection | LLM system prompt constrains output to JSON format |

### 5.6 Known Limitations

- **Vision Model Dependency**: JPEG extraction requires a vision-capable model (`qwen3.5:4b` or `gemma4:12b`). Falls back if unavailable.
- **Extraction Quality**: Bound by the LLM's ability to identify labeled data. Complex table structures may not parse correctly.
- **Learning Store Simplicity**: Similarity is word-overlap based, not semantic. The store is local to the container (lost on `docker compose down -v`).
- **No Streaming**: LLM responses are generated fully before returning. No token-by-token streaming.
- **Single Worker**: 1 gunicorn worker; concurrent requests queue behind it.
