# First live-provider smoke test

Date: 2026-10-07
GitHub Actions run: 37616784173
Trigger: manual workflow dispatch
Branch: main
Commit: eaf7c3e07fa47bab6c8b4691cb9b5a320bc21dbc

## Result

The workflow setup, checkout, Python 3.11 environment, and dependency
installation succeeded. The live-provider step failed on its first external
call to Hugging Face.

Observed failure:

```
HTTP 400 Bad Request
research_agent.huggingface.LLMProviderError:
Hugging Face inference request failed
```

Because the first version of the smoke test stopped immediately after the
Hugging Face exception, this run did not establish whether Crossref or OpenAlex
were reachable with the configured credentials.

## Remediation

Two changes were made before re-running:

1. Hugging Face HTTP failures now include the bounded provider response body and
   status code in the exception. Request headers and tokens are not logged.
2. The smoke test now executes Hugging Face, Crossref, and OpenAlex
   independently and reports all three outcomes before returning a failure.

This preserves the failed run as genuine development evidence rather than
hiding it, while making the next run diagnostically useful.
