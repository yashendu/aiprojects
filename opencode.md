# Development Principles

## 1. Workspace & Directory Guardrails
- All coding projects, experiments, assets, and artifacts MUST be contained strictly within the folder path: `~/lab/aiprojects`
- Do not initialize projects or create files outside of this directory tree under any circumstances.

## 2. Initialization Workflow (Every Session / First Run)
Before writing or modifying any application code, execute the following sequence:
1. **Locate and Read `README.md`**: Read the root `README.md` to gain a comprehensive understanding of the current workspace state and project catalog.
2. **Handle Missing README**: If `README.md` does not exist, create it immediately. Structure it with a high-level title: `# Experimental AI Apps Portfolio`.
3. **Locate and Read `opencode.md`**: Read this rules file to reinforce your operational constraints. If this file was initialized dynamically, ensure these core rules are preserved explicitly within it.

## 3. Directory Cataloging & Alignment
- On the first run, or whenever a change, addition, or deletion is detected in the subfolders or files within `~/lab/aiprojects`, automatically scan the directory.
- Catalogue the functionality of each sub-project/experimental app directly into the root `README.md`. Keep descriptions concise, technical, and focused on the app's core AI capability.

## 4. Strict Changelog Enforcement
Every single time a code modification, creation, or deletion is performed, document it.
- **File Target**: `changelog.md` (Create it in the root if it does not exist).
- **Format**: Append changes to a clean Markdown table using the following structure:

| Date & Time | Component/File | What Was Changed? | Why Was It Changed? |
| :--- | :--- | :--- | :--- |
| [YYYY-MM-DD HH:MM] | `path/to/file` | Brief description of the precise code modification. | The architectural or functional reason for the change. |

- **Timestamp Rule**: All timestamps MUST be read from the live server clock using `date '+%Y-%m-%d %H:%M'`. The reference timezone is Indian Standard Time (IST, UTC+5:30). Do not hardcode or assume timestamps. Always run the `date` command to capture the current server time for every changelog entry.
- **Append-Only Rule**: Never modify, correct, or delete past changelog entries. The changelog is an immutable audit log. New changes are always appended as new rows at the bottom of the table. Even if timestamps, formatting, or descriptions of past entries appear inaccurate, leave them untouched and only add new entries moving forward.

## 5. Product Documentation Standard

Every product MUST have a corresponding documentation file in `product_documentation/`.

### 5.1 File Naming & Location
- File: `product_documentation/<product_name>.md`
- One file per product. Use snake_case for multi-word product names.

### 5.2 Required Sections (in order)

| # | Section | Content |
|---|---------|---------|
| 1 | **Title + Marketing Intro** | Product name tagline + 1-paragraph value proposition |
| 2 | **Requirements** | Functional and non-functional requirements as bullet lists |
| 3 | **Product Features** | Markdown table: Feature \| Description |
| 4 | **Design Choices** | For each key architectural decision: Choice, Rationale, Trade-off (numbered subsections) |
| 5 | **High-Level Design** | ASCII architecture diagram + request flow (numbered steps) |
| 6 | **Product Architecture** | Directory tree, component breakdown per source file, deployment architecture, API reference table, security considerations table, known limitations |

### 5.3 API Reference Format
```markdown
| Endpoint | Method | Auth | Payload | Response |
|---|---|---|---|---|
```

### 5.4 Security Considerations Format
```markdown
| Concern | Mitigation |
|---|---|
```

## 6. Regression Testing Standard

Every product MUST have a regression test file in `regression_tests/`.

### 6.1 File Naming & Location
- File: `regression_tests/test_<product_name>.md`
- Integration tests: `regression_tests/test_integration.md`

### 6.2 Test Case Lineage (Traceability)
Every test case MUST include three traceability fields:

| Field | Purpose |
|-------|---------|
| **REQ** | Link to requirement in `product_documentation/<product>.md` (section number + line number) |
| **IMPL** | Link to source file and line number (relative `../` path from the test file) |
| **TC-ID** | Unique test identifier |

