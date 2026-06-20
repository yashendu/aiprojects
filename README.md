# Experimental AI Apps Portfolio

## Projects

### blooms.ai
AI-first company showcase site with demo app gateway. Node.js server with HTTP Basic Auth, reverse proxy to Docker containers, and analytics collection. Serves the landing page dynamically from `web_conf.json`.

### faq_chatbot
Secure local RAG chatbot for enterprise document Q&A. Upload PDFs/DOCX/etc., paste text, or use pre-loaded sample HR policy. Answers from document context only via Ollama-hosted LLM. All processing local — no cloud dependency.

### bench_llm
Self-hosted LLM benchmarking platform. Evaluates Ollama-served models across 5 quality metrics (response speed, hallucination resistance, bias neutrality, factual accuracy, context adherence) using LLM-as-a-judge. Provides app-weighted recommendations.

### i_extract
Local LLM-powered document data extraction. Upload PDF or JPEG, extract structured key-value pairs (names, dates, amounts, IDs) into an editable table with CSV export. Split-view UI with row-to-document highlighting. Learning loop improves accuracy over time via few-shot storage.
