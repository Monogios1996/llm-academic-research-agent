# Development timeline

This timeline summarises the main implementation milestones and genuine
integration findings preserved in the repository history and evidence records.

## 5 October 2026 — foundation

- Established the Python project structure and shared Pydantic domain models.
- Added initial planning, retrieval, and processing foundations.
- Created the first automated test suite and GitHub Actions workflow.
- Initial recorded automated state: 17 tests.

## 6 October — summarisation and validation

- Added evidence summarisation and validation boundaries.
- Expanded deterministic testing around the research workflow.
- Automated suite increased through the mid-20s.

## 7 October — LangGraph orchestration and first live provider work

- Implemented bounded Plan-and-Execute orchestration with LangGraph.
- Added retry, re-planning, clean failure, and human-approval termination paths.
- Automated orchestration milestone reached 30 passing tests.
- Live Hugging Face smoke testing exposed provider/model integration failures,
  including unsupported-model and account-credit conditions.
- These were retained as integration evidence rather than hidden.

## 8 October — full live workflow, deduplication, export, and local fallback

- Achieved the first full live hosted workflow ending at
  `awaiting_approval`.
- A duplicate paper appeared across subtasks, leading to final aggregation
  deduplication.
- Added guarded human-approved Markdown/JSON/CSV export.
- Began local fallback integration with Ollama and `qwen3:4b`.
- The first local route exposed empty/unusable output, motivating the native
  Ollama chat adapter and non-thinking controls.

## 9 October — local Planner contract remediation

- Local Planner output failed the required JSON contract during controlled
  hosted-to-local failover testing.
- Added bounded JSON recovery and then Ollama JSON Schema constraints.
- A later live run produced too few subtasks, leading to an explicit minimum of
  two subtasks in the Planner contract.
- Further malformed output led to stronger structured-schema generation.
- The controlled failover path then completed with a valid two-subtask plan.

## 10 October — grounding, relevance, persistence, evaluation, and final demo

### Grounded summarisation

- Local summaries initially exposed reasoning-style preambles; structured local
  summary output removed these.
- A live approved export revealed an unrelated generic dataset result and a
  truncated sentence.
- Added topic-anchor relevance penalties, threshold filtering, and sentence-safe
  truncation.
- A later summary introduced unsupported named benchmarks; added deterministic
  no-abstract handling and high-confidence grounding guards.
- A Pydantic `HttpUrl` type error was exposed only in live execution and was
  fixed with explicit text normalisation.

### Persistence and observability

- Added unique run IDs, SQLite LangGraph checkpoints, and structured JSON run
  telemetry.
- The first live persistence run failed because `AcademicRecord` was not
  msgpack-serialisable.
- Updated the checkpoint serializer and added regression coverage using real
  Pydantic domain objects.
- Repeat live verification succeeded.

### Broader evaluation

- Added a fixed 12-case evaluation manifest spanning clear, comparative, broad,
  ambiguous, agent-specific, application-domain, and sociotechnical topics.
- A three-case smoke evaluation passed 3/3.
- The full live evaluation passed 12/12 structurally (100%), exceeding the
  predefined 90% target.
- The result is explicitly treated as structural reliability rather than proof
  of perfect semantic accuracy.

### Demonstration interface

- Added a deliberately minimal single-page Streamlit interface.
- Live browser verification confirmed plan/evidence display, the human-approval
  boundary, and approved Markdown/JSON/CSV export.
- Feature development was then treated as complete for the university-project
  scope.

## Final automated state

The final automated suite contains **83 passing tests** covering models,
planning contracts, retrieval, processing, grounded summarisation, validation,
orchestration, failover, persistence, telemetry, evaluation logic, export
guards, and the demonstration interface helper behaviour.

The chronological files under `evidence/test-results/` contain the detailed
failure/remediation evidence behind this summary.
