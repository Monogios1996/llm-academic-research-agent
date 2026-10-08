# First full live workflow run

Date: 2026-10-08
GitHub Actions run: 37742577881
Trigger: manual workflow dispatch
Branch: main
Commit: 30460b5069470ac1dfc2719d26afb1136feea302

## Result

The first complete hosted workflow run succeeded and reached the intended
human-approval boundary.

Observed outcome:

```
Status: awaiting_approval
Model: openai/gpt-oss-20b:fastest
Validated evidence items: 9
```

The live Planner generated three subtasks. For each subtask the workflow
retrieved records from Crossref and OpenAlex, ranked the results, generated
LLM summaries through Hugging Face, validated the evidence, and accepted the
subtask before advancing. No retry or re-planning path was needed in this run.

The final audit trail ended with:

```
All subtasks validated; human approval required before export.
```

## Integration finding

Reviewing the final package revealed one duplicate scholarly work across two
different subtasks:

```
Agent Planning Benchmark: A Diagnostic Framework for Planning Capabilities in LLM Agents
DOI: 10.48550/arxiv.2606.04874
```

Per-subtask deduplication was already working, but the final accumulated
evidence list did not deduplicate records reused across different subtasks.

## Remediation

Global evidence deduplication was added at the final aggregation boundary.
The change preserves per-subtask validation requirements while ensuring the
final package contains each scholarly work only once. When a duplicate work is
encountered, the stronger evidence instance is retained deterministically using
relevance score, metadata completeness, and summary length.

Dedicated unit/integration tests were added for this behaviour. A subsequent
full live run is required to verify the change against live provider output.
