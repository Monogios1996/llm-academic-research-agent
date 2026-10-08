# First live local-model smoke test and remediation

Date: 2026-10-08
Environment: Windows, Python 3.11.9, Ollama 0.40.1, qwen3:4b

## First project smoke result

The repository was up to date and all dependencies were installed successfully.
Running:

```
py -3.11 -m research_agent.local_smoke
```

reached the local gateway but failed with:

```
research_agent.llm.LLMProviderError: Local LLM returned empty model output
```

This demonstrated that the local Ollama process and Python integration path were
reachable, but the adapter did not receive a usable final answer from the
OpenAI-compatible endpoint.

## Diagnostic check

A direct request to Ollama's native `/api/chat` endpoint using the same
`qwen3:4b` model returned a completed response and a final answer. The output
also showed that this model/runtime combination could still emit a thinking
prefix despite a non-thinking request.

The defect was therefore isolated to local response handling rather than model
installation or connectivity.

## Remediation

The local adapter was changed to:

- use Ollama's native `/api/chat` endpoint;
- request `think=false`;
- append Qwen3's `/no_think` soft switch;
- use Ollama's `num_predict` option for the output budget;
- strip a leaked leading thinking block before returning text to the Planner or
  Summariser;
- reject cases where no final answer remains.

Automated coverage was expanded for the native payload, thinking cleanup, and
empty-final-output case.

Latest automated verification after the code/test remediation:

```
53 passed in 0.62s
```

A repeat live local smoke test is still required before this remediation is
considered live-verified.
