"""Local Ollama LLM gateway.

The local fallback uses Ollama's native chat endpoint rather than the
OpenAI-compatible route. This gives the application explicit control over
thinking behaviour and avoids exhausting a small output budget on hidden
reasoning before a usable final answer is produced.
"""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

from research_agent.llm import LLMGateway, LLMProviderError


class LocalLLMGateway(LLMGateway):
    """Generate text through a locally running Ollama model."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        client: httpx.Client | None = None,
        timeout: float = 120.0,
        max_tokens: int = 700,
        temperature: float = 0.2,
    ) -> None:
        if not base_url.strip():
            raise ValueError("A local LLM base URL is required")
        if not model.strip():
            raise ValueError("A local LLM model is required")
        if max_tokens < 1:
            raise ValueError("max_tokens must be at least 1")

        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._owns_client = client is None
        self.client = client or httpx.Client(timeout=timeout)

    def generate(self, prompt: str) -> str:
        """Return final-answer text from the configured local model."""
        if not prompt.strip():
            raise ValueError("prompt cannot be empty")

        # Qwen3 supports a soft non-thinking switch. We also send Ollama's
        # explicit think=False flag so the intent is clear at both layers.
        local_prompt = f"{prompt.rstrip()}\n\n/no_think"
        is_summary_prompt = _is_summary_prompt(prompt)
        if is_summary_prompt:
            local_prompt += (
                "\n\nFor this local fallback call, return only JSON matching "
                "the supplied schema. Put the final evidence summary in the "
                "'summary' field with no analysis or preamble."
            )

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": local_prompt}],
            "stream": False,
            "think": False,
            "options": {
                "num_predict": self.max_tokens,
                "temperature": self.temperature,
            },
        }

        # The Planner explicitly requests JSON-only output. Ollama accepts a
        # JSON Schema in the native "format" field, which constrains the local
        # model to the planner contract instead of merely asking for generic
        # JSON. Plain-text roles such as the evidence summariser are unchanged.
        if "Return JSON only" in prompt:
            payload["format"] = _planner_output_schema(prompt)
        elif is_summary_prompt:
            payload["format"] = _summary_output_schema()

        try:
            response = self.client.post(self.base_url, json=payload)
            response.raise_for_status()
            data: dict[str, Any] = response.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text.strip().replace("\n", " ")[:500]
            raise LLMProviderError(
                f"Local LLM request failed with HTTP "
                f"{exc.response.status_code}: {detail or 'no response detail'}"
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise LLMProviderError(
                "Local LLM request failed; check that Ollama is running"
            ) from exc

        try:
            content = data["message"]["content"]
        except (KeyError, TypeError) as exc:
            raise LLMProviderError(
                "Local LLM returned an unexpected response structure"
            ) from exc

        if not isinstance(content, str):
            raise LLMProviderError("Local LLM returned invalid model output")

        cleaned = _final_answer(content)
        if not cleaned:
            raise LLMProviderError("Local LLM returned empty final model output")

        if is_summary_prompt:
            return _extract_structured_summary(cleaned)

        return cleaned

    def close(self) -> None:
        """Close the internally-created HTTP client."""
        if self._owns_client:
            self.client.close()


def _final_answer(content: str) -> str:
    """Remove any leaked thinking prefix and return only the final answer.

    Recent Ollama versions support think=False for Qwen3, but a live Windows
    integration run showed that this model/version combination could still
    include a thinking block in message.content. Stripping a leading block
    makes the adapter robust without exposing model reasoning to downstream
    agent roles.
    """
    text = content.strip()
    if not text:
        return ""

    if "</think>" in text.lower():
        text = re.sub(r"(?is)^.*?</think>\s*", "", text, count=1)

    return text.strip()



def _planner_output_schema(prompt: str) -> dict[str, Any]:
    """Return the JSON Schema used to constrain local Planner output.

    The minimum of two subtasks mirrors the Planner contract. When the prompt
    contains the configured maximum ("between 2 and N"), the same upper bound
    is applied at generation time; the Planner still performs its own Pydantic
    and explicit count validation afterwards.
    """
    maximum = 5
    match = re.search(r"between\s+2\s+and\s+(\d+)\s+focused", prompt, re.IGNORECASE)
    if match:
        maximum = max(2, int(match.group(1)))

    return {
        "type": "object",
        "properties": {
            "subtasks": {
                "type": "array",
                "minItems": 2,
                "maxItems": maximum,
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "minLength": 1},
                        "question": {"type": "string", "minLength": 5},
                        "search_terms": {
                            "type": "array",
                            "minItems": 1,
                            "items": {"type": "string", "minLength": 1},
                        },
                    },
                    "required": ["id", "question", "search_terms"],
                    "additionalProperties": False,
                },
            },
            "rationale": {"type": "string"},
        },
        "required": ["subtasks", "rationale"],
        "additionalProperties": False,
    }



def _is_summary_prompt(prompt: str) -> bool:
    """Identify the evidence-summarisation role without affecting other calls."""
    return (
        "evidence-summarisation component of an academic research agent"
        in prompt.lower()
    )


def _summary_output_schema() -> dict[str, Any]:
    """Constrain local evidence summarisation to one final summary field."""
    return {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "minLength": 1,
            }
        },
        "required": ["summary"],
        "additionalProperties": False,
    }


def _extract_structured_summary(content: str) -> str:
    """Return only the schema-constrained final summary from local output."""
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise LLMProviderError(
            "Local summariser returned invalid structured output"
        ) from exc

    if not isinstance(payload, dict):
        raise LLMProviderError(
            "Local summariser returned invalid structured output"
        )

    summary = payload.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise LLMProviderError(
            "Local summariser returned an empty structured summary"
        )

    return summary.strip()
