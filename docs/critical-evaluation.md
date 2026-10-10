# Critical evaluation

## Overall assessment

The final prototype meets the core design goal: it behaves as a bounded,
inspectable academic research planning agent rather than a single unrestricted
LLM prompt. Planning, retrieval, deterministic processing, summarisation,
validation, persistence, and human-approved export are separated into explicit
responsibilities.

The strongest aspect of the implementation is not any individual model call
but the way deterministic controls constrain where the LLM is used.

## Design choices and trade-offs

### LangGraph instead of a free-form multi-agent framework

LangGraph was selected for explicit state transitions, conditional routing, and
bounded retry/re-planning behaviour. This made it easier to test the workflow
as a graph of responsibilities and to preserve an inspectable approval
boundary.

The trade-off is additional orchestration code compared with a simpler chain,
but that complexity directly supports the assignment's focus on intelligent
agents, planning, state, and controlled interaction.

### Structured scholarly APIs instead of web scraping or a vector database

Crossref and OpenAlex were used because they expose traceable academic metadata
and stable identifiers. This keeps retrieval explainable and reduces the risk
of presenting arbitrary web text as academic evidence.

A vector database could improve semantic retrieval at scale, but it would add
infrastructure beyond the needs of this prototype. The current deterministic
lexical ranker is easier to inspect and test, although it can miss semantically
relevant results when vocabulary differs.

### Hosted model with local fallback

The hosted Hugging Face route provides convenient live inference, while Ollama
reduces dependence on hosted quota or availability. This design became
important during development when provider failures and credit limitations were
encountered in live testing.

The fallback improves resilience but introduces local-runtime variability.
Qwen3 output required structured JSON constraints and non-thinking controls,
and one local Planner request timed out before a later repeat succeeded.

### Deterministic safeguards around generative summarisation

Live testing exposed unsupported benchmark names in one summary and inference
from title-only metadata in another. The final system therefore does not rely
on prompt wording alone. Missing abstracts receive deterministic limitation
statements, while suspicious unsupported acronyms or numeric claims trigger an
extractive abstract fallback.

This is deliberately conservative. It can reduce fluency and sometimes exposes
raw source formatting such as LaTeX commands, but grounded evidence is more
important than polished unsupported prose in an academic research tool.

### Human approval before export

The export action remains outside the graph and requires both
`awaiting_approval` state and explicit approval. This is stronger than a UI-only
confirmation because the export function itself enforces the boundary.

The cost is one additional interaction for the user, but that is appropriate
for a tool producing a research package that could influence later academic
work.

## Development failures that improved the system

The development record contains several genuine integration failures rather
than only successful final tests:

- hosted inference failures exposed quota/provider dependence;
- the first Ollama route produced unusable output and motivated the native API
  adapter and non-thinking controls;
- local Planner output violated the JSON contract, leading to schema-constrained
  structured output and a minimum-subtask contract;
- duplicate evidence in a full live run led to global aggregation
  deduplication;
- weak generic relevance matching admitted an unrelated dataset result,
  motivating domain-anchor penalties and threshold filtering;
- unsafe truncation produced incomplete summaries, leading to sentence-aware
  truncation;
- unsupported named benchmarks appeared in a generated summary, leading to
  grounding safeguards and deterministic no-abstract behaviour;
- a Pydantic `HttpUrl` caused a live type error in the grounding guard,
  leading to URL normalisation and a regression test;
- SQLite checkpointing initially failed on Pydantic `AcademicRecord` objects,
  leading to an appropriate serializer configuration and persistence tests with
  real domain objects.

These failures are useful evidence because they show the difference between
unit-level confidence and real integration behaviour.

## Evaluation

The automated suite reached **83 passing tests**.

The fixed live evaluation set contained 12 varied requests and achieved
**12/12 structural passes (100%)**, above the predefined 90% target. Structural
success required:

- `awaiting_approval` final state;
- at least two Planner subtasks;
- at least two retained evidence items;
- at least 75% traceability;
- passed final validation;
- no unhandled exception.

The result demonstrates reliable execution across the selected test set, but it
should not be interpreted as a semantic accuracy score. A source can be
traceable yet only partially relevant, and a grounded summary can still omit
useful context.

## Known limitations

The main remaining limitations are:

- relevance ranking is lexical rather than embedding-based and has no full
  stemming or semantic matching;
- Crossref/OpenAlex metadata quality varies, and some records have no abstract;
- grounding safeguards target observed high-risk failure modes rather than
  proving factual correctness of every sentence;
- local Ollama performance depends on the user's hardware and model state;
- provider token/cost usage is not recorded because it is not exposed
  consistently through the current gateways;
- the Streamlit interface is intentionally a demonstration layer, not a
  production application;
- evaluation focuses primarily on structural reliability, with qualitative
  semantic review still required.

## Future work

If the prototype were extended beyond the university-project scope, useful next
steps would be semantic/embedding retrieval, richer citation-level claim
verification, provider usage accounting, resumable user-facing checkpoint
recovery, and a larger manually judged evaluation corpus.

These are deliberately treated as future work rather than added to the current
submission, because the existing implementation is sufficient to demonstrate
the intended intelligent-agent concepts without unnecessary production
complexity.
