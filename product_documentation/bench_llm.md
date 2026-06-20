# Bench LLM — Local LLM Benchmarking & Model Selection

**Ship the Right Model: Evidence-Based LLM Selection for Production**

Choosing the right local LLM for a production application is rarely obvious. Leaderboard scores measured on remote GPUs don't reflect real-world latency, and model quality varies dramatically across different tasks.

Our self-hosted benchmarking platform runs standardized quality evaluations across any number of Ollama-served models on your own hardware—measuring what actually matters: response speed, factual accuracy, hallucination resistance, bias neutrality, and context adherence on your infrastructure. Every result is scored by an independent judge model and weighted against your specific application profile, so you deploy with data, not gut feel.

---

## 1. Requirements

### Functional Requirements
- **Multi-Model Benchmarking**: Evaluate any number of Ollama-hosted generation models in a single automated run.
- **5 Quality Metrics**: Response Speed, Hallucination Resistance, Bias Neutrality, Factual Accuracy, and Context Adherence.
- **LLM-as-a-Judge Scoring**: Subjective metrics scored 1–5 by a configurable judge model with structured JSON output.
- **Application-Aware Recommendations**: Assign custom metric weights per application profile to identify the best-fit model.
- **Dashboard UI**: Single-page web interface with run history sidebar, per-question expandable detail, and PDF export via print-to-PDF.
- **Run Persistence**: All benchmark results saved as timestamped JSON files for audit trail and comparison.

### Non-Functional Requirements
- **Deployment**: Containerized via Docker, served by Gunicorn on port 5052.
- **Infrastructure**: No database, no message queue, no cloud APIs—entirely self-contained.
- **Latency Awareness**: Wall-clock response time measured per-question; scoring thresholds configured in `config.yaml`.
- **Privacy**: Every component (models, judge, data) runs locally. No data leaves the host.
- **Concurrency**: Single Gunicorn worker; benchmarks run in a background thread with status polling.

---

## 2. Product Features

| Feature | Description |
|---|---|
| **Multi-Model Runs** | Test any set of Ollama models in a single benchmark run. Configurable via `config.yaml`. |
| **5 Quality Metrics** | Response Speed, Hallucination Resistance, Bias Neutrality, Factual Accuracy, Context Adherence. |
| **LLM-as-a-Judge** | A dedicated judge model scores each response 1–5 with a written reasoning. |
| **App Profiles** | Define weighted metric importance per use case (e.g., FAQ chatbot weights factual accuracy at 2×). |
| **Run History** | All past results stored as JSON files; browsable from the dashboard sidebar. |
| **Per-Question Detail** | Expand each question to see the judge's score, reasoning, and the model's raw response. |
| **Dashboard UI** | Dark/light theme, responsive layout, print-to-PDF for offline reporting. |
| **Status Polling** | Frontend polls `/api/status` every 2 seconds during an active benchmark. |
| **No Cloud Dependency** | Everything—models, embeddings, judge—runs on local Ollama. Zero external API calls. |

---

## 3. Design Choices

### 3.1 LLM-as-a-Judge over Human Evaluation
- **Choice**: Use a separate judge LLM to score model responses instead of human raters.
- **Rationale**: Human evaluation does not scale to 15+ questions × N models per run. A judge model provides consistent, repeatable scoring with written justification for every score.
- **Trade-off**: Judge quality is bounded by the judge model's own capabilities; a weak judge produces unreliable scores.

### 3.2 LangChain ChatOllama Integration
- **Choice**: LangChain's `ChatOllama` wrapper for model invocation instead of raw HTTP calls.
- **Rationale**: Provides structured message handling, tool support, and a consistent interface for both generation and judge models.
- **Trade-off**: Adds a dependency that may lag behind Ollama's latest API features.

### 3.3 Background-Thread Benchmark Execution
- **Choice**: Daemon thread with `threading.Event` for cancellation signaling.
- **Rationale**: Keeps the Flask app responsive for status polling during a multi-minute benchmark run.
- **Trade-off**: No persistent task queue; a run cannot survive a container restart, and only one run can execute at a time.

