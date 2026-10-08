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
local OpenAI-compatible gateway in `FailoverGateway`.

The fallback activates only when the primary gateway raises
`LLMProviderError`. Application errors such as an invalid prompt are not
caught, because silently routing programming defects to another model would
make faults harder to diagnose.

The default local endpoint is:

```
http://127.0.0.1:11434/v1/chat/completions
```

and the default model name is:

```
qwen3:4b
```

These defaults are compatible with a local OpenAI-style server configuration
and can be overridden through environment variables.

## Configuration

```
LOCAL_LLM_ENABLED=true
LOCAL_LLM_MODEL=qwen3:4b
LOCAL_LLM_BASE_URL=http://127.0.0.1:11434/v1/chat/completions
```

The fallback is disabled by default so hosted CI does not incorrectly assume a
model server is running on the GitHub runner.

## Verification strategy

Automated tests use deterministic gateways and mocked HTTP calls to verify:

- local OpenAI-compatible request/response handling;
- connection failure reporting;
- hosted success without fallback;
- failover after a provider-specific failure;
- non-provider application errors are not swallowed;
- dependency wiring when local fallback is enabled.

A separate command checks a real local model server:

```
PYTHONPATH=src python -m research_agent.local_smoke
```

A real local smoke test and a full workflow run with the hosted provider made
unavailable are still required before claiming live fallback verification.
