# LangGraph orchestration CI verification

Date: 2026-10-07
GitHub Actions run: 37588409993
Trigger: manual workflow dispatch
Branch: main
Verified commit: 40e562eec4a2392e7eac74a32a842db8e98f724b

## Purpose

This run verified the repository in a clean GitHub-hosted environment after
introducing LangGraph orchestration, bounded remediation, re-planning, and the
human-approval boundary.

## Environment observed in the CI log

- Python 3.11.16
- LangGraph 1.2.14
- Pydantic 2.13.5
- httpx 0.28.1
- pytest 9.1.1

Dependencies were installed from the repository's `requirements.txt`.

## Command

```
PYTHONPATH=src pytest -q
```

## Result

```
..............................                                           [100%]
30 passed in 0.35s
```

Checkout, Python setup, dependency installation, and the automated test step all
completed successfully.

## Behaviour covered

The suite covers models, planning, mocked academic retrieval,
processing/ranking, grounded summarisation, validation, and orchestration paths
for:

- successful progression to the human-approval boundary;
- targeted retrieval retry after validation failure;
- escalation of validation feedback to the Planner after retry exhaustion; and
- clean termination when retry and re-planning budgets are exhausted.

## Interpretation and limitations

This is reproducible CI evidence that the codebase installs and its 30 automated
tests pass in a clean Python 3.11 environment.

It is not yet evidence of a complete live system. LLM behaviour in the automated
tests is represented by deterministic test doubles and academic API responses
are mocked. Live Hugging Face/model integration, live Crossref/OpenAlex
execution, persistence, approval/export, and the final user-facing
demonstration remain separate implementation and evaluation stages.

The runner also reported a GitHub Actions warning about actions targeting
Node.js 20 being forced to Node.js 24. The warning is external to the Python
application and did not affect the successful test result.
