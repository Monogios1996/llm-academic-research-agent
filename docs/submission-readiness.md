# Submission-readiness checklist

## Core system

- [x] High-level research goal accepted.
- [x] LLM Planner decomposes the goal into searchable subtasks.
- [x] Crossref and OpenAlex retrieval implemented.
- [x] Deterministic deduplication and relevance ranking implemented.
- [x] Grounded evidence summarisation safeguards implemented.
- [x] Evidence validation implemented.
- [x] Bounded retry and bounded re-planning implemented.
- [x] Hosted-model route with verified local Ollama fallback implemented.
- [x] Human approval enforced before export.
- [x] Markdown, JSON, and CSV export implemented.
- [x] SQLite LangGraph checkpoint persistence implemented.
- [x] Structured run IDs and JSON telemetry implemented.
- [x] Minimal Streamlit demonstration interface implemented and live-verified.

## Testing and evaluation

- [x] Automated unit/integration suite passing: **83 tests**.
- [x] GitHub Actions automated verification configured.
- [x] Live provider/integration evidence retained separately from mocked tests.
- [x] Genuine failures and remediation steps documented chronologically.
- [x] Fixed 12-case evaluation manifest implemented.
- [x] Full live evaluation completed: **12/12 structural passes (100%)**.
- [x] Predefined structural reliability target of 90% exceeded.
- [x] Evaluation limitation stated: structural success is not equivalent to
      semantic perfection.

## Documentation

- [x] README includes purpose, architecture, installation, configuration,
      execution, evaluation, testing, and Streamlit instructions.
- [x] Final system overview written.
- [x] Critical evaluation and known limitations written.
- [x] Orchestration implementation note retained.
- [x] Local-fallback design note updated to final verified state.
- [x] Human-approval/export note updated with browser verification.
- [x] Evidence directory indexed.

## Demonstration evidence

Recommended final evidence to use in the assessment presentation:

1. automated test result showing the final passing suite;
2. full 12-case evaluation summary showing 12/12 and the 90% target met;
3. Streamlit evidence page showing plan/evidence and the human-approval
   boundary;
4. Streamlit success state showing approved Markdown/JSON/CSV export;
5. one concise failure/remediation example, preferably the unsupported
   summarisation or SQLite serialization issue.

The chronological GitHub evidence files remain the authoritative development
record; screenshots should support that record rather than replace it.

## Remaining before submission

- [ ] Perform one final local `git pull` and `pytest -q` after documentation
      cleanup.
- [ ] Confirm the repository working tree is clean.
- [ ] Select/crop the clearest screenshots for the presentation.
- [ ] Confirm the University's required AI-use declaration wording and apply it
      accurately. The implementation used substantial AI assistance, so the
      declaration must follow the module/university rules rather than claiming
      unaided authorship.
- [ ] Prepare the maximum-10-slide presentation.
- [ ] Prepare the matching presentation transcript.

The presentation and transcript are intentionally left until the repository and
evidence package are final.