### 3.4 JSON File Persistence
- **Choice**: Full benchmark results (per-question scores, judge reasoning, model responses) written as timestamped JSON files.
- **Rationale**: Zero infrastructure, human-readable, debuggable, and easily exported to external tools.
- **Trade-off**: No querying capability; listing all runs requires loading and parsing every file in the `runs/` directory.

### 3.5 Fixed Question Banks
- **Choice**: 15 hardcoded questions (3 per metric) in `test_suites.py`.
- **Rationale**: Ensures standardized, repeatable evaluation across runs and models. Questions are carefully crafted to stress specific failure modes (future events for hallucination, gendered prompts for bias).
- **Trade-off**: Questions never rotate, so repeated runs may produce identical evaluations. Potential for models to "memorize" answers.

### 3.6 Single Gunicorn Worker
- **Choice**: 1 worker with 1800s timeout.
- **Rationale**: Benchmarks can take 10–30 minutes for 3–5 models. A single worker avoids request-routing inconsistencies with the background thread.
- **Trade-off**: UI is unresponsive (shows stale data) during a benchmark run.

### 3.7 Host-Networked Ollama Access
- **Choice**: Container reaches Ollama via `host.docker.internal:11434`.
- **Rationale**: Ollama runs on the host for GPU access. No Docker networking gymnastics required.
- **Trade-off**: Not portable to multi-host or Kubernetes deployments without changes.

### 3.8 Frontend: Vanilla JS + Jinja2 Templates
- **Choice**: Single Jinja2 HTML template with embedded CSS and JavaScript; no frontend framework.
- **Rationale**: No build step, no npm dependencies, single-file deployment. The UI complexity (status polling, sidebar navigation, expandable cards) is manageable without a framework.
- **Trade-off**: Harder to maintain as features grow; no reactive component model.

---

## 4. High-Level Design

```
┌─────────────────────────────────────────────────────────┐
│                   Docker Container                       │
│  ┌─────────────────────────────────────────────────────┐│
│  │               Gunicorn (1 worker, 1800s timeout)    ││
│  │               port 5000                              ││
│  │  ┌─────────────────────────────────────────────────┐ ││
│  │  │           Flask Application                      │ ││
│  │  │                                                  │ ││
│  │  │  ┌─────────────┐  ┌──────────────┐              │ ││
│  │  │  │ main.py     │  │ storage.py   │              │ ││
│  │  │  │ (routes)    │  │ (JSON I/O)   │              │ ││
│  │  │  └──────┬──────┘  └──────────────┘              │ ││
│  │  │         │                                        │ ││
│  │  │  ┌──────▼──────┐  ┌──────────────┐              │ ││
│  │  │  │benchmark_   │  │ evaluator.py │              │ ││
│  │  │  │ agent.py    │──│ (judge logic)│              │ ││
│  │  │  │ (orchestr.) │  └──────────────┘              │ ││
│  │  │  └──────┬──────┘                                │ ││
│  │  │         │                                        │ ││
│  │  │  ┌──────▼──────┐                                 │ ││
│  │  │  │ test_suites │  ┌──────────────────────┐      │ ││
│  │  │  │ .py        │  │ templates/index.html  │      │ ││
│  │  │  │ (questions)│  │ (Jinja2 dashboard)    │      │ ││
│  │  │  └────────────┘  └──────────────────────┘      │ ││
│  │  └─────────────────────────────────────────────────┘ ││
│  └─────────────────────────────────────────────────────┘│
│                                                          │
│  Volumes:                                                │
│    ./config.yaml  ──>  /app/config.yaml                  │
│    ./runs/        ──>  /app/runs/                        │
│                                                          │
│  Communicates with:                                      │
│    host.docker.internal:11434  (Ollama on host)          │
└─────────────────────────────────────────────────────────┘
```

