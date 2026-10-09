# Local fallback planner JSON remediation

Date: 2026-10-09

## Live finding

A controlled fallback run was executed with the hosted Hugging Face token
deliberately invalid while the local Ollama fallback was enabled. The workflow
reached the Planner through the fallback path, but terminated with:

```
research_agent.planner.PlanningError: Planner returned invalid JSON
```

The local Qwen3 model had already passed the project smoke test, so the failure
was isolated to the Planner's assumption that model output would contain only a
raw JSON object.

## Remediation

The Planner still requests JSON-only output, but response handling now makes one
bounded recovery attempt when strict parsing fails:

1. parse the complete response with `json.loads`;
2. if that fails, locate the first opening brace and use
   `json.JSONDecoder.raw_decode` from that point;
3. require the recovered value to be a JSON object;
4. pass the result through the existing Pydantic `ResearchPlan` validation.

This permits common local-model wrappers such as a short explanation or
Markdown code fence without introducing a general JSON repair mechanism.
Malformed JSON and non-object JSON remain rejected.

## Automated verification

Four tests were added covering:

- Markdown-fenced planner JSON;
- leading/trailing prose around a valid JSON object;
- malformed embedded JSON;
- non-object JSON.

GitHub Actions verification after the change:

```
57 passed in 0.44s
```

A repeat controlled Hugging Face-to-Ollama fallback run is still required to
confirm the remediation under live execution.
