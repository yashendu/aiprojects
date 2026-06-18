# FAQ Chatbot — RAG Document Q&A Demo

A Retrieval-Augmented Generation chatbot that answers questions from HR policy documents. Built with Flask + ChromaDB + Ollama.

## Architecture

```
nginx (:80) → Node.js proxy (:3369) → Flask/Gunicorn (:5000) → Ollama (host:11434)
```

## Quick Start

```bash
docker compose up -d --build
```

Access at `https://<host>/blooms/demo/faq_chatbot/` (requires Basic Auth).

## Data Flow

1. **Session start** — precomputed embeddings + FAQs loaded from pickle (~1.3 MB, 131 chunks)
2. **User upload/paste** — document chunked → embedded via `nomic-embed-text` → stored in ChromaDB
3. **Question** → embedded → ChromaDB similarity search (top_k=4) → prompt + context → `gemma4:12b` generation

## Configuration

See `config.yaml` for Ollama host/model, chunking params, sample document, and limits.

## Future Product Features

### Streaming Responses (SSE)
Replace the current blocking POST with a Server-Sent Events endpoint so tokens stream to the UI as they're generated. The user sees the first token in 1–3s instead of waiting 16–32s for the full response.

**Impact**: Dramatically improves perceived UX with no model or infrastructure changes.

### Smaller / Faster Generation Models
The current model (`gemma4:12b`) is overkill for factual QA. Smaller models (gemma3:4b, phi4:7b, llama3.2:3b) would reduce generation latency from 15–30s down to 4–8s while maintaining answer quality for this use case.

**Impact**: 3–5× faster answers. User plans to experiment when time permits.

### GPU Passthrough to Container
Mount NVIDIA runtime so the Flask container calls Ollama directly via `localhost` instead of traversing `host.docker.internal`. Eliminates ~5ms RTT per request.

**Impact**: Marginal but removes a dependency on the Docker networking bridge.

### Model Warm-up / Keep-Alive
Set `OLLAMA_KEEP_ALIVE=5m` to keep the model loaded between requests, avoiding the 2–5s cold-start penalty per generation.

**Impact**: Shaves 2–5s off every question after the first.

### Async Embedding Overlap
While the generation model runs, pre-compute the embedding for the *next* user query in the background, overlapping the ~1s embedding cost with generation.

**Impact**: Hides embedding latency on follow-up questions.

### Speculative Decoding (Advanced)
Pair the main model with a small draft model (e.g., `phi4:7b` drafts, `gemma4:12b` verifies). Tokens/sec can improve 2–3× when the draft agrees with the main model.

**Impact**: Significant speedup, but complex to configure and model-dependent.