### 6.3 Test Case ID Format
```
TC-<PROJECT>-<AREA>-<NNN>
```
Project codes: `FC` (FAQ Chatbot), `BL` (Bench LLM), `BA` (Blooms.ai), `INT` (Integration).

Area codes: `API`, `CHUNK`, `SESS`, `LOADER`, `UI`, `SEC`, `DEPLOY`, `BENCH`, `SPEED`, `JUDGE`, `APP`, `STORAGE`, `DEMO`, `ANALYTICS`, `CONFIG`, `GATEWAY`, `AUTH`, `OLLAMA`, `DATAFLOW`, `ENDPOINT`.

### 6.4 Test Case Structure
Every test case uses a table format:

```markdown
| Field | Value |
|---|---|
| **Test ID** | `TC-XX-YYY-NNN` |
| **Title** | Short descriptive name |
| **REQ** | Link to requirement |
| **IMPL** | Link to implementation |
| **Precondition** | What must be true before running |
| **Steps** | Numbered step-by-step |
| **Expected** | Detailed expected behavior |
| **Pass Criteria** | Measurable pass/fail condition |
```

### 6.5 Coverage Requirements
- API endpoint tests for every route (success + error cases)
- Unit tests for core logic (chunking, scoring, parsing, etc.)
- Security tests (auth, XSS, file validation, etc.)
- Deployment tests (Docker health, connectivity checks)
- Integration tests for cross-project flows

### 6.6 Integration Tests File
`regression_tests/test_integration.md` covers:
- Proxy chain (nginx → Node.js → Docker)
- Cross-project auth enforcement
- Shared infrastructure (Ollama connectivity)
- End-to-end data flows
- Global health checks

---

## 7. Project Structure Standard

Every product project follows this structure:

```
<product_name>/
├── app/
│   ├── __init__.py              # Package marker
│   ├── main.py                  # Application entry point (Flask routes)
│   ├── ...                      # Domain-specific modules
│   └── templates/
│       └── index.html           # Single-page frontend (Jinja2, vanilla JS + CSS)
├── config.yaml                  # All runtime configuration
├── Dockerfile                   # Python 3.11-slim, gunicorn entrypoint
├── docker-compose.yml           # Service definition, port mapping, volume mounts
├── requirements.txt             # Python dependencies
└── README.md                    # Project-specific documentation
```

### 7.1 Application Entry Point Rules
- Flask app defined in `app/main.py` with `app = Flask(__name__)`
- Gunicorn as WSGI server: `gunicorn --bind 0.0.0.0:5000 --workers 1 --timeout <n> app.main:app`
- Single worker unless stateless (in-memory state requires single worker)

### 7.2 API Convention
- JSON request/response bodies
- Session management via Flask signed cookies (`session['sid']`)
- Route naming: `/api/<resource>` for data endpoints
- Error responses: `{"error": "<message>"}` with appropriate HTTP status code

### 7.3 Configuration Convention
- Single `config.yaml` at project root
- Loaded once at import time via `yaml.safe_load()`
- Sections: `ollama`, `generation`, `chunking`, `limits`, `sample` (as applicable)

### 7.4 Docker Convention
- Base image: `python:3.11-slim`
- Port mapping via docker-compose (internal 5000 → external varies)
- Config and data directories mounted as volumes (never bake user-modifiable config into the image)
- `host.docker.internal:host-gateway` extra host for Ollama access
- Restart policy: `unless-stopped`

---

## 8. Frontend Standard

### 8.1 Technology
- Vanilla JavaScript + CSS (no React, Vue, or build step)
- Jinja2 server-side templating for initial render
- Dark/light theme with CSS custom properties and localStorage persistence

### 8.2 UI Patterns
- Status bar with dot indicator (ready/busy/error states)
- Inline SVG icons (no external icon libraries or font-based icons)
- Responsive design with breakpoints at 768px and 480px
- Loading/typing indicators for async operations
- Follow-up suggestion buttons for chat interfaces

### 8.3 Security
- `textContent` (not `innerHTML`) for user-generated content rendering
- `linkify()` for safe URL detection (only http/https links)
- No inline event handlers in production (use `addEventListener`)

---

## 9. Content & Asset Guidelines

