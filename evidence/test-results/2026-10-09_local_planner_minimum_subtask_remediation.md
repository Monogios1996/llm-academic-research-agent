# Local planner minimum-subtask remediation

Date: 2026-10-09

## Live finding

A controlled Hugging Face-to-Ollama failover test succeeded and showed:

```
Fallback calls: 1
Last provider: fallback
```

The local Qwen3 model returned a valid structured `ResearchPlan`, but it
contained only one subtask even though the Planner prompt states that the goal
must be decomposed into between two and the configured maximum number of
subtasks.

This exposed a contract gap: the prompt requested at least two subtasks, but the
runtime validation only enforced the upper bound. The prompt example also
showed only one subtask, which gave the smaller local model a conflicting
demonstration.

## Remediation

The Planner now:

- requires `max_subtasks >= 2`;
- rejects plans containing fewer than two subtasks;
- continues to reject plans exceeding the configured maximum;
- shows both `q1` and `q2` in the JSON example;
- explicitly states that the `subtasks` array must contain at least two
  items.

Two tests were added for the minimum-subtask contract, and the existing planner
test now verifies that the prompt itself demonstrates `q2`.

The first CI run after adding the tests failed because the prompt example had
not yet been updated as intended. The prompt was then corrected and the next
GitHub Actions run passed.

## Automated verification

Latest GitHub Actions result:

```
60 passed in 0.84s
```

A repeat controlled live failover test is still required to confirm that Qwen3
now returns a plan satisfying the two-subtask minimum.
