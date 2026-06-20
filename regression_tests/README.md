# Regression Test Suite — aiprojects

End-to-end regression tests for all products in the `aiprojects` monorepo.

## Scope

| Test File | Product | Tests |
|---|---|---|
| `test_faq_chatbot.md` | FAQ Chatbot — Document Q&A with RAG | 22 |
| `test_bench_llm.md` | Bench LLM — Local LLM Benchmarking & Model Selection | 17 |
| `test_blooms_ai.md` | Blooms.ai — Company Website & Demo Gateway | 18 |
| `test_integration.md` | Cross-Project Integration Tests | 8 |
| **Total** | | **65** |

## Lineage Convention

Every test case traces back to:

- **REQ** — A requirement in the product documentation (`product_documentation/*.md`)
- **IMPL** — The exact source file and line number implementing that requirement

This ensures each test verifies that a documented requirement continues to work after changes.

## Test Case ID Format

```
TC-<PROJECT>-<AREA>-<NNN>
```

| Project Code | Product |
|---|---|
| `FC` | FAQ Chatbot |
| `BL` | Bench LLM |
| `BA` | Blooms.ai |
| `INT` | Integration |

| Area Code | Meaning |
|---|---|
| `API` | HTTP endpoint tests |
| `CHUNK` | Text chunking logic |
| `SESS` | Session management |
| `LOADER` | Document loader tests |
| `UI` | Frontend / rendering tests |
| `SEC` | Security tests |
| `DEPLOY` | Deployment / Docker tests |
| `BENCH` | Benchmark orchestration |
| `SPEED` | Response speed scoring |
| `JUDGE` | LLM-as-a-judge logic |
| `APP` | App recommendation scoring |
| `STORAGE` | File persistence tests |
| `DEMO` | Demo gateway / proxy tests |
| `ANALYTICS` | Analytics endpoint tests |
| `CONFIG` | Configuration file tests |
| `GATEWAY` | Proxy chain tests |
| `AUTH` | Authentication tests |
| `OLLAMA` | Ollama connectivity tests |
| `DATAFLOW` | End-to-end data flow tests |
| `ENDPOINT` | Health check tests |

## How to Use

### Prerequisites

- All Docker containers running (see each project's `docker-compose.yml`)
- Ollama running on the host with required models
- Basic auth credentials known (for demo-path tests)

### Running Tests Manually

Each test case contains step-by-step instructions. Use `curl`, `docker exec`, or a REST client:

```bash
# Example: TC-FC-API-001 — Session Creation
curl -s http://localhost:5050/api/start -X POST | jq .

# Example: TC-BL-API-001 — Dashboard
curl -s -o /dev/null -w "%{http_code}" http://localhost:5052/

# Example: TC-BA-DEMO-001 — Authenticated Demo Listing
curl -s -u "demo:Oo&6Kjl1Bh" http://localhost:3369/demo/
```

### Running Tests with a Script

Each test file can be converted to a shell script or automated test suite. The structured format (table with Fields/Expected) is designed for both manual and automated execution.

### After Code Changes

Run the full regression suite to verify no regressions:

1. Start all containers: `docker compose up -d` in `faq_chatbot/` and `bench_llm/`
2. Start Node.js server: `node blooms.ai/server.js`
3. Verify Ollama: `curl http://host.docker.internal:11434/api/tags`
4. Execute tests from each file above
5. Mark TC-ID as PASS/FAIL based on Pass Criteria
