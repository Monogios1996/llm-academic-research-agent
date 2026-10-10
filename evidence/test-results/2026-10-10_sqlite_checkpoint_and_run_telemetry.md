# SQLite checkpoint persistence and structured run telemetry

Date: 2026-10-10

## Assignment rationale

The Unit 6 design proposed persistent workflow state and inspectable execution
metadata. The implementation now adds these as lightweight prototype features
without changing the existing human-approval or bounded-retry behaviour.

## Persistence implementation

The live CLI can now compile the LangGraph workflow with LangGraph's official
SQLite checkpointer. Each run receives a unique run/thread identifier and that
identifier is supplied to LangGraph as the checkpoint `thread_id`.

By default, local live runs persist checkpoints to:

```
runtime/research_agent_checkpoints.sqlite3
```

The runtime directory is gitignored because checkpoint databases are generated
execution state rather than source code. The CLI also supports redirecting the
database path or disabling checkpointing for an individual run.

Automated coverage verifies both:

- workflow state can be retrieved by an explicit thread ID; and
- a SQLite checkpoint remains available after the checkpoint store is closed
  and reopened, demonstrating real disk persistence rather than only in-memory
  state.

## Structured run telemetry

Completed workflow runs now write one JSON record under:

```
runtime/run-logs/
```

The record includes:

- run ID / trace ID;
- UTC start and finish times;
- execution duration;
- final workflow status;
- model/fallback provenance;
- fallback-call count;
- checkpoint database path;
- generated subtask IDs/questions;
- final evidence count;
- workflow audit events.

Token usage and estimated cost are recorded explicitly as unavailable rather
than fabricated because the configured hosted/local gateways do not expose
provider usage consistently.

## Automated verification

The latest verified GitHub Actions result after persistence and telemetry tests:

```
76 passed in 0.78s
```

A live local run is still required to verify that the CLI creates both the
SQLite checkpoint database and structured JSON run log under the normal
hosted-to-local fallback workflow.
