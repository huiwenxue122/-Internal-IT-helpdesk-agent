# GaggiaAgent — Policy-Governed IT Helpdesk Agent

GaggiaAgent is a LangGraph-orchestrated policy enforcement agent for internal IT helpdesk requests. It combines policy RAG, a high-risk rule graph, explicit conflict detection, deterministic trust/tool/output guards, and an auditable decision trace.

**Core architectural principle:** The Policy Reasoning Agent proposes decisions. It does not have execution authority. Tool execution is controlled by deterministic guards that run independently of any LLM.

---

## Demo

GaggiaAgent ships with a product-style demo UI called the **GaggiaAgent Policy Console**.

The UI separates three concerns:
- **Scenario** — what the user is asking (one of the 21 official test cases, as a message template)
- **Run As** — who is asking (trust tier + requester identity)
- **Trace** — why the agent made the decision (Router, Policy Evidence, Conflicts, Tool Safety, Output Filter, Backend tabs)

This separation lets you run the same request under Blue, Grey, or Red trust tiers and compare how the policy enforcement changes.

### Local dev mode (two terminals)

```bash
# Terminal 1 — backend
uvicorn demo_api.app:app --reload --port 8000

# Terminal 2 — frontend
cd demo_ui
npm install
npm run dev
```

Open http://localhost:5173

### Local production mode (single process)

```bash
npm --prefix demo_ui install
npm --prefix demo_ui run build
uvicorn demo_api.app:app --host 0.0.0.0 --port 8000
```

Open http://localhost:8000

### Docker

```bash
docker build -t gaggia-agent .
docker run --env-file .env -p 8000:8000 gaggia-agent
```

Open http://localhost:8000

---

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Build the in-memory policy index (required before first run)
python scripts/build_policy_index.py

# Run the test suite
pytest -q

