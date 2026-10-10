# Fixed end-to-end evaluation harness

Date: 2026-10-10

## Purpose

The Unit 6 design proposed evaluating the prototype across more than a single
showcase request and set a target of at least 90% error-free execution.

A fixed manifest now contains 12 academic research requests spanning:

- clear domain questions;
- comparative evaluation questions;
- technically broad questions;
- application-domain questions;
- agent-specific questions;
- deliberately ambiguous requests;
- sociotechnical evaluation questions.

The manifest is stored at:

```
evaluation/cases.json
```

## Success criteria

A case is counted as structurally successful only when all of the following are
true:

- final workflow status is `awaiting_approval`;
- the Planner created at least two subtasks;
- at least two evidence items are retained;
- at least 75% of final evidence items are traceable;
- final evidence validation passed;
- no unhandled exception terminated the case.

These criteria test execution reliability and workflow integrity. They do not
claim that semantic research quality is fully captured by a single automated
score; qualitative review of outputs remains necessary.

## Evaluation runner

The runner is available through:

```
python -m research_agent.evaluation
```

A partial smoke run can be performed with:

```
python -m research_agent.evaluation --limit 3
```

Each case records status, run ID, subtask count, evidence count, traceability
ratio, duration, fallback-call count, and any exception. The runner catches an
individual case failure and continues so the resulting success rate reflects
the whole selected set.

Reports are written locally under `runtime/evaluation/` and are gitignored
until a reviewed result is deliberately captured as assessment evidence.

The 90% target is evaluated only on the full 12-case manifest; partial smoke
runs are explicitly labelled as partial and cannot claim that the target has
been met.

## Automated verification

Unit tests validate the manifest loader and the structural pass/fail criteria.
The current GitHub Actions suite reports:

```
81 passed in 0.79s
```

The 12-case live evaluation itself has not yet been executed, so no success-rate
claim is made at this stage.


## Three-case live smoke verification

The first live smoke run executed the first three fixed evaluation cases with
the normal hosted-to-local fallback configuration.

Observed results:

- E01 — LLM planning-agent evaluation: PASS;
- E02 — multi-agent coordination evaluation: PASS;
- E03 — retrieval-augmented generation evaluation: PASS;
- all three cases reached `awaiting_approval`;
- each case produced two Planner subtasks;
- each case retained six final evidence items;
- traceability was 100% in all three cases;
- fallback calls were 5, 7, and 7 respectively;
- smoke success rate: 3/3 (100%).

The runner correctly labelled this as a partial smoke run and did not claim
that the design target had been met. The 90% target remains reserved for the
complete 12-case manifest.

Generated local report:

```
runtime/evaluation/evaluation-20261010T155012Z.json
```

The next step is to execute the full 12-case manifest and record the resulting
success rate and any genuine failure cases.
