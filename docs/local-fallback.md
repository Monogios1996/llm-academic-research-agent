# Local LLM fallback

The Unit 6 design included a locally runnable LLM fallback so the research
workflow would not depend entirely on hosted inference availability.

That requirement became concrete during live integration testing. A hosted
Hugging Face run reached the provider successfully but returned HTTP 402
because the account had no remaining inference credits. After credits were
added, the same hosted path succeeded. Rather than treating that incident as a
one-off billing problem, the implementation uses it as evidence that provider
quota is an operational dependency worth mitigating.

## Design

Hosted Hugging Face inference remains the primary path.

When `LOCAL_LLM_ENABLED=true`, the application wraps the hosted gateway and a
local Ollama gateway in `FailoverGateway`.

The fallback activates only when the primary gateway raises
`LLMProviderError`. Application errors such as an invalid prompt are not
caught, because silently routing programming defects to another model would
make faults harder to diagnose.

The default local endpoint is Ollama's native chat API:

```
http://127.0.0.1:11434/api/chat
```

The native endpoint is used because the first real Windows smoke test exposed a
Qwen3 thinking-mode edge case on the OpenAI-compatible route: the request
completed, but the final `message.content` was empty after the output budget
was consumed before a usable answer was returned. A direct native Ollama call
confirmed that the model itself was healthy.

The local adapter therefore sends both Ollama's `think=false` option and
Qwen3's `/no_think` soft switch. It also defensively strips a leaked leading
thinking block if the local runtime still places one in `message.content`.
Only the final answer is passed into Planner or Summariser.

and the default model name is:

```
qwen3:4b
```

These defaults target Ollama's native local chat endpoint and can be overridden
through environment variables.

## Configuration

```
LOCAL_LLM_ENABLED=true
LOCAL_LLM_MODEL=qwen3:4b
LOCAL_LLM_BASE_URL=http://127.0.0.1:11434/api/chat
```

The fallback is disabled by default so hosted CI does not incorrectly assume a
model server is running on the GitHub runner.

## Verification strategy

Automated tests use deterministic gateways and mocked HTTP calls to verify:

- native Ollama request/response handling and non-thinking controls;
- connection failure reporting;
- hosted success without fallback;
- failover after a provider-specific failure;
- non-provider application errors are not swallowed;
- dependency wiring when local fallback is enabled.

A separate command checks a real local model server:

```
PYTHONPATH=src python -m research_agent.local_smoke
```

The first real local smoke test exposed an empty-output integration defect and
was remediated through the native Ollama adapter. Subsequent controlled
hosted-failure runs verified the complete fallback path with `qwen3:4b`,
including structured Planner output, grounded summarisation, validation, and
completion at the human-approval boundary. Later 12-case evaluation runs also
used the fallback successfully across varied research topics.
