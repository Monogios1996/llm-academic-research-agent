# Live-integration code CI verification

Date: 2026-10-07
GitHub Actions run: 37589810711
Trigger: push
Branch: main
Verified commit: 3cf00665b6cba6c330619a5c1c16c6c1b1de96a4

## Purpose

This run verifies the codebase after adding the Hugging Face Inference
Providers gateway, environment-based live configuration, Crossref client
identification, live dependency wiring, the executable CLI, and the manual
live-provider smoke-test workflow.

## Automated result

```
......................................                                   [100%]
38 passed in 0.48s
```

The test suite passed in GitHub Actions on Python 3.11.

## What this run proves

The automated suite now verifies:

- Hugging Face request construction and response parsing with mocked HTTP;
- provider HTTP failure handling;
- environment configuration and missing-secret handling;
- Crossref and OpenAlex client behaviour under mocked responses;
- live dependency wiring without performing network calls;
- all previously implemented models, planning, ranking, summarisation,
  validation, retry, re-planning, and orchestration tests.

## What this run does not prove

This CI run does not claim that Hugging Face, Crossref, or OpenAlex were reached
live. External provider execution is deliberately separated into the
`live-provider-smoke` workflow so network and credential evidence cannot be
confused with mocked automated tests.

The next verification milestone is to configure repository secrets and run the
manual live-provider smoke test.