### Request Flow (Benchmark Run)
1. User clicks "Run Benchmark" → browser sends `POST /api/benchmark`
2. Flask spawns a daemon thread → `BenchmarkAgent.run(config, models, apps)`
3. For each model, for each metric (5), for each question (3):
   - Model is asked the question via LangChain `ChatOllama`
   - Wall-clock time recorded for Response Speed scoring
   - For the 4 subjective metrics: judge model scores the response 1–5 with reasoning
4. Per-metric scores averaged across questions → overall model score computed (mean)
5. App-weighted scores computed for each configured application profile
6. Run result JSON written to `runs/<timestamp>.json`
7. Frontend polls `/api/status` → `running: false` → UI shows results

---

## 5. Product Architecture

### 5.1 Directory Structure

```
bench_llm/
├── app/
│   ├── __init__.py              # Package marker (empty)
│   ├── main.py                  # Flask app: routes, config loading, benchmark trigger
│   ├── benchmark_agent.py       # Benchmark orchestrator: model iteration, question loop
│   ├── evaluator.py             # Judge system prompt, LLM-as-a-judge scoring logic
│   ├── test_suites.py           # 5 metrics × 3 questions (15 total) with metric metadata
│   ├── storage.py               # JSON file read/write for run persistence
│   └── templates/
│       └── index.html           # Single-page dashboard (Jinja2, vanilla JS + CSS)
├── config.yaml                  # Models list, app profiles, judge config, metric weights
├── Dockerfile                   # Python 3.11-slim, gunicorn entrypoint
├── docker-compose.yml           # Service definition, port mapping, volume mounts
├── requirements.txt             # Python dependencies (Flask, LangChain, etc.)
└── runs/                        # Timestamped JSON benchmark results
```

### 5.2 Component Breakdown

#### 5.2.1 `app/main.py` — Flask Application
- **Routes**:
  - `GET /` — Renders dashboard with run history sidebar and latest run results.
  - `POST /api/benchmark` — Triggers a new benchmark run in a background daemon thread. Returns 409 if already running.
  - `GET /api/status` — Returns `{"running": true/false}` for frontend polling.
  - `GET /api/runs` — Lists all past runs (run ID, timestamp, models tested).
  - `GET /api/runs/<run_id>` — Returns full run JSON including per-question scores and app recommendations.
  - `GET /api/metrics` — Returns metric definitions with labels and descriptions.
- **Key Design**: `threading.Event` (`_cancel_event`) enables best-effort cancellation. Config is loaded once at import from `config.yaml`.

#### 5.2.2 `app/benchmark_agent.py` — Benchmark Orchestrator
- **`run(config, models, apps)`**: Main loop—warms up each model, then iterates models × metrics × questions.
- **`process_metric(model, metric, config, judge_llm)`**: Scores a single model on a single metric by asking 3 questions, collecting responses, and computing the mean.
- **`score_response_speed(elapsed, thresholds)`**: Maps wall-clock time (seconds) to a 1–5 score via configurable thresholds.
- **`score_with_judge(judge_llm, question, response, metric_def)`**: Sends the judge model the question, model's response, and scoring criteria; parses JSON output.
- **`_compute_app_scores(model_scores, apps)`**: Applies weighting factors per app profile, breaks ties by lower latency.
- **Key Design**: Scores are accumulated into a flat list of `MetricScore` namedtuples, then grouped by model for the final `RunResult`.

#### 5.2.3 `app/evaluator.py` — Judge Logic
- **`JUDGE_SYSTEM`**: System prompt instructing the judge to return a JSON object `{"score": 1-5, "reason": "..."}`. Metric-specific criteria (hallucination, bias, accuracy, context) are embedded in the prompt for each call.
- **`get_judge_llm(config)`**: Builds a LangChain `ChatOllama` instance from the judge model config (model name, temperature 0.0, timeout).
- **Key Design**: Temperature 0.0 ensures deterministic scoring. The judge is invoked only for the 4 subjective metrics (Response Speed uses wall-clock time). Judge output is parsed with regex `r'\{[^{}]*"score"[^{}]*\}'` with fallback to score 3.

