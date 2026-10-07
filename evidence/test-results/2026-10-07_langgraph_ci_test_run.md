# LangGraph orchestration CI test run

Date: 2026-10-07
Workflow: test-suite
Trigger: manual workflow_dispatch
GitHub Actions run: 37588409993
Commit tested: 40e562eec4a2392e7eac74a32a842db8e98f724b

## Environment

- GitHub-hosted Ubuntu 24.04 runner
- Python 3.11.16
- Pydantic 2.13.5
- httpx 0.28.1
- LangGraph 1.2.14
- pytest 9.1.1

## Command

```
pytest -q
```

with:

```
PYTHONPATH=src
```

## Result

```
..............................                                           [100%]
30 passed in 0.35s
```

## Scope verified

This CI run verifies the current automated tests for:

- Pydantic workflow and evidence models
- planner output validation and bounded re-planning feedback
- mocked Crossref and OpenAlex metadata normalisation
- retrieval failure handling
- deterministic deduplication and relevance ranking
- grounded LLM summarisation logic using deterministic test doubles
- evidence sufficiency, traceability, and relevance validation
- LangGraph orchestration
- targeted retrieval retry
- bounded escalation to the Planner
- clean termination when retry and re-planning budgets are exhausted
- progression to the human-approval boundary when all subtasks validate

## Interpretation and limitations

The full automated suite passed in a clean GitHub-hosted environment after
installing dependencies directly from `requirements.txt`. This is stronger
evidence than a local-only test because it demonstrates that the repository can
be checked out and its automated tests executed reproducibly on Python 3.11.

The run does not yet prove live Hugging Face inference, live Crossref/OpenAlex
integration, SQLite persistence, export behaviour, or the final user interface.
Those are separate implementation and testing stages.
