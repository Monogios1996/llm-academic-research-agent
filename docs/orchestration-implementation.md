# Orchestration implementation note

## Purpose

This note records the implementation decisions made when translating the Unit 6
Plan-and-Execute design into the working prototype.

## Why LangGraph is used

LangGraph is used only for orchestration: explicit nodes represent the major
workflow stages and conditional edges represent validation, retry, re-planning,
and termination decisions. Domain messages continue to use Pydantic models.
This keeps control flow inspectable without making the framework responsible for
the academic data model.

The current LangGraph documentation describes StateGraph as a shared state with
nodes and edges, and supports mixing deterministic and LLM-driven steps. That is
a close fit for this project because retrieval/ranking/validation should remain
predictable while planning and summarisation require model flexibility.

## Bounded remediation

A failed validation does not create an unrestricted loop.

1. A targeted retry is attempted first.
2. Retrieval retries widen the result window so the second attempt is materially
   different from the first.
3. Processing retries remove evidence below the validator's explicit relevance
   threshold.
4. If the retry budget is exhausted, validation feedback is passed back to the
   Planner for one bounded re-plan.
5. If the re-plan still cannot satisfy validation, the workflow ends with a
   structured failure.

The limits are configurable, but the defaults remain deliberately small for the
prototype. This reduces the risk of runaway model/API calls and makes the
control path easier to demonstrate and test.

## Human approval boundary

Successful graph execution ends with `status = "awaiting_approval"`. Export is
not performed by the graph at this stage. This preserves the Unit 6 design
decision that final export is consequential and should require explicit human
approval.

## Testing strategy

Orchestration tests use deterministic substitutes for the LLM and academic API
providers. This isolates routing behaviour from external availability and lets
the tests verify:

- successful progression to human approval;
- targeted retrieval retry;
- escalation to the Planner after retry exhaustion; and
- clean termination when retry and re-planning budgets are exhausted.

Live provider tests and end-to-end execution evidence remain separate tasks so
mocked unit/integration tests are not misrepresented as live-system evidence.
