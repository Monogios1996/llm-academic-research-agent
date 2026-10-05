"""Abstractions for LLM access used by the planning agent.

Keeping the model provider behind a small interface prevents the Planner from
being coupled to one vendor. This supports the Unit 6 requirement for a hosted
Hugging Face model with a locally runnable fallback and also makes the Planner
testable without making live network calls.
"""

from __future__ import annotations

from typing import Protocol


class LLMGateway(Protocol):
    """Minimal interface required by agent roles that request model output."""

    def generate(self, prompt: str) -> str:
        """Return model-generated text for the supplied prompt."""
