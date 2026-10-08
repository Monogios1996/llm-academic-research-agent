"""Tests for environment-based live configuration."""

import pytest

from research_agent.settings import ConfigurationError, LiveSettings


def test_live_settings_load_required_values(monkeypatch) -> None:
    monkeypatch.setenv("HF_TOKEN", "hf_test")
    monkeypatch.setenv("HF_MODEL", "example/model")
    monkeypatch.setenv("OPENALEX_API_KEY", "oa_test")
    monkeypatch.setenv("CROSSREF_EMAIL", "student@example.org")

    settings = LiveSettings.from_env()

    assert settings.hf_token == "hf_test"
    assert settings.hf_model == "example/model"
    assert settings.openalex_api_key == "oa_test"
    assert settings.crossref_email == "student@example.org"
    assert settings.local_llm_enabled is False
    assert settings.local_llm_model == "qwen3:4b"
    assert (
        settings.local_llm_base_url
        == "http://127.0.0.1:11434/v1/chat/completions"
    )


def test_live_settings_uses_small_default_model(monkeypatch) -> None:
    monkeypatch.setenv("HF_TOKEN", "hf_test")
    monkeypatch.delenv("HF_MODEL", raising=False)
    monkeypatch.setenv("OPENALEX_API_KEY", "oa_test")

    settings = LiveSettings.from_env()

    assert settings.hf_model == "openai/gpt-oss-20b:fastest"


def test_live_settings_reject_missing_secrets(monkeypatch) -> None:
    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)

    with pytest.raises(ConfigurationError) as exc:
        LiveSettings.from_env()

    assert "HF_TOKEN" in str(exc.value)
    assert "OPENALEX_API_KEY" in str(exc.value)


def test_live_settings_enables_local_fallback(monkeypatch) -> None:
    monkeypatch.setenv("HF_TOKEN", "hf_test")
    monkeypatch.setenv("OPENALEX_API_KEY", "oa_test")
    monkeypatch.setenv("LOCAL_LLM_ENABLED", "true")
    monkeypatch.setenv("LOCAL_LLM_MODEL", "local-test-model")
    monkeypatch.setenv(
        "LOCAL_LLM_BASE_URL",
        "http://localhost:9999/v1/chat/completions",
    )

    settings = LiveSettings.from_env()

    assert settings.local_llm_enabled is True
    assert settings.local_llm_model == "local-test-model"
    assert settings.local_llm_base_url.endswith("/v1/chat/completions")


def test_live_settings_rejects_invalid_local_fallback_flag(monkeypatch) -> None:
    monkeypatch.setenv("HF_TOKEN", "hf_test")
    monkeypatch.setenv("OPENALEX_API_KEY", "oa_test")
    monkeypatch.setenv("LOCAL_LLM_ENABLED", "sometimes")

    with pytest.raises(ConfigurationError, match="LOCAL_LLM_ENABLED"):
        LiveSettings.from_env()
