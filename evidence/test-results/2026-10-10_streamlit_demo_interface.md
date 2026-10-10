# Minimal Streamlit demonstration interface

Date: 2026-10-10

## Scope decision

The final interface is intentionally limited to a single Streamlit page because
the assessment focuses on the intelligent-agent design, implementation,
testing, and critical evaluation rather than production web-development
features.

The interface therefore reuses the existing tested workflow and does not
introduce a separate backend, authentication layer, user accounts, multi-page
navigation, or other non-essential features.

## Implemented interface

The page provides:

- a research-topic input;
- an optional research-objective input;
- a **Run Research Agent** button;
- visible run status and run ID;
- model/fallback provenance;
- the generated research plan;
- validated evidence with source, identifier, relevance, traceability, and
  grounded summary;
- the workflow audit trail;
- the SQLite checkpoint path and structured run-log path;
- an **Approve & Export** button only after the workflow reaches
  `awaiting_approval`.

The approval button calls the existing guarded export layer, so the UI cannot
bypass the same human-approval requirement enforced by the CLI.

## Automated verification

Two unit tests cover model-provenance labelling in the demonstration layer,
including the hosted-only and hosted-to-local fallback cases.

Latest GitHub Actions result after adding the interface:

```
83 passed in 2.41s
```

The interface itself still requires a local browser-based smoke test before it
is treated as live-verified demonstration evidence.


## Successful browser smoke verification

The Streamlit interface was launched locally and a full research workflow was
completed through the browser.

The rendered page showed:

- validated academic evidence in expandable sections;
- source, identifier, relevance score, traceability, and grounded summary;
- the workflow audit trail;
- the explicit human-approval notice;
- the **Approve & Export** control only after the workflow reached the approval
  boundary.

This confirms that the browser interface exposes the existing agent workflow
without bypassing the human-in-the-loop design. The remaining UI verification
step is to exercise the approval/export button once and confirm that the
existing guarded export layer creates the three expected output formats.
