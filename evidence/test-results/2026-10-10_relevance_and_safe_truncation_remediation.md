# Relevance filtering and safe-summary remediation

Date: 2026-10-10

## Live finding

The approval/export verification proved that the full workflow could reach the
human-approval boundary and create Markdown, JSON, and CSV outputs. Review of
that run identified two output-quality issues that should be corrected before
using a final showcase export:

1. a Crossref result about DIARETDB1/KAGGLE performance metrics was ranked for
   an LLM-planning benchmark sub-question even though it was from an unrelated
   application domain;
2. an otherwise useful FlowBench summary was cut off mid-sentence by the
   character limit.

These were treated as relevance and presentation-quality defects rather than
failures of the orchestration or approval/export mechanisms.

## Remediation

### Relevance

Deterministic relevance scoring now distinguishes generic evaluation vocabulary
such as `metrics`, `datasets`, `performance`, and `benchmarks` from more
query-specific anchor terms. A record that matches only generic vocabulary and
has no overlap with the sub-question's domain anchors receives a conservative
penalty.

The processing stage now also applies the validator's configured minimum
relevance threshold before LLM summarisation. This avoids spending model calls
on records already known to be too weak and allows the existing bounded
retrieval/re-planning logic to recover when filtering leaves too little
evidence.

### Summary truncation

The summariser prompt now asks for complete sentences within the configured
character limit. If a provider still returns an overlong response, deterministic
post-processing keeps the last useful complete sentence that fits. When no
complete sentence boundary is available, truncation occurs at a nearby word
boundary and is marked explicitly with an ellipsis instead of returning a
broken fragment.

## Automated verification

New tests cover:

- penalising an unrelated generic dataset/metrics match;
- filtering records below the configured relevance threshold;
- rejection of an invalid relevance threshold;
- preserving a complete sentence during truncation;
- explicit ellipsis fallback when no sentence boundary fits;
- the updated summariser prompt constraint.

Latest GitHub Actions result:

```
67 passed in 0.66s
```

A repeat live fallback workflow is required to verify that irrelevant generic
dataset matches are filtered and that displayed summaries no longer end in
broken sentence fragments.
