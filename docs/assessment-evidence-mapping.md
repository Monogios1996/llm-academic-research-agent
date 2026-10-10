# Assessment evidence mapping

This note maps the implemented project evidence to the main assessment areas so
the final presentation can stay focused and avoid repeating repository detail.

## Code quality and structure

Evidence:

- clear package separation across planning, retrieval, processing,
  summarisation, validation, orchestration, persistence, telemetry, export, and
  UI;
- Pydantic domain models at logical boundaries;
- provider-independent LLM gateway and explicit failover;
- deterministic processing kept separate from generative stages;
- focused comments that explain design intent rather than restating code;
- final automated suite: **83 passing tests**.

Primary repository locations:

- `src/research_agent/`
- `tests/`
- `.github/workflows/tests.yml`

## Meeting the proposed design

Implemented proposal elements include:

- high-level goal decomposition into searchable subtasks;
- Plan-and-Execute control flow;
- Crossref and OpenAlex academic retrieval;
- deterministic filtering/ranking before LLM summarisation;
- traceability and evidence validation;
- bounded retry and bounded re-planning;
- hosted inference with local fallback;
- SQLite persistence and run metadata;
- explicit human approval before export;
- Markdown/JSON/CSV outputs;
- minimal Streamlit demonstration interface.

Primary narrative:

- `docs/final-system-overview.md`
- `docs/orchestration-implementation.md`
- `docs/local-fallback.md`
- `docs/approval-export.md`

## Intelligent-agent concepts and final demonstration

Concepts visibly demonstrated by the implementation:

- goal-directed planning;
- specialised logical responsibilities;
- shared state and controlled transitions;
- environment/tool interaction through scholarly APIs;
- validation feedback;
- bounded autonomy;
- resilience/failover;
- persistence;
- human-in-the-loop control.

The Streamlit interface provides a simple demonstration surface without hiding
the workflow behaviour behind a complex front end.

Primary evidence:

- `src/research_agent/orchestration.py`
- `src/research_agent/streamlit_app.py`
- `evidence/test-results/2026-10-10_streamlit_demo_interface.md`

## Critical commentary and design decisions

Strongest critical-evaluation examples:

- choosing LangGraph for inspectable bounded routing rather than a freer-form
  multi-agent framework;
- using structured scholarly APIs rather than general web scraping;
- separating deterministic ranking from LLM summarisation;
- adding local failover after real hosted-provider failures;
- moving from prompt-only grounding to deterministic safeguards after a real
  hallucination;
- treating live integration failures as evidence rather than hiding them;
- keeping the final UI deliberately minimal for the project scope.

Primary narrative:

- `docs/critical-evaluation.md`
- `docs/development-timeline.md`
- chronological remediation records under `evidence/test-results/`

## Testing and outcomes

Evidence:

- automated suite: **83 passing tests**;
- live hosted-provider verification;
- controlled hosted-to-local fallback verification;
- persistence/checkpoint verification;
- browser approval/export verification;
- fixed 12-case live evaluation: **12/12 structural passes (100%)**, exceeding
  the predefined 90% target.

The 100% result is reported only as structural workflow success, not as a claim
of perfect semantic research accuracy.

Primary evidence:

- `evaluation/cases.json`
- `src/research_agent/evaluation.py`
- `evidence/test-results/2026-10-10_end_to_end_evaluation_harness.md`
- `evidence/test-results/2026-10-10_sqlite_checkpoint_and_run_telemetry.md`

## Sources, acknowledgement, and integrity

External technologies and APIs are acknowledged in the README and design
documentation. Academic references from the Unit 6 proposal should be reused
where they support final design commentary.

Before final submission, the module-specific rules on generative-AI assistance
must be checked and any required declaration must accurately acknowledge the
assistance used during implementation and documentation. No submission wording
should imply unaided authorship if that would be inaccurate.
