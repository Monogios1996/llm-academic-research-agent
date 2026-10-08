"""Environment-based configuration for live provider execution.

Secrets are read at runtime and are never stored in source control. Hosted
Hugging Face inference remains the primary path; an optional local
OpenAI-compatible fallback can be enabled explicitly for resilience.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


class ConfigurationError(RuntimeError):
    """Raised when required live-provider configuration is missing."""


def _env_flag(name: str, *, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default

    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise ConfigurationError(
        f"{name} must be one of true/false, yes/no, on/off, or 1/0"
    )


@dataclass(frozen=True)
class LiveSettings:
    """Configuration required to run the live academic research workflow."""

    hf_token: str
    hf_model: str
    openalex_api_key: str
    crossref_email: str | None = None
    local_llm_enabled: bool = False
    local_llm_model: str = "qwen3:4b"
    local_llm_base_url: str = "http://127.0.0.1:11434/v1/chat/completions"

    @classmethod
    def from_env(cls) -> "LiveSettings":
        """Load configuration from environment variables."""
        hf_token = os.getenv("HF_TOKEN", "").strip()
        hf_model = os.getenv("HF_MODEL", "openai/gpt-oss-20b:fastest").strip()
        openalex_api_key = os.getenv("OPENALEX_API_KEY", "").strip()
        crossref_email = os.getenv("CROSSREF_EMAIL", "").strip() or None
        local_llm_enabled = _env_flag("LOCAL_LLM_ENABLED", default=False)
        local_llm_model = os.getenv("LOCAL_LLM_MODEL", "qwen3:4b").strip()
        local_llm_base_url = os.getenv(
            "LOCAL_LLM_BASE_URL",
            "http://127.0.0.1:11434/v1/chat/completions",
        ).strip()

        missing = []
        if not hf_token:
            missing.append("HF_TOKEN")
        if not hf_model:
            missing.append("HF_MODEL")
        if not openalex_api_key:
            missing.append("OPENALEX_API_KEY")
        if local_llm_enabled and not local_llm_model:
            missing.append("LOCAL_LLM_MODEL")
        if local_llm_enabled and not local_llm_base_url:
            missing.append("LOCAL_LLM_BASE_URL")

        if missing:
            raise ConfigurationError(
                "Missing required environment variable(s): " + ", ".join(missing)
            )

        return cls(
            hf_token=hf_token,
            hf_model=hf_model,
            openalex_api_key=openalex_api_key,
            crossref_email=crossref_email,
            local_llm_enabled=local_llm_enabled,
            local_llm_model=local_llm_model,
            local_llm_base_url=local_llm_base_url,
        )
