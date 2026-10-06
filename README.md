# LLM Academic Research Agent

An LLM-powered academic research and information-gathering planning agent developed for the University of Essex Online **Intelligent Agents** module.

## Project status

The project is under active development. The current prototype implements the main planning, retrieval, processing, summarisation, validation, and orchestration stages from the Unit 6 design proposal. Human approval, export, persistence, live model integration, and the final demonstration interface remain to be completed.

Development is intentionally incremental so that Git history, tests, and execution evidence show how the prototype evolved and how identified issues were remediated.

## System overview

The system accepts a high-level academic research goal and coordinates six logical responsibilities:

1. **Orchestrator / Supervisor** – maintains workflow state, routing, bounded retries, and termination.
2. **Planner** – decomposes the research goal into searchable sub-questions.
3. **Academic Retrieval** – retrieves scholarly metadata from structured academic APIs.
4. **Processing / Ranking** – normalises, deduplicates, and ranks retrieved evidence.
5. **Evidence Validator** – checks sufficiency, relevance, and source traceability.
6. **Storage / Export** – planned final stage for approved Markdown and machine-readable outputs.

Current control flow:

```text
Goal
  ↓
Planner
  ↓
Academic Retrieval
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

The prototype currently stops at **human approval** after all subtasks validate. Export is deliberately not performed automatically because the original design specifies approval before a consequential final action.

## Technical approach

- Python 3.11+
- LangGraph for explicit stateful orchestration
- Pydantic for validated domain and inter-agent data models
- Crossref and OpenAlex for structured scholarly metadata
- deterministic deduplication and lexical relevance ranking before LLM summarisation
- pytest for automated unit and workflow tests
- GitHub Actions for reproducible test execution

The LLM is accessed through a provider-independent gateway so that a hosted Hugging Face model can be used without coupling the Planner or Summariser to one provider. Unit tests use deterministic test doubles so application logic can be tested without consuming model credits or depending on network availability.

## Repository structure

```text
.
├── .github/workflows/     # reproducible CI test workflow
├── src/research_agent/    # application source code
├── tests/                 # unit and orchestration tests
├── docs/                  # design and implementation notes
├── evidence/              # test results, example runs, logs, screenshots
├── requirements.txt
└── README.md
```

## Testing status

Recorded development evidence is stored under `evidence/test-results/`.

The first test run covered models, planning, mocked academic retrieval, and processing/ranking. A later run extended coverage to grounded summarisation and evidence validation. LangGraph orchestration tests have now been added to cover successful completion, targeted retry, bounded re-planning, and clean failure; CI verification of this new stage is the next execution checkpoint.

## Running the project

The final runnable interface has not yet been implemented. The current codebase is a development prototype and should not yet be treated as the final submission package. Complete installation, configuration, model credentials, and execution instructions will be added once live integration and the interface are implemented.

## Academic integrity and acknowledgements

External libraries, frameworks, models, APIs, and academic sources used by the implementation will be acknowledged in the final README and, where appropriate, in code commentary.

Code comments focus on **why** design and implementation choices were made rather than simply paraphrasing what individual lines do. This is intended to keep implementation decisions traceable to the submitted design and the assessment requirements.

Current external technologies include:

- LangGraph / LangChain documentation: https://docs.langchain.com/oss/python/langgraph/overview
- Crossref REST API: https://www.crossref.org/documentation/retrieve-metadata/rest-api/
- OpenAlex API: https://developers.openalex.org/api-reference/introduction
- Pydantic: https://docs.pydantic.dev/
- httpx: https://www.python-httpx.org/
- pytest: https://docs.pytest.org/
