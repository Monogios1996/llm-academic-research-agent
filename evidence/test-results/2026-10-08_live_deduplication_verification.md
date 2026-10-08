# Full live workflow after global deduplication

Date: 2026-10-08
GitHub Actions run: 37765632457
Trigger: manual workflow dispatch
Branch: main
Commit: b0f48066867365a5f56805f7d19edf6cd3060d74

## Result

The live workflow completed successfully on the post-deduplication code and
stopped at the intended human-approval boundary.

Observed outcome:

```
Status: awaiting_approval
Model: openai/gpt-oss-20b:fastest
Validated evidence items: 8
```

The audit trail confirmed that a cross-subtask duplicate was removed during
final aggregation:

```
Accepted evidence for subtask q3. Removed 1 duplicate evidence item(s) during final aggregation.
All subtasks validated; human approval required before export.
```

The earlier live run returned nine accumulated evidence items and exposed one
duplicate DOI across different subtasks. This verification run returned eight
unique items, demonstrating that the remediation works against live provider
output as well as deterministic tests.
