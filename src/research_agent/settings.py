"""Environment-based configuration for live provider execution.

Secrets are read at runtime and are never stored in source control. Keeping
configuration in one small model makes live execution reproducible while
keeping unit tests independent from personal credentials.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigurationError(RuntimeError):
    """Raised when required live-provider configuration is missing."""


@dataclass(frozen=True)
class LiveSettings:
    """Configuration required to run the live academic research workflow."""

    hf_token: str
    hf_model: str
    openalex_api_key: str
    crossref_email: str | None = None

    @classmethod
    def from_env(cls) -> "LiveSettings":
        """Load configuration from environment variables."""
        hf_token = os.getenv("HF_TOKEN", "").strip()
        hf_model = os.getenv("HF_MODEL", "openai/gpt-oss-20b:fastest").strip()
        openalex_api_key = os.getenv("OPENALEX_API_KEY", "").strip()
        crossref_email = os.getenv("CROSSREF_EMAIL", "").strip() or None

        missing = []
        if not hf_token:
            missing.append("HF_TOKEN")
        if not hf_model:
            missing.append("HF_MODEL")
        if not openalex_api_key:
            missing.append("OPENALEX_API_KEY")

        if missing:
            raise ConfigurationError(
                "Missing required environment variable(s): " + ", ".join(missing)
            )

        return cls(
            hf_token=hf_token,
            hf_model=hf_model,
            openalex_api_key=openalex_api_key,
            crossref_email=crossref_email,
        )
