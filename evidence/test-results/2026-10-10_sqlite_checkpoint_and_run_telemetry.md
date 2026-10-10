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


## First live persistence verification failure

The first local live run after enabling SQLite checkpointing failed during
LangGraph checkpoint serialization with:

```
TypeError: Type is not msgpack serializable: AcademicRecord
```

The failure occurred before the research workflow could complete. Unit tests had
only exercised primitive checkpoint values, so they did not expose the fact that
the real workflow state contains custom Pydantic domain objects such as
`AcademicRecord`.

## Serialization remediation

The SQLite checkpoint store now uses LangGraph's `JsonPlusSerializer` with
`pickle_fallback=True` so unsupported trusted local domain objects can be
persisted while retaining the standard serializer for supported values.

Because pickle deserialization must not be used with untrusted data, the code
documents that the checkpoint database is trusted local runtime state and must
not be replaced by or loaded from externally supplied files.

The persistence regression test now checkpoints and reloads a real
`AcademicRecord`, including a Pydantic `HttpUrl`, after closing and reopening
the SQLite store.

Latest GitHub Actions result:

```
76 passed in 0.73s
```

The live persistence verification should now be repeated to confirm creation of
the SQLite checkpoint database and structured JSON run log under the complete
research workflow.


## Successful live persistence verification

The repeat live workflow completed successfully after the serialization
remediation.

Observed result:

- automated suite: `76 passed`;
- run ID: `44916240c1074498aaf8f9b8d8636c75`;
- final status: `awaiting_approval`;
- SQLite checkpoint database:
  `runtime/research_agent_checkpoints.sqlite3`;
- local fallback: enabled with `qwen3:4b`;
- local fallback calls: 6;
- final evidence items: 5;
- structured run log:
  `runtime/run-logs/44916240c1074498aaf8f9b8d8636c75.json`;
- human approval boundary preserved and no research-package export performed.

This verifies the persistence and structured telemetry milestone end-to-end
under the normal controlled hosted-to-local fallback workflow.
