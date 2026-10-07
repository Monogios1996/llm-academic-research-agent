# LLM Academic Research Agent

An LLM-powered academic research and information-gathering planning agent developed for the University of Essex Online **Intelligent Agents** module.

## Project status

The project is under active development. The prototype now implements planning, structured academic retrieval, deterministic processing/ranking, LLM-grounded summarisation, evidence validation, bounded LangGraph orchestration, and a live Hugging Face provider gateway. Persistence, approval/export, and the final demonstration interface remain to be completed.

Development is intentionally incremental so that Git history, tests, and execution evidence show how the prototype evolved and how identified issues were remediated.

## System overview

The system accepts a high-level academic research goal and coordinates six logical responsibilities:

1. **Orchestrator / Supervisor** – maintains workflow state, routing, bounded retries, re-planning, and termination.
2. **Planner** – decomposes the research goal into searchable sub-questions.
3. **Academic Retrieval** – retrieves scholarly metadata from Crossref and OpenAlex.
4. **Processing / Ranking** – normalises, deduplicates, and ranks retrieved evidence.
5. **Evidence Validator** – checks sufficiency, relevance, and source traceability.
6. **Storage / Export** – planned final stage for approved Markdown and machine-readable outputs.

Current control flow:

```text
Goal
  ↓
Planner (LLM)
  ↓
Crossref + OpenAlex retrieval
  ↓
Processing / Ranking
  ↓
LLM-grounded Summarisation
  ↓
Evidence Validation
  ├─ pass ───────────────→ next subtask / human approval
  ├─ retry ──────────────→ retrieval or processing
  └─ retries exhausted ─→ bounded re-planning → clean failure if unresolved
```

The workflow deliberately stops at **human approval** after all subtasks validate. Export is not performed automatically because the original design specifies approval before a consequential final action.

## Technical approach

- Python 3.11+
- LangGraph for explicit stateful orchestration
- Pydantic for validated domain and inter-agent data models
- Hugging Face Inference Providers for live LLM planning and summarisation
- Crossref and OpenAlex for structured scholarly metadata
- deterministic deduplication and lexical relevance ranking before LLM summarisation
- pytest for automated unit and workflow tests
- GitHub Actions for reproducible automated and live-provider verification

The LLM is accessed through a provider-independent gateway so that the Planner and Summariser do not depend directly on one provider client. Automated tests use deterministic test doubles so core application logic can be verified without consuming model credits or depending on network availability.

## Repository structure

```text
.
├── .github/workflows/     # automated tests and manual live-provider checks
├── src/research_agent/    # application source code
├── tests/                 # unit and orchestration tests
├── docs/                  # design and implementation notes
├── evidence/              # test results, example runs, logs, screenshots
├── .env.example           # credential names only; never real secrets
├── requirements.txt
└── README.md
```

## Installation

Create and activate a Python 3.11+ virtual environment, then install dependencies:

```bash
python -m pip install -r requirements.txt
```

The source directory must be on `PYTHONPATH` when running directly from the repository.

## Live provider configuration

Set these environment variables before live execution:

- `HF_TOKEN` – Hugging Face fine-grained token with permission to make Inference Providers calls.
- `HF_MODEL` – optional model override. The development default is `openai/gpt-oss-20b:fastest`.
- `OPENALEX_API_KEY` – OpenAlex API key.
- `CROSSREF_EMAIL` – recommended identification address for Crossref polite API access.

An example containing placeholder values is provided in `.env.example`. Real credentials must never be committed to the repository.

## Live provider smoke test

Before running a complete multi-step agent workflow, verify each external provider independently:

```bash
PYTHONPATH=src python -m research_agent.live_smoke
```

The smoke test performs one small Hugging Face generation and one-record searches against Crossref and OpenAlex. This deliberately limits model/API usage while establishing that credentials, connectivity, and response parsing are working.

A manual GitHub Actions workflow named **live-provider-smoke** provides the same check in a clean hosted environment after the repository secrets have been configured.

## Running the live research agent

After the provider smoke test succeeds:

```bash
PYTHONPATH=src python -m research_agent.main --topic "LLM planning agents in academic research"
```

An optional objective can also be supplied:

```bash
PYTHONPATH=src python -m research_agent.main \
  --topic "LLM planning agents in academic research" \
  --objective "Identify current architectures, evaluation approaches, and limitations."
```

The CLI displays the generated plan, validated evidence, concise grounded summaries, and the workflow audit trail. A successful run ends at `awaiting_approval`; no export is performed at this stage.

## Testing status

Recorded development evidence is stored under `evidence/test-results/`.

The automated suite covers:

- Pydantic state and message validation;
- planner output validation and re-planning feedback;
- mocked Crossref/OpenAlex normalisation and failure handling;
- deterministic deduplication and ranking;
- LLM summarisation boundaries;
- evidence validation and targeted remediation;
- LangGraph success, retry, re-planning, and failure routes;
- live dependency wiring without making network calls.

The LangGraph milestone was verified in GitHub Actions with **30 tests passing**. After adding the live-provider gateway, runtime configuration, CLI wiring, and smoke-test infrastructure, the full automated suite was re-run successfully with **38 tests passing**. Live-provider verification remains intentionally separate from unit testing so mocked tests are not presented as evidence of live external execution.

## Academic integrity and acknowledgements

External libraries, frameworks, models, APIs, and academic sources used by the implementation are acknowledged here and, where appropriate, in code commentary.

Code comments focus on **why** design and implementation choices were made rather than simply paraphrasing what individual lines do. This keeps implementation decisions traceable to the submitted design and the assessment requirements.

Current external technologies and documentation include:

- LangGraph / LangChain documentation: https://docs.langchain.com/oss/python/langgraph/overview
- Hugging Face Inference Providers: https://huggingface.co/docs/inference-providers/
- Crossref REST API: https://www.crossref.org/documentation/retrieve-metadata/rest-api/
- OpenAlex API: https://developers.openalex.org/api-reference/introduction
- Pydantic: https://docs.pydantic.dev/
- httpx: https://www.python-httpx.org/
- pytest: https://docs.pytest.org/

Academic references from the Unit 6 design proposal will be carried into the final submission documentation where they support design and implementation decisions.
