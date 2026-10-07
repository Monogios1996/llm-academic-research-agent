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