### 9.1 Text Content
- Use precise, technical language. Avoid marketing fluff in UI text.
- Tooltips and labels should be short (1-5 words) and descriptive.

### 9.2 Icons & Images
- Use inline SVG icons only (no Unicode emoji, no icon font libraries).
- SVGs must be inline in the HTML (no external SVG file dependencies).
- All icons must be original or from non-copyright sources.
- No external image hotlinking in production UI (use local assets or inline SVGs).

### 9.3 Disclaimer Placement
- Warnings about data usage, model training, or limitations belong in a **collapsible "How to Use" section** below the product description, not as a standalone banner.
- Disclaimers should use warning-colored styling (yellow/amber) with an alert icon.

---

## 10. Prompt Catalog Standard

Every product that sends prompts to an LLM MUST maintain a `prompts.yaml` file.

### 10.1 File Structure
```yaml
prompts:
  <prompt_name>:
    version: <integer>
    created: "<YYYY-MM-DD>"
    description: "Brief description of what this prompt does"
    system: |-
      Full system prompt text...

    user_template: |-
      Template with {placeholders} for runtime variables...
```

### 10.2 Change Trail
Every `prompts.yaml` MUST have a Change Trail section at the bottom:

```yaml
# =============================================================================
# Change Trail
# =============================================================================
# Version History:
#
# YYYY-MM-DD - v1 - Initial prompt catalog created
#   - prompt_name: What was added/changed
#
# YYYY-MM-DD - v2 - Updated extraction prompt
#   - extraction_v2: Changed output format from CSV to JSON
#
# =============================================================================
```

### 10.3 Rules
- Every prompt has a version number and creation date.
- Changes append to the Change Trail (never modify existing entries).
- Prompts are loaded at runtime from `prompts.yaml`, never hardcoded in Python.

---

## 11. Learning / RAG Store Standard

Products that improve over time through user interactions SHOULD implement a learning store.

### 11.1 Directory Convention
- Store path: `<project>/knowledge/samples/`
- Each sample is a JSON file: `<uuid>.json`

### 11.2 Sample Schema
```json
{
  "id": "12-char-hex",
  "filename": "original_filename.pdf",
  "document_text": "truncated text for similarity",
  "extracted_pairs": [{"label": "Name", "value": "John"}],
  "model_used": "qwen3.5:4b",
  "pair_count": 5
}
```

### 11.3 Similarity Retrieval
- Word-overlap based (Jaccard-like) for simplicity.
- Configurable `top_k` (default 3).
- Samples capped at `max_samples` (default 100), pruning lowest-value entries.

---

## 13. Ollama Integration Pattern

- All LLM calls go through Ollama running on the host at `host.docker.internal:11434`
- Generation model and embedding model are independently configurable in `config.yaml`
- Embedding via Ollama `/api/embed` endpoint
- Generation via Ollama `/api/generate` endpoint (or LangChain `ChatOllama`)
- Timeout must be set explicitly (120s for generation, 120s for embeddings)
- Temperature 0.0 for judge/deterministic tasks; 0.1 for chat generation

---

## 14. New Product Onboarding Checklist

When adding a new product to this workspace, follow this sequence:

1. **Create project directory** following [§7 Project Structure Standard](#7-project-structure-standard)
2. **Write product documentation** in `product_documentation/<name>.md` following [§5 Product Documentation Standard](#5-product-documentation-standard)
3. **Write regression tests** in `regression_tests/test_<name>.md` following [§6 Regression Testing Standard](#6-regression-testing-standard)
4. **Create prompt catalog** in `prompts.yaml` following [§10 Prompt Catalog Standard](#10-prompt-catalog-standard) (if LLM calls are involved)
5. **Create learning store** directory `knowledge/samples/` following [§11 Learning/RAG Store Standard](#11-learning--rag-store-standard) (if few-shot learning is applicable)
6. **Add app profile to bench_llm** in `bench_llm/config.yaml` for ongoing benchmarking
7. **Update root `README.md`** with the new product entry
8. **Log in `changelog.md`** using [§4 Strict Changelog Enforcement](#4-strict-changelog-enforcement)
