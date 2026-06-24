# i_extract

Local LLM-powered document data extraction service. Upload PDFs or JPEG images and extract structured key-value pairs using configurable Ollama models.

## Features

- **PDF text extraction** via Docling or PyMuPDF with automatic fallback to **Surya OCR** for scanned documents
- **Image OCR** via Surya OCR (multilingual, 12 Indian languages supported) with fallback to Ollama vision model
- **Key-value pair extraction** powered by local LLMs (llama3.2, gemma4, etc.) with dedicated Indic language extraction pipeline
- **Language detection** — automatically identifies document language(s) via Unicode script analysis and displays it in the UI
- **Extraction validation** — a separate LLM model flags hallucinated values for higher accuracy
- **Learning store** — similar past extractions are used as few-shot examples, improving consistency over time
- **CSV export** of extracted fields
- **Inline editing** of extracted fields with source-text highlighting in PDF documents

## Architecture

```
Upload (PDF/JPEG)
    │
    ├── PDF ──→ Docling / PyMuPDF ──→ text
    │              │
    │              └── if text < 50 chars ──→ Surya OCR on page images
    │
    ├── JPEG ──→ Surya OCR ──→ text
    │              │
    │              └── if empty ──→ Ollama vision model
    │
    └── Both ──→ Language detection (Unicode script analysis)
                    │
                    ├── Not Indic ──→ extract_pairs() (English pipeline)
                    │
                    └── Indic ──→ extract_indic_pairs() (Indic pipeline)
                                    │
                                    └── Validation (separate LLM model)
                                            │
                                            └── SSE stream → Frontend
```

## Surya OCR Integration

Surya OCR is a deep-learning based OCR engine supporting 90+ languages with particular strength in Indian language scripts. It is used in two scenarios:

1. **Scanned PDFs** — when Docling/PyMuPDF extract less than 50 characters, each page is rendered at 150 DPI and passed through Surya OCR
2. **Image files** — Surya is tried first; only on empty result does the service fall back to the Ollama vision model

Surya models are downloaded to `~/.cache/surya/` on first run (~1 GB). In Docker, persist this with a volume mount (see `docker-compose.yml`).

**Supported languages (default):** Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Odia, Sinhala, English

## Language Detection

After text extraction, the service analyzes Unicode script ranges to determine the document language:

- One script > 50% → identified as that language (e.g., "Hindi", "Tamil", "English")
- No clear majority → "Multi-language"
- No text/numeric only → defaults to "English"

Detected language appears as a badge in the status bar (e.g., "🌐 Hindi (85%)") and is emitted as a `language_detected` SSE event during processing.

## Configuration

See `config.yaml` for all settings:

```yaml
ollama:
  host: http://host.docker.internal:11434
  model: llama3.2:3b           # main extraction model
  vision_model: qwen3.5:4b     # vision model for image OCR fallback
  validation_model: gemma4:12b # validation model (optional, independent check)
  indic_model: gemma4:12b      # model used for Indic language extraction
  embedding_model: nomic-embed-text

surya:
  enabled: true
  languages: [hi, ta, te, bn, mr, gu, kn, ml, pa, or, si, en]
  min_text_length_for_skip: 50   # pages with more text than this skip Surya

extraction:
  min_confidence: 0.3
  max_pairs: 50

learning:
  max_samples: 100
  similarity_top_k: 3
  store_path: /app/knowledge/samples
```

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Serves the web UI |
| `/api/upload` | POST | Upload file, returns SSE stream of extraction events |
| `/api/export_csv` | POST | Export extracted rows as CSV |
| `/api/learning/stats` | GET | Returns sample count in learning store |
| `/api/prompts` | GET | Returns the prompt catalog |

### SSE Event Stream

The `/api/upload` endpoint returns a newline-delimited JSON stream with these event types:

```json
{"stage": "parsing",         "message": "..."}
{"stage": "language_detected", "language": "Hindi", "confidence": 0.85}
{"stage": "analyzing",       "message": "..."}
{"stage": "extracting",      "message": "..."}
{"stage": "validating",      "message": "..."}
{"stage": "complete",        "extracted": [...], "document_html": "...", "message": "..."}
{"stage": "error",           "message": "..."}
```

## Running

### Docker (recommended)

```bash
docker compose build
docker compose up -d
# Access at http://localhost:5053
```

### Development

```bash
pip install -r requirements.txt
# Install test dependencies: pip install pytest
OLLAMA_HOST=http://localhost:11434 gunicorn --bind 0.0.0.0:5000 --workers 1 --timeout 300 app.main:app
```

## Testing

```bash
pip install pytest
pytest tests/ -v
```

Tests cover:
- Language detection (English, Hindi, multi-language, edge cases)
- Unicode script counting
- KV pattern detection
- Surya OCR integration (mocked model loading)
- Document processor fallback logic
- API SSE event format (language_detected stage)

## Prompts

All LLM prompts are defined in `prompts.yaml` with a change trail at the bottom of the file. Edit prompts there without touching Python code.