# Run the evaluation suite (21 official + 16 regression scenarios)
python scripts/run_eval.py --all
```

No API key is needed to run tests or the evaluation suite. The agent falls back to deterministic logic automatically.

---

## Environment Variables

Create a `.env` file at the repo root (see `.env.example`). All variables are optional.

| Variable | Purpose | Default |
|---|---|---|
| `ANTHROPIC_API_KEY` | Enables live Claude LLM mode | — (deterministic fallback) |
| `ANTHROPIC_MODEL` | Claude model name | `claude-sonnet-4-20250514` |
| `LANGSMITH_API_KEY` | LangSmith trace export | — (tracing disabled) |
| `LANGSMITH_TRACING` | Enable LangSmith tracing | `false` |
| `LANGSMITH_PROJECT` | LangSmith project name | `gaggia-agent` |
| `NEO4J_URI` | Neo4j AuraDB connection URI | — (in-memory graph fallback) |
| `NEO4J_USERNAME` | Neo4j username | — |
| `NEO4J_PASSWORD` | Neo4j password | — |
| `CHROMA_PERSIST_PATH` | ChromaDB persistence path | — (lexical fallback) |

**Never commit `.env`.** The `.gitignore` excludes it.

Fallback behaviour when keys are absent:
- No `ANTHROPIC_API_KEY` → deterministic routing and policy reasoning (all tests pass in this mode)
- No Neo4j credentials → in-memory policy graph (identical rule set, no external dependency)
- ChromaDB embedding failure → keyword-based lexical retrieval

---

## Architecture

![GaggiaAgent architecture diagram](docs/architecture.png)

### Component roles

| Component | Role |
|---|---|
| **Router Agent** | Classifies intent, extracts target entities and requested fields, predicts candidate tools, detects adversarial signals. Deterministic fallback when no LLM is available. |
| **Trust Tier Guard** | Enforces tier-level restrictions before policy reasoning. Red users cannot proceed to tool-executing paths. |
| **Policy Retriever** | Retrieves relevant policy sections (ChromaDB or lexical) and high-risk rules (Neo4j or in-memory graph). Populates a `PolicyEvidenceBundle`. |
| **Conflict Detector** | Identifies contradictions between retrieved rules (e.g., broad denial vs. manager exception). Provides resolution hints. |
| **Policy Reasoning Agent** | Proposes a verdict (`allow`, `deny`, `clarify`, `escalate`), a list of allowed tool calls with arguments, and policy citations. **Does not execute tools.** |
| **Tool Authorization Guard** | Validates proposed tool calls against trust tier, target scope, and policy rules. Blocks any call that does not meet all conditions. |
| **Tool Executor** | Calls mock IT tools. Returns raw outputs that are never directly exposed to users. |
| **Output Filter** | Redacts sensitive fields (salary, personal contact, performance data) from tool outputs before they reach the Response Agent. |
| **Response Agent** | Generates the user-facing message from filtered outputs and policy citations. |
| **Decision Logger** | Writes a structured audit record to `logs/decisions.jsonl`. Sensitive values are never written. |

---

## Policy Layer

The expanded corporate IT helpdesk policy is stored at:

```
gaggia_agent/policy/gaggia_it_helpdesk_policy_expanded.md
```

The seed policy was expanded into a larger, realistic document (sections covering identity verification, password management, directory data, HR records, file access, legal holds, vendor access, offboarding, and more) so that policy is retrieved in context rather than embedded wholesale into LLM prompts.

**Section retrieval** uses ChromaDB for semantic similarity search, with a lexical keyword fallback when embeddings are unavailable. The query is constructed from intent, requested fields, and candidate tools.

**High-risk rules** are modelled explicitly as `PolicyRule` objects and indexed in a graph:
- Team Red restrictions (§1.2)
- HR record privacy (§5.2)
- Manager active-status exception (§5.4)
- Legal-hold drive access (§4.3, §15.1)
- Personal drive protection (§6.2)
- Privileged account reset restrictions (§2.2)
- Claimed-authority bypass detection (§7.3)
- Prompt injection handling (§7.4)
- Raw tool output filtering (§19.3)

---

## Why Graph + RAG

Vector retrieval alone can miss cross-references and exceptions. A salary request and an active-status request both involve `lookup_employee`, but only the active-status path triggers the manager exception rule — the graph models this distinction explicitly through `data_types`, `resource_types`, and rule relationships.

**Example:** The broad prohibition on individual HR records (§5.2) has an explicit exception for verified managers confirming active status for direct reports (§5.4). The conflict detector surfaces this contradiction; the Policy Reasoning Agent resolves it based on requester profile and target entity. A plain vector search over policy text would not reliably surface the exception when the salary path also matches superficially similar sections.

---

## Safety Model

- **LLM agents do not execute tools.** The Policy Reasoning Agent produces a structured proposal; deterministic guards decide whether to honour it.
- **Red users cannot execute non-escalation tools**, regardless of what the policy reasoning agent proposes.
- **Grey users** on high-risk actions receive `clarify` or `escalate` verdicts pending human review.
- **Side-effecting mock tools** (`reset_password`, `grant_file_access`) include defensive checks against privileged targets.
- **Tool outputs are filtered** before reaching the Response Agent. Salary, personal contact details, performance ratings, disciplinary records, and home addresses are always redacted from user-facing output.
- **Raw tool outputs are never returned** by the API or shown in the UI.
- **Adversarial signals** (`prompt_injection`, `claimed_authority`, `urgency`, `raw_tool_output`) are detected deterministically by the Router Agent and influence both verdict and citations independently of the LLM.

---

## Evaluation

| Metric | Result |
|---|---|
| Unit + integration tests | **100 / 100 pass** |
| Official take-home scenarios | **21 / 21 pass** |
| Regression / adversarial scenarios | **16 / 16 pass** |
| Total evaluation scenarios | **37 / 37 pass** |

Report: `gaggia_agent/evaluation/results/eval_report.md`

> These results demonstrate coverage for the included scenarios and regression suite. They do not prove complete policy correctness for all possible requests.

Each scenario asserts one or more of:

- **verdict** — expected allow / deny / clarify / escalate
- **required citations** — specific policy sections that must appear
- **forbidden tools** — tools that must not be executed
- **authorized tools** — tools that must be proposed
- **sensitive leakage** — raw sensitive values must not appear in response or logs
- **redacted fields** — specific output fields must be redacted
- **trust-tier enforcement** — Red / Grey / Blue behaviour differences

---

## Demo Scenarios

The UI includes all 21 official take-home test scenarios as request templates, grouped by category:

| Category | Count | Examples |
|---|---|---|
| **Clearly Allowed** | 5 | Password reset, work email, PTO policy question |
| **Clearly Denied** | 5 | Salary, performance review, home address |
| **Ambiguous / Judgment Calls** | 6 | Legal-hold drive, manager active-status, org chart |
| **Adversarial** | 5 | Prompt injection, CISO-approved bypass, skip-level authority claim |

**UX model:**
- Selecting a scenario updates only the message text. Trust tier and profile are not changed.
- The **Run As** selector sets the combined trust tier and requester identity.
- **"Use suggested context"** applies the scenario's recommended tier and identity in one click.
- The **Effective Request** panel previews the exact payload that will be sent.
- The **Compare Trust Tiers** button runs the current message under Blue, Grey, and Red simultaneously.

---

## Known Limitations

- **Mock tools only.** `reset_password`, `grant_file_access`, `lookup_employee`, `query_hr_database`, and `escalate_to_human` simulate IT side effects — they do not connect to real systems.
- **Deterministic fallback is less flexible than a live LLM.** Keyword-based intent classification and entity extraction can misclassify unusual phrasings.
- **Neo4j is optional.** The in-memory graph fallback is used by default and has identical rule coverage, but loses persistence across restarts.
- **ChromaDB can fall back to lexical retrieval.** Semantic recall may differ slightly.
- **Finite evaluation coverage.** The evaluation suite exercises the included scenarios. Novel requests may trigger edge cases not covered by the current heuristics.
- **Some conservative denials are intentional.** Security-critical ambiguity (e.g., unverified authority claims, Grey-tier file access) produces `clarify` or `escalate` rather than a potentially incorrect `allow`.

---

## Deployment

### Option A — Docker (local)

```bash
docker build -t gaggia-agent .
docker run --env-file .env -p 8000:8000 gaggia-agent
open http://localhost:8000
```

### Option B — Render

1. Push the repo to GitHub.
2. Create a new **Web Service** on [Render](https://render.com).
3. Select **Docker** as the environment (Render auto-detects the `Dockerfile`).
4. Add environment variables in the Render dashboard (see the table above).
5. Deploy. Render builds the image and starts the service.
6. Open the Render-provided URL.

A `render.yaml` blueprint is included for infrastructure-as-code setup.

**Important:**
- Never commit `.env`. Set API keys via Render's environment variable dashboard.
- If `NEO4J_*` vars are absent, the app uses the in-memory graph fallback automatically.
- If `ANTHROPIC_API_KEY` is absent, the deterministic fallback is used (evaluation still passes).
- On Render's free tier, `CHROMA_PERSIST_PATH=/tmp/chroma_db` is recommended — the volume is ephemeral and will be rebuilt on each restart.

---

## Development Commands

```bash
# Tests
pytest -q

