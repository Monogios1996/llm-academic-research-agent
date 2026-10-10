# Local summariser structured-output remediation

Date: 2026-10-10

## Live finding

A full controlled hosted-to-local fallback workflow completed successfully and
reached the required human-approval boundary. The local fallback was used for
the Planner and all six evidence summaries.

Functional execution passed, but several local Qwen3 summaries included
instruction-restatement or reasoning-like preamble such as "We are given..." or
"Hmm, the user wants me to..." before the actual evidence summary. Because the
summariser applies a bounded character limit, that extra text also caused some
useful summaries to be truncated mid-sentence.

The run was therefore treated as a functional success but not as acceptable
final-output quality for approval/export.

## Remediation

For evidence-summarisation prompts only, the local Ollama gateway now:

- supplies a JSON Schema through Ollama's native `format` field;
- requires exactly one non-empty `summary` string;
- adds a local-only instruction to place the final evidence summary in that
  field with no analysis or preamble;
- parses the structured response and returns only the `summary` value to the
  existing `EvidenceSummariser`.

Planner structured output and ordinary plain-text local calls remain
independent. The existing evidence prompt continues to restrict summaries to
the supplied bibliographic metadata and abstract.

## Automated verification

Two tests were added covering:

- the structured summary schema and extraction of only the final summary text;
- rejection of an empty structured summary.

Latest GitHub Actions result:

```
62 passed in 0.49s
```

## Live verification

The repeat full controlled fallback workflow completed successfully after the
remediation.

Observed result:

- workflow status: `awaiting_approval`;
- local fallback enabled with `qwen3:4b`;
- seven fallback calls in total (one Planner call plus six summary calls);
- two valid research subtasks;
- five evidence items after final cross-subtask deduplication;
- both subtask validation stages passed;
- the workflow stopped at the human-approval boundary with no export performed;
- the displayed summaries began directly with evidence-focused academic content
  and no longer contained the earlier instruction-restatement or
  reasoning-like preamble.

The audit trail also confirmed that one duplicate evidence item was removed
during final aggregation.

This verifies the structured-output remediation under live local inference.
