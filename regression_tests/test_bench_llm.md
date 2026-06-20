# Regression Tests: Bench LLM

> **Product**: Local LLM Benchmarking & Model Selection
> **Documentation**: `product_documentation/bench_llm.md`
> **Source**: `bench_llm/`

---

## Test Tag Convention

Each test case is tagged with:
- **REQ** — Link to requirement in product documentation
- **IMPL** — Link to implementation file and line number
- **TC** — Test case identifier

---

## TC-BL-API-001: Dashboard Page Renders

| Field | Value |
|---|---|
| **Test ID** | `TC-BL-API-001` |
| **Title** | GET `/` returns dashboard HTML with all required sections |
| **REQ** | [§1 - Dashboard UI](product_documentation/bench_llm.md#L18), [§5.2.1 - GET /](product_documentation/bench_llm.md#L169) |
| **IMPL** | [`bench_llm/app/main.py`](../bench_llm/app/main.py), [`bench_llm/app/templates/index.html`](../bench_llm/app/templates/index.html) |
| **Precondition** | Docker container running |
| **Steps** | 1. Send `GET /`<br>2. Inspect HTML response |
| **Expected** | HTTP 200. HTML contains: Run Benchmark button, run history sidebar area, status bar, results display area. |
| **Pass Criteria** | All UI sections are present in the rendered HTML. |

---

## TC-BL-API-002: Start Benchmark

| Field | Value |
|---|---|
| **Test ID** | `TC-BL-API-002` |
| **Title** | POST `/api/benchmark` starts a benchmark run |
| **REQ** | [§1 - Multi-Model Benchmarking](product_documentation/bench_llm.md#L14), [§5.2.1 - /api/benchmark](product_documentation/bench_llm.md#L170) |
| **IMPL** | [`bench_llm/app/main.py`](../bench_llm/app/main.py) |
| **Precondition** | Server running, Ollama accessible, no benchmark currently running |
| **Steps** | 1. Send `POST /api/benchmark`<br>2. Immediately check `GET /api/status` |
| **Expected** | Step 1: Returns 200 with `{"status": "started"}` or `{"message": "Benchmark started"}`. Step 2: `{"running": true}`. |
| **Pass Criteria** | Benchmark starts and status immediately reflects running state. |

---

## TC-BL-API-003: Concurrent Benchmark Rejected

| Field | Value |
|---|---|
| **Test ID** | `TC-BL-API-003` |
| **Title** | Second POST `/api/benchmark` while one is running returns 409 |
| **REQ** | [§5.2.1 - 409 if already running](product_documentation/bench_llm.md#L170) |
| **IMPL** | [`bench_llm/app/main.py`](../bench_llm/app/main.py) |
| **Precondition** | A benchmark run is in progress (`/api/status` returns `running: true`) |
| **Steps** | 1. Send `POST /api/benchmark` while a benchmark is already running |
| **Expected** | HTTP 409 with error message indicating a benchmark is already in progress |
| **Pass Criteria** | Concurrent benchmark request is rejected with 409. |

---

## TC-BL-API-004: Status Polling

| Field | Value |
|---|---|
| **Test ID** | `TC-BL-API-004` |
| **Title** | GET `/api/status` returns benchmark running state |
| **REQ** | [§2 - Status Polling](product_documentation/bench_llm.md#L41), [§4 - Request Flow step 7](product_documentation/bench_llm.md#L139) |
| **IMPL** | [`bench_llm/app/main.py`](../bench_llm/app/main.py) |
| **Precondition** | Server running |
| **Steps** | 1. Send `GET /api/status` when no benchmark running<br>2. Start a benchmark<br>3. Send `GET /api/status` |
| **Expected** | Step 1: `{"running": false}`. Step 3: `{"running": true}`. After benchmark completes, returns `{"running": false}`. |
| **Pass Criteria** | Status accurately reflects benchmark running state at all times. |

---

## TC-BL-API-005: List Runs

| Field | Value |
|---|---|
| **Test ID** | `TC-BL-API-005` |
| **Title** | GET `/api/runs` returns list of past benchmark runs |
| **REQ** | [§2 - Run History](product_documentation/bench_llm.md#L38), [§5.2.1 - /api/runs](product_documentation/bench_llm.md#L172) |
| **IMPL** | [`bench_llm/app/storage.py`](../bench_llm/app/storage.py) |
| **Precondition** | At least one benchmark run has been completed |
| **Steps** | 1. Send `GET /api/runs` |
| **Expected** | `{"runs": [{"run_id": "...", "timestamp": "...", "models_tested": [...]}, ...]}`. Runs are sorted newest-first. Each entry has `run_id`, `timestamp`, `models_tested`. |
| **Pass Criteria** | Response is a JSON object with `runs` array. At least one run entry present after running a benchmark. |

---

## TC-BL-API-006: Get Run Detail

| Field | Value |
|---|---|
| **Test ID** | `TC-BL-API-006` |
| **Title** | GET `/api/runs/<run_id>` returns full benchmark results |
| **REQ** | [§2 - Per-Question Detail](product_documentation/bench_llm.md#L39), [§5.2.1 - /api/runs/](product_documentation/bench_llm.md#L173) |
| **IMPL** | [`bench_llm/app/storage.py`](../bench_llm/app/storage.py) |
| **Precondition** | A benchmark run exists with run_id from `/api/runs` |
| **Steps** | 1. Get run_id from `/api/runs`<br>2. Send `GET /api/runs/<run_id>` |
| **Expected** | Returns full run JSON. Structure contains: `run_id`, `timestamp`, `models` array with per-model scores, `app_suggestions` with weighted recommendations. Each model entry has per-metric scores and per-question details. |
| **Pass Criteria** | Response contains all required fields. Each metric score is between 1 and 5. `app_suggestions` identifies a best model. |

---

## TC-BL-API-007: Get Run Detail — Not Found

| Field | Value |
|---|---|
| **Test ID** | `TC-BL-API-007` |
| **Title** | GET `/api/runs/<nonexistent>` returns 404 |
| **REQ** | [§5.2.1 - /api/runs/](product_documentation/bench_llm.md#L173) |
| **IMPL** | [`bench_llm/app/storage.py`](../bench_llm/app/storage.py) |
| **Precondition** | Server running |
| **Steps** | 1. Send `GET /api/runs/nonexistent_run` |
| **Expected** | HTTP 404 with error message |
| **Pass Criteria** | Nonexistent run returns 404. |

---

## TC-BL-API-008: Get Metric Definitions

| Field | Value |
|---|---|
| **Test ID** | `TC-BL-API-008` |
| **Title** | GET `/api/metrics` returns all 5 metric definitions |
| **REQ** | [§1 - 5 Quality Metrics](product_documentation/bench_llm.md#L15), [§5.2.1 - /api/metrics](product_documentation/bench_llm.md#L174) |
| **IMPL** | [`bench_llm/app/test_suites.py`](../bench_llm/app/test_suites.py) |
| **Precondition** | Server running |
| **Steps** | 1. Send `GET /api/metrics` |
| **Expected** | JSON object with 5 keys: `response_speed`, `hallucination`, `bias`, `factual_accuracy`, `context_adherence`. Each has `label` and `description` strings. |
| **Pass Criteria** | All 5 metric keys are present. Labels are non-empty. Descriptions are non-empty. |

---

## TC-BL-BENCH-001: Benchmark Produces Valid Run Result

| Field | Value |
|---|---|
| **Test ID** | `TC-BL-BENCH-001` |
| **Title** | Full benchmark run produces a valid, complete result |
| **REQ** | [§1 - Multi-Model Benchmarking](product_documentation/bench_llm.md#L14), [§1 - Run Persistence](product_documentation/bench_llm.md#L19) |
| **IMPL** | [`bench_llm/app/benchmark_agent.py`](../bench_llm/app/benchmark_agent.py), [`bench_llm/app/evaluator.py`](../bench_llm/app/evaluator.py), [`bench_llm/app/storage.py`](../bench_llm/app/storage.py) |
| **Precondition** | Ollama running with at least one test model and the judge model |
| **Steps** | 1. Send `POST /api/benchmark`<br>2. Poll `/api/status` until complete<br>3. Get run_id from `/api/runs`<br>4. Fetch full run result from `/api/runs/<run_id>`<br>5. Inspect the saved JSON file in `runs/` directory |
| **Expected** | - All configured models are tested<br>- Each model has scores for all 5 metrics<br>- Per-question details are present (3 questions per metric)<br>- Judge reasoning is present for subjective metrics<br>- `app_suggestions` contains recommendations<br>- A new JSON file appears in `runs/` directory |
| **Pass Criteria** | Every model has 5 metric scores. Each score is 1-5. `app_suggestions` is non-empty. JSON file is written to disk. |

---

## TC-BL-SPEED-001: Response Speed Thresholds

| Field | Value |
|---|---|
| **Test ID** | `TC-BL-SPEED-001` |
| **Title** | Response speed scoring maps elapsed time to correct score |
| **REQ** | [§2 - 5 Quality Metrics](product_documentation/bench_llm.md#L35), [§5.2.2 - score_response_speed](product_documentation/bench_llm.md#L180) |
| **IMPL** | [`bench_llm/app/benchmark_agent.py`](../bench_llm/app/benchmark_agent.py) |
| **Precondition** | None (unit-level) |
| **Steps** | 1. Call `score_response_speed(2, thresholds)` with thresholds e.g. `[5, 10, 20, 30]`<br>2. Call with elapsed=7<br>3. Call with elapsed=15<br>4. Call with elapsed=25<br>5. Call with elapsed=35 |
| **Expected** | - 2s → score 5<br>- 7s → score 4<br>- 15s → score 3<br>- 25s → score 2<br>- 35s → score 1 |
| **Pass Criteria** | Scores follow the threshold mapping: <5s=5, 5-10=4, 10-20=3, 20-30=2, >30=1. |

---

## TC-BL-JUDGE-001: Judge JSON Parsing

| Field | Value |
|---|---|
| **Test ID** | `TC-BL-JUDGE-001` |
| **Title** | Judge model response with valid JSON is parsed correctly |
| **REQ** | [§1 - LLM-as-a-Judge](product_documentation/bench_llm.md#L16), [§5.2.3 - Judge logic](product_documentation/bench_llm.md#L188) |
| **IMPL** | [`bench_llm/app/evaluator.py`](../bench_llm/app/evaluator.py) |
| **Precondition** | None (unit-level) |
| **Steps** | 1. Simulate judge response: `'{"score": 4, "reason": "The model correctly refused to answer."}'`<br>2. Parse using regex `r'\{[^{}]*"score"[^{}]*\}'` |
| **Expected** | Parsed `score=4`, `reason` is extracted. |
| **Pass Criteria** | Valid JSON in expected format is parsed correctly. |

---

## TC-BL-JUDGE-002: Judge JSON Parse Fallback

| Field | Value |
|---|---|
| **Test ID** | `TC-BL-JUDGE-002` |
| **Title** | Malformed judge response falls back to default score 3 |
| **REQ** | [§5.2.3 - Regex fallback to score 3](product_documentation/bench_llm.md#L188) |
| **IMPL** | [`bench_llm/app/evaluator.py`](../bench_llm/app/evaluator.py) |
| **Precondition** | None (unit-level) |
| **Steps** | 1. Simulate malformed judge response: `"The model did ok"` (no JSON)<br>2. Attempt to parse |
| **Expected** | Default score of 3 is returned. |
| **Pass Criteria** | Non-JSON response does not crash; score defaults to 3. |

---

## TC-BL-APP-001: Weighted App Suggestions

| Field | Value |
|---|---|
| **Test ID** | `TC-BL-APP-001` |
| **Title** | Application-aware recommendations compute correctly |
| **REQ** | [§1 - Application-Aware Recommendations](product_documentation/bench_llm.md#L17), [§5.2.2 - _compute_app_scores](product_documentation/bench_llm.md#L182) |
| **IMPL** | [`bench_llm/app/benchmark_agent.py`](../bench_llm/app/benchmark_agent.py) |
| **Precondition** | None (unit-level) |
| **Steps** | 1. Define Model A: `{response_speed: 5, factual_accuracy: 3, hallucination: 4, bias: 4, context_adherence: 3}`<br>2. Define Model B: `{response_speed: 3, factual_accuracy: 5, hallucination: 5, bias: 5, context_adherence: 5}`<br>3. Define app with weights: `{factual_accuracy: 2.0, context_adherence: 2.0, response_speed: 1.0, hallucination: 1.5, bias: 0.5}`<br>4. Call `_compute_app_scores` |
| **Expected** | Weighted scores are calculated correctly. If weights favor factual_accuracy and context_adherence, Model B should be recommended. Ties broken by lower latency. |
| **Pass Criteria** | Weighted score computation follows: `sum(metric_score * metric_weight for each metric) / sum(weights)`. Best model per app matches expected heuristic. |

---

## TC-BL-STORAGE-001: Save and Load Run

| Field | Value |
|---|---|
| **Test ID** | `TC-BL-STORAGE-001` |
| **Title** | Run result is persisted to disk and can be loaded back |
| **REQ** | [§1 - Run Persistence](product_documentation/bench_llm.md#L19), [§5.2.5 - Storage](product_documentation/bench_llm.md#L200-L203) |
| **IMPL** | [`bench_llm/app/storage.py`](../bench_llm/app/storage.py) |
| **Precondition** | `runs/` directory exists and is writable |
| **Steps** | 1. Create a `RunResult` dataclass instance with sample data<br>2. Call `save_run(run_result)`<br>3. Call `load_runs()`<br>4. Call `load_run(run_id)` with the saved run_id |
| **Expected** | - A new JSON file is created in `runs/` directory<br>- `load_runs()` includes the new run in the list<br>- `load_run()` returns the same data that was saved |
| **Pass Criteria** | File exists. Round-trip save/load preserves all fields exactly. |

---

## TC-BL-STORAGE-002: Empty Runs Directory

| Field | Value |
|---|---|
| **Test ID** | `TC-BL-STORAGE-002` |
| **Title** | Empty runs directory returns empty list |
| **REQ** | [§5.2.5 - Storage](product_documentation/bench_llm.md#L200-L203) |
| **IMPL** | [`bench_llm/app/storage.py`](../bench_llm/app/storage.py) |
| **Precondition** | `runs/` directory is empty or does not exist |
| **Steps** | 1. Call `load_runs()` |
| **Expected** | Returns empty list. Does not throw. |
| **Pass Criteria** | Empty directory handled gracefully. |

---

## TC-BL-DEPLOY-001: Container Health Check

| Field | Value |
|---|---|
| **Test ID** | `TC-BL-DEPLOY-001` |
| **Title** | Docker container starts and serves on expected port |
| **REQ** | [§1 - Deployment](product_documentation/bench_llm.md#L22) |
| **IMPL** | [`bench_llm/Dockerfile`](../bench_llm/Dockerfile), [`bench_llm/docker-compose.yml`](../bench_llm/docker-compose.yml) |
| **Precondition** | Docker and docker-compose installed |
| **Steps** | 1. `docker compose up -d` from `bench_llm/`<br>2. `docker compose ps`<br>3. `curl -s -o /dev/null -w "%{http_code}" http://localhost:5052/` |
| **Expected** | Container state is "Up". HTTP request returns 200. |
| **Pass Criteria** | Container is running and port 5052 responds. |

---

## TC-BL-DEPLOY-002: Ollama Connectivity

| Field | Value |
|---|---|
| **Test ID** | `TC-BL-DEPLOY-002` |
| **Title** | Container can reach Ollama and detect configured models |
| **REQ** | [§5.3 - Deployment Architecture](product_documentation/bench_llm.md#L211-L228) |
| **IMPL** | [`bench_llm/config.yaml`](../bench_llm/config.yaml#L2) |
| **Precondition** | Both containers running, Ollama running on host |
| **Steps** | 1. `docker exec bench_llm curl -s http://host.docker.internal:11434/api/tags` |
| **Expected** | Returns JSON with available models. Models configured in `config.yaml` (e.g., `qwen3.5:4b`, `gemma4:12b`, `llama3.2:3b`) are present. Judge model is available. |
| **Pass Criteria** | Ollama API responds. Required models are listed. |

---

## Regression Test Summary: Bench LLM

| Area | Test Count |
|---|---|
| API Endpoint Tests | 8 |
| Benchmark Orchestration Tests | 1 |
| Speed Scoring Tests | 1 |
| Judge Evaluation Tests | 2 |
| Weighted Scoring Tests | 1 |
| Storage Tests | 2 |
| Deployment Tests | 2 |
| **Total** | **17** |
