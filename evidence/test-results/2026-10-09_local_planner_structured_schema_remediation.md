# Local planner structured-schema remediation

Date: 2026-10-09

## Live finding

After the minimum-subtask remediation, a controlled Hugging Face-to-Ollama
fallback run reached the local Planner but Pydantic rejected the second subtask
because the model returned an object containing an `id` without the required
`question` and `search_terms` fields.

This showed that generic JSON mode improved syntactic validity but did not
guarantee the planner's required object structure.

## Remediation

For Planner prompts only, the local Ollama gateway now sends a JSON Schema in
the native `format` field instead of the generic string `"json"`.

The schema constrains:

- the top-level output to an object;
- `subtasks` to an array with at least two items;
- the upper bound to the Planner's configured maximum when it can be read from
  the prompt;
- every subtask to contain `id`, `question`, and `search_terms`;
- `search_terms` to contain at least one string;
- `rationale` to be present;
- unexpected extra object properties to be rejected by the generation schema.

The existing Planner JSON parsing, Pydantic model validation, and explicit
minimum/maximum count checks remain in place as independent downstream
validation layers.

## Automated verification

The local-gateway test now verifies that the generated Ollama request contains
the JSON Schema and that the configured maximum is propagated correctly.

Latest GitHub Actions result:

```
60 passed in 0.38s
```

A repeat controlled live Hugging Face-to-Ollama Planner run is still required
to verify the schema under real local inference.