#### 5.2.4 `app/test_suites.py` — Question Definitions
- **5 metric definitions**: Each with a key, label, description, and 3 test questions.
- **Question types**:
  - **Response Speed**: Simple factual questions ("What is the capital of Japan?").
  - **Hallucination Resistance**: Questions about future events or nonexistent entities ("Who won the 2030 FIFA World Cup?").
  - **Bias Neutrality**: Sentence completions designed to reveal demographic or gender bias ("Complete this sentence neutrally: 'The most qualified candidate...'").
  - **Factual Accuracy**: Verifiable facts ("What is the chemical formula for water?").
  - **Context Adherence**: Questions paired with a context passage; model must answer from context alone.

#### 5.2.5 `app/storage.py` — Run Persistence
- **`save_run(run_result)`**: Serializes the `RunResult` dataclass to JSON and writes to `runs/<timestamp>.json`.
- **`load_runs()`**: Lists all JSON files in the `runs/` directory, returns sorted list of run metadata (newest first).
- **`load_run(run_id)`**: Reads a single run JSON file by ID.
- **Key Design**: Run IDs are timestamps (`YYYYMMDD_HHMMSS`). The runs directory is mounted as a Docker volume for persistence across restarts.

#### 5.2.6 `config.yaml` — Configuration
- **Models**: List of `{name, label, type}` entries for models under test.
- **Judge**: Model name, host, and generation parameters (temperature 0.0, max_tokens, top_p).
- **Apps**: Named application profiles with per-metric weights (e.g., `faq_chatbot` weights `factual_accuracy` at 2.0).
- **Scoring**: Response Speed thresholds (seconds mapped to scores 1–5), generation defaults.

### 5.3 Deployment Architecture

```
                            Docker Host
                               │
                    ┌──────────┴──────────┐
                    │                     │
             ┌──────┴──────┐      ┌──────┴──────┐
             │  Ollama     │      │  Bench LLM  │
             │  (host)     │      │  :5052→:5000│
             │  :11434     │      │  (container) │
             └─────────────┘      └──────┬──────┘
                                         │
                                    ┌────┴────┐
                                    │ Browser │
                                    │ (User)  │
                                    └─────────┘
```

### 5.4 API Reference

| Endpoint | Method | Payload | Response |
|---|---|---|---|
| `/` | GET | — | HTML dashboard |
| `/api/benchmark` | POST | — | `{"message": "Benchmark started"}` or 409 |
| `/api/status` | GET | — | `{"running": true/false}` |
| `/api/runs` | GET | — | `[{"run_id", "timestamp", "models_tested", ...}]` |
| `/api/runs/<run_id>` | GET | — | Full run JSON (scores, questions, app suggestions) |
| `/api/metrics` | GET | — | `{"response_speed": {"label", "description"}, ...}` |

### 5.5 Security Considerations

| Concern | Mitigation |
|---|---|
| Unauthorized access | No authentication—intended for isolated/internal networks only |
| Data leakage | All model inference and evaluation runs locally; no data sent to external APIs |
| Model poisoning | Judge model is self-hosted and configured by the operator via `config.yaml` |
| Run data exposure | Run JSON files stored on a Docker volume; accessible only to the container and host |

### 5.6 Known Limitations

- **Single-Threaded**: The background thread blocks the only Gunicorn worker; the dashboard is unresponsive during a benchmark run.
- **No Run Cancellation**: Once started, a benchmark cannot be cancelled (short of container restart).
- **Fixed Question Bank**: The 15 questions are hardcoded. No mechanism for custom questions without modifying `test_suites.py`.
- **No Retry Logic**: Model invocation failures or timeouts are recorded but not retried.
- **No GPU Awareness**: The Docker container does not request GPU resources, which is fine since Ollama runs on the host—but the benchmark cannot distinguish between model quality and GPU contention on the host.
- **Regex JSON Parsing**: The judge's JSON parser may fail for unusual output formatting, defaulting to score 3 silently.
