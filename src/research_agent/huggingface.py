"""Hugging Face Inference Providers gateway.

The application talks to Hugging Face through its OpenAI-compatible chat
completion route using httpx directly. A small gateway keeps provider details
out of the Planner and Summariser and avoids coupling core agent logic to a
specific client SDK.
"""

from __future__ import annotations

from typing import Any

import httpx

from research_agent.llm import LLMGateway, LLMProviderError


class HuggingFaceGateway(LLMGateway):
    """Generate text through Hugging Face Inference Providers."""

    BASE_URL = "https://router.huggingface.co/v1/chat/completions"

    def __init__(
        self,
        *,
        token: str,
        model: str,
        client: httpx.Client | None = None,
        timeout: float = 60.0,
        max_tokens: int = 700,
        temperature: float = 0.2,
    ) -> None:
        if not token.strip():
            raise ValueError("A Hugging Face token is required")
        if not model.strip():
            raise ValueError("A Hugging Face model is required")
        if max_tokens < 1:
            raise ValueError("max_tokens must be at least 1")

        self.token = token
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._owns_client = client is None
        self.client = client or httpx.Client(timeout=timeout)

    def generate(self, prompt: str) -> str:
        """Return plain generated text for one user prompt."""
        if not prompt.strip():
            raise ValueError("prompt cannot be empty")

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        try:
            response = self.client.post(self.BASE_URL, json=payload, headers=headers)
            response.raise_for_status()
            data: dict[str, Any] = response.json()
        except httpx.HTTPStatusError as exc:
            # Include a bounded provider response so configuration/model errors
            # are diagnosable from CI without exposing request headers or tokens.
            detail = exc.response.text.strip().replace("\n", " ")[:500]
            raise LLMProviderError(
                f"Hugging Face inference request failed with HTTP "
                f"{exc.response.status_code}: {detail or 'no response detail'}"
            ) from exc
        except (httpx.HTTPError, ValueError) as exc:
            raise LLMProviderError("Hugging Face inference request failed") from exc

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError(
                "Hugging Face returned an unexpected response structure"
            ) from exc

        if not isinstance(content, str) or not content.strip():
            raise LLMProviderError("Hugging Face returned empty model output")

        return content.strip()

    def close(self) -> None:
        """Close the internally-created HTTP client."""
        if self._owns_client:
            self.client.close()
