"""Tests for the minimal Streamlit demonstration helpers."""

from research_agent.llm import FailoverGateway, LLMProviderError
from research_agent.settings import LiveSettings
from research_agent.streamlit_app import _model_label


class _StaticGateway:
    def __init__(self, output: str) -> None:
        self.output = output

    def generate(self, prompt: str) -> str:
        return self.output


class _FailingGateway:
    def generate(self, prompt: str) -> str:
        raise LLMProviderError("provider unavailable")


def _settings() -> LiveSettings:
    return LiveSettings(
        hf_token="hf_test",
        hf_model="example/model",
        openalex_api_key="oa_test",
        local_llm_enabled=True,
        local_llm_model="qwen3:4b",
    )


def test_model_label_uses_hosted_model_when_no_fallback_call() -> None:
    gateway = FailoverGateway(
        primary=_StaticGateway("hosted"),
        fallback=_StaticGateway("local"),
    )

    assert _model_label(_settings(), gateway) == "example/model"


def test_model_label_reports_local_fallback_provenance() -> None:
    gateway = FailoverGateway(
        primary=_FailingGateway(),
        fallback=_StaticGateway("local"),
    )
    assert gateway.generate("test") == "local"

    label = _model_label(_settings(), gateway)

    assert "example/model (primary)" in label
    assert "qwen3:4b" in label
    assert "fallback used 1 call(s)" in label
