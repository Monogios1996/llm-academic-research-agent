# Summarisation and validation unit test run

Date: 2026-10-06
Scope: shared models, planning, academic retrieval, processing/ranking,
LLM evidence summarisation, and evidence validation.

## Test method

The repository source and test files were executed in an isolated Python
verification environment with the project `src/` directory on `PYTHONPATH`.

Command:

```
PYTHONPATH=src pytest -q
```

## Result

```
.........................                                                [100%]
25 passed in 0.19s
```

## New behaviour covered in this stage

- grounded evidence-summary creation through an injected LLM gateway
- rejection of empty LLM summary output
- bounded summary length
- preservation of relevance scores and source traceability
- evidence-count validation
- traceability-ratio validation
- relevance-threshold validation
- targeted remediation routing to either retrieval or processing

## Limitations of this test run

The LLM is represented by a deterministic test double. These tests therefore
verify application logic and failure handling, but do not yet demonstrate a
live Hugging Face model call. Academic API behaviour is also mocked in unit
tests; live Crossref/OpenAlex integration will be tested separately.

End-to-end orchestration, bounded retries, persistence, human approval, and
export remain outstanding.
