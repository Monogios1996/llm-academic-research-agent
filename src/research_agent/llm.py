"""Abstractions and failover behaviour for LLM access.

Keeping model providers behind a small interface prevents the Planner and
Summariser from being coupled to one vendor. The failover gateway implements
the Unit 6 resilience requirement: hosted inference is attempted first and a
local OpenAI-compatible model can take over when the hosted provider is
unavailable.
"""

from __future__ import annotations

from typing import Protocol


class LLMProviderError(RuntimeError):
    """Raised when an LLM provider cannot return usable model output."""


class LLMGateway(Protocol):
    """Minimal interface required by agent roles that request model output."""

    def generate(self, prompt: str) -> str:
        """Return model-generated text for the supplied prompt."""


class FailoverGateway:
    """Use a local fallback only when the primary provider genuinely fails.

    Invalid prompts and downstream parsing errors are deliberately not caught
    here. Failover is restricted to LLMProviderError so application defects are
    not silently hidden behind a second model call.
    """

    def __init__(self, primary: LLMGateway, fallback: LLMGateway) -> None:
        self.primary = primary
        self.fallback = fallback
        self.fallback_count = 0
        self.last_provider = "primary"

    def generate(self, prompt: str) -> str:
        try:
            output = self.primary.generate(prompt)
            self.last_provider = "primary"
            return output
        except LLMProviderError:
            self.fallback_count += 1
            self.last_provider = "fallback"
            return self.fallback.generate(prompt)
