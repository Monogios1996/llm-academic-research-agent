"""Local OpenAI-compatible LLM gateway.

The default configuration targets Ollama's OpenAI-compatible chat endpoint on
localhost. Keeping the adapter OpenAI-compatible also allows other local model
servers to be used without changing Planner or Summariser code.
"""

from __future__ import annotations

from typing import Any

import httpx

from research_agent.llm import LLMGateway, LLMProviderError


class LocalLLMGateway(LLMGateway):
    """Generate text through a locally running OpenAI-compatible model server."""

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
        """Return generated text from the configured local model."""
        if not prompt.strip():
            raise ValueError("prompt cannot be empty")

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": False,
        }

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
                "Local LLM request failed; check that the local model server is running"
            ) from exc

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError(
                "Local LLM returned an unexpected response structure"
            ) from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMProviderError("Local LLM returned empty model output")

        return content.strip()

    def close(self) -> None:
        """Close the internally-created HTTP client."""
        if self._owns_client:
            self.client.close()
