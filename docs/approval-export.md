# Human approval and export implementation

The Unit 6 design requires a human decision before the final consequential
action. The implementation therefore keeps workflow execution and export as two
separate responsibilities.

## Boundary

A successful LangGraph run terminates with:

```
status = awaiting_approval
```

At that point the plan, unique evidence items, summaries, and audit trail can be
reviewed. The workflow itself never writes the final research package.

The export layer performs two independent guards:

1. the workflow state must be `awaiting_approval`;
2. the caller must supply an explicit approval decision.

If either condition is missing, export raises `ExportApprovalError` before any
files are created.

## CLI behaviour

Normal CLI execution remains non-consequential and stops at the approval
boundary. To exercise the human-in-the-loop path locally, run with
`--prompt-for-approval`. The CLI displays the complete result first and only
then asks the user whether export should proceed.

A negative or blank response creates no files. An affirmative response calls the
guarded export layer.

## Export formats

After approval, the same validated package is written in three forms:

- Markdown for human-readable inspection and submission evidence;
- JSON for structured reproducibility and later processing;
- CSV for tabular evidence analysis.

The JSON output also records UTC export time, model identifier, evidence count,
pre-export workflow status, the human-approval flag, the research goal, plan,
evidence, and audit trail.

Generated files are written under `outputs/` by default and are ignored by Git
so local approved packages are not accidentally committed.

## Testing

Automated tests verify that:

- export is refused without explicit approval;
- export is refused from a failed/non-approval workflow state;
- approved export creates Markdown, JSON, and CSV outputs with expected
  traceability and metadata.

This separation makes the approval requirement enforceable in code rather than
only described in documentation.


## Streamlit behaviour

The minimal Streamlit demonstration reuses the same guarded export function as
the CLI. The **Approve & Export** control is shown only after the workflow
reaches `awaiting_approval`, and the export function still performs its own
status and approval checks.

A live browser smoke test verified the complete path from research input through
planning, retrieval, processing, summarisation, validation, review, explicit
approval, and creation of Markdown, JSON, and CSV files.
