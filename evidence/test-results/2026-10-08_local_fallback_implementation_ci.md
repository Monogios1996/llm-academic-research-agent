# Local LLM fallback implementation milestone

Date: 2026-10-08
Latest CI run: 37810089561
Branch: main
Commit: 84f8bc5e8699735e87a384f07a4c6975529df92e

## Motivation

A live Hugging Face integration run previously reached the provider but failed
with HTTP 402 because no inference credits remained. After credits were added,
the hosted path succeeded. This demonstrated that quota availability is an
external operational dependency rather than a purely theoretical concern.

## Implementation

The codebase now includes:

- a shared provider-specific `LLMProviderError`;
- a `LocalLLMGateway` for OpenAI-compatible local model servers;
- a `FailoverGateway` that uses the hosted provider first and invokes the
  local model only after a provider-specific failure;
- explicit environment configuration for enabling/disabling the fallback;
- CLI reporting of fallback usage;
- mixed-provider provenance in approved export metadata;
- a standalone local-model smoke-test command.

The local fallback is deliberately disabled by default so hosted GitHub Actions
does not assume that a model server is running on localhost.

## Automated verification

The latest GitHub Actions test suite completed successfully:

```
51 passed in 0.62s
```

Coverage added for this milestone verifies local OpenAI-compatible request
handling, local connection failures, successful hosted execution without
fallback, provider-triggered failover, protection against swallowing
non-provider application errors, environment parsing, and dependency wiring.

## Remaining verification

This milestone establishes deterministic automated coverage but does not yet
claim live local inference. A real local model server must still be started on
a developer machine, followed by:

1. a local smoke test;
2. a full workflow run with local fallback enabled;
3. a controlled hosted-provider failure to demonstrate that the local model
   actually takes over during the workflow.
