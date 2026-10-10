# Grounded summarisation remediation

Date: 2026-10-10

## Live finding

A repeat live fallback run passed relevance filtering and sentence-safe
truncation, but review identified a grounding defect in one LLM-generated
summary. The generated summary introduced named benchmark acronyms that were
not present in the retrieved source evidence.

A second weaker case also inferred likely benchmark content from a title when
the record had no abstract.

Because the system is intended to produce traceable academic evidence, these
were treated as genuine output-quality defects rather than acceptable model
variation.

## Remediation

The evidence summariser now applies three safeguards:

1. **No-abstract deterministic path.** When a retrieved record has no abstract,
   the LLM is not called. The system returns a deterministic limitation
   statement explaining that specific methods, metrics, datasets, findings,
   and conclusions cannot be established from the retrieved evidence.

2. **Stronger grounding instruction.** For records with abstracts, the prompt
   explicitly forbids introducing named benchmarks, datasets, models,
   organisations, acronyms, metric names, or numeric values unless they are
   present in the supplied bibliographic evidence.

3. **High-confidence deterministic guard.** Generated summaries are checked for
   acronyms and numeric claims that do not occur in the retrieved record. If an
   unsupported high-risk term is detected, the generated text is discarded and
   replaced by a bounded extractive summary from the source abstract.

The guard is intentionally conservative rather than attempting to solve general
semantic hallucination detection. This keeps the behaviour inspectable and
testable while directly addressing the observed failure mode.

## Automated verification

New tests cover:

- bypassing the LLM and returning a limitation statement when no abstract is
  available;
- rejecting generated summaries that introduce unsupported benchmark acronyms;
- rejecting generated summaries that introduce unsupported numeric claims;
- the strengthened grounding constraints in the summarisation prompt.

Latest verified GitHub Actions result after the substantive change:

```
70 passed in 0.49s
```

A repeat live fallback run is required to confirm the behaviour under local
Qwen3 inference before this remediation is considered fully verified.
