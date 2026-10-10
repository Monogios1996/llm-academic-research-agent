# Final system overview

## Purpose

The prototype is an LLM-powered academic research and information-gathering
planning agent. It accepts a broad research goal, decomposes it into searchable
sub-questions, retrieves structured scholarly metadata, ranks and summarises
evidence, validates the result, and stops for explicit human approval before
export.

The implementation deliberately keeps the intelligent-agent behaviour central
and the user interface thin.

## Final architecture

The system is organised around six logical responsibilities:

1. **Orchestrator / Supervisor** — LangGraph controls state, routing, bounded
   retries, bounded re-planning, completion, and the human-approval boundary.
2. **Planner** — an LLM converts the high-level goal into at least two focused,
   searchable research subtasks.
3. **Academic Retrieval** — Crossref and OpenAlex provide structured scholarly
   metadata.
4. **Processing / Ranking** — deterministic deduplication and lexical relevance
   scoring reduce duplicates and weak matches before model summarisation.
5. **Evidence Summarisation and Validation** — the LLM produces concise
   evidence summaries under grounding constraints; deterministic safeguards and
   the validator check traceability, sufficiency, and relevance.
6. **Persistence / Export** — LangGraph state is checkpointed to SQLite, run
   metadata is recorded as JSON telemetry, and approved evidence can be exported
   to Markdown, JSON, and CSV.

The primary model route uses Hugging Face Inference Providers. When explicitly
enabled, Ollama with `qwen3:4b` acts as a local fallback after a
provider-specific failure.

## Control flow

```text
Research goal
    |
    v
Planner (LLM)
    |
    v
Subtask selection
    |
    v
Crossref + OpenAlex retrieval
    |
    v
Deduplication + relevance ranking
    |
    v
Grounded evidence summarisation
    |
    v
Evidence validation
    |-----------------------------|
    | pass                        | fail
    v                             v
next subtask              targeted bounded retry
    |                             |
    |                         retry exhausted
    |                             v
    |                     bounded re-planning
    |                             |
    |                     unresolved -> fail
    v
Human approval boundary
    |
    | explicit approval only
    v
Markdown + JSON + CSV export
```

## State, persistence, and traceability

Each workflow run receives a unique run ID. When checkpointing is enabled, the
same ID is used as the LangGraph thread ID and workflow state is persisted in a
local SQLite database.

Completed runs also write structured JSON telemetry including start/end time,
duration, status, model provenance, fallback-call count, subtask information,
evidence count, and the audit trail. Token and cost figures are deliberately
left unavailable when the configured providers do not expose them consistently.

## Grounding safeguards

Several safeguards were added after live testing:

- records without an abstract bypass generative summarisation and receive a
  deterministic limitation statement;
- the summarisation prompt forbids unsupported named benchmarks, datasets,
  acronyms, metric names, and numeric values;
- generated summaries containing unsupported high-risk acronyms or numeric
  claims fall back to bounded source-abstract text;
- duplicate evidence is removed both within retrieval processing and across
  final multi-subtask aggregation;
- generic evaluation vocabulary is not allowed to dominate relevance ranking
  without topic-specific overlap.

These safeguards do not make hallucination impossible, but they make the
observed high-risk failure modes more visible and testable.

## Human-in-the-loop design

The graph ends successfully at `awaiting_approval`. Export is implemented
outside the graph and independently checks both workflow status and the explicit
approval flag. This prevents either the CLI or Streamlit layer from bypassing
the intended approval requirement.

The same approval path is exposed in the minimal Streamlit interface, where the
user can review the plan, evidence, traceability, summaries, and audit trail
before selecting **Approve & Export**.

## Testing and evaluation summary

The final automated suite contains **83 tests** covering domain models,
planning contracts, API normalisation, processing/ranking, summarisation,
validation, orchestration, failover, persistence, telemetry, approval/export,
and the Streamlit helper logic.

A fixed 12-case live evaluation set was also executed across clear, comparative,
broad, ambiguous, agent-specific, application, and sociotechnical research
questions. All **12/12 cases reached structural success (100%)**, exceeding the
predefined 90% target. Every case reached `awaiting_approval`, created at
least two subtasks, retained at least five evidence items, passed validation,
and achieved 100% traceability.

This is a structural reliability result, not proof that every retrieved source
or every generated summary is semantically perfect.

## Final demonstration

The final system can be demonstrated either through the CLI or a single-page
Streamlit interface. The Streamlit version intentionally adds no separate
backend or account system. It reuses the same tested workflow and shows:

- topic and optional objective input;
- plan/sub-questions;
- validated evidence;
- source identifiers and relevance scores;
- traceability;
- grounded summaries;
- run ID and persistence/log paths;
- audit trail;
- human approval and export.

The full browser path has been live-verified through successful Markdown, JSON,
and CSV export.