# Build policy index
python scripts/build_policy_index.py

# Run full evaluation suite
python scripts/run_eval.py --all

# Inspect full graph run for a single message
python scripts/inspect_graph.py

# Run agent from CLI
python -m gaggia_agent.main \
  --message "Can you get David Kim's work email?" \
  --trust-tier blue \
  --show-trace

# Check which backends are active
python scripts/check_backends.py
```

---

## Project Structure

```
gaggia_agent/
  agents/          router_agent, policy_reasoning_agent, response_agent
  llm/             Anthropic client with deterministic fallback
  nodes/           LangGraph nodes: guards, retriever, executor, filter, logger
  policy/          Policy markdown, ChromaDB index, Neo4j / in-memory graph
  evaluation/      Eval framework, YAML scenarios, result reports
  state.py         AgentState TypedDict
  runner.py        run_agent() entrypoint
  graph.py         LangGraph StateGraph assembly

demo_api/          FastAPI backend (serves /api/* + React SPA in production)
demo_ui/           React Vite frontend (GaggiaAgent Policy Console)
tests/             pytest unit + integration tests
scripts/           CLI utilities
logs/              Decision audit log (decisions.jsonl, gitignored)
```

---

## Models Used

**Runtime LLM:**
- Hosted demo: Anthropic Claude Sonnet 4 (`claude-sonnet-4-20250514`)
- Local tests / evaluation: deterministic fallback — works without an API key

**Embedding / retrieval:**
- Section retrieval: `sentence-transformers/all-MiniLM-L6-v2` via ChromaDB `DefaultEmbeddingFunction` (local, no API key required)
- Lexical fallback: token-overlap scoring when ChromaDB or embeddings are unavailable
- High-risk rule graph: Neo4j if credentials are configured; in-memory graph fallback otherwise

The system is model-agnostic at the architecture level: LLM agents produce structured JSON proposals, while deterministic guards enforce trust tier, tool authorization, and output filtering independently of any model.

---

## AI Tool Usage

I used ChatGPT and Cursor / Claude Code to brainstorm the architecture, generate implementation prompts, debug retrieval precision, build the evaluation suite, and polish the demo UI. All behaviour was validated with local tests, the evaluation scenario suite, and manual demo runs. Policy enforcement logic, guard conditions, and test assertions were written and reviewed by me.
