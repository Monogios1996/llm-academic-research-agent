# Second live-provider smoke test

Date: 2026-10-07
GitHub Actions run: 37669818952
Trigger: manual workflow dispatch
Branch: main
Commit: 75123763faa6af0fa3b449e49a1bd18333118d83

## Result

The second live-provider smoke test successfully reached both academic metadata
providers:

```
Crossref: OK - Planning as Graphs: Adaptive Agentic Planning for LLM Agents
OpenAlex: OK - Plancraft: an evaluation dataset for planning with LLM agents
```

Hugging Face authentication and routing were reached, but the configured model
was rejected:

```
HTTP 400
model_not_supported
The requested model 'google/gemma-2-2b-it' is not supported by any provider you
have enabled.
```

## Interpretation

The failure was not caused by missing repository secrets. The Hugging Face
router returned a structured model-selection error, while Crossref and OpenAlex
completed successfully. This isolated the remaining live-integration problem to
the default model choice.

## Remediation

The default model was changed to:

```
openai/gpt-oss-20b:fastest
```

The `:fastest` suffix delegates provider selection to Hugging Face's routing
policy rather than assuming a specific backend provider. The model choice is
also kept configurable through `HF_MODEL` so it can be changed without code
changes if provider availability changes.

A further live smoke run is required before claiming successful Hugging Face
execution.
