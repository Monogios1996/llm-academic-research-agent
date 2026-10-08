"""Tests for live dependency wiring without making network calls."""

from research_agent.huggingface import HuggingFaceGateway
from research_agent.llm import FailoverGateway
from research_agent.local_llm import LocalLLMGateway
from research_agent.retrieval import CrossrefRetriever, OpenAlexRetriever
from research_agent.settings import LiveSettings
from research_agent.bootstrap import build_live_workflow


def test_live_workflow_wires_expected_providers() -> None:
    settings = LiveSettings(
        hf_token="hf_test",
        hf_model="example/model",
        openalex_api_key="oa_test",
        crossref_email="student@example.org",
    )

    workflow = build_live_workflow(settings)

    assert isinstance(workflow.planner.gateway, HuggingFaceGateway)
    assert workflow.planner.gateway.model == "example/model"
    assert isinstance(workflow.retrievers[0], CrossrefRetriever)
    assert isinstance(workflow.retrievers[1], OpenAlexRetriever)
    assert workflow.retrievers[1].api_key == "oa_test"
    assert workflow.max_retries == 1
    assert workflow.max_replans == 1


def test_live_workflow_wires_local_fallback_when_enabled() -> None:
    settings = LiveSettings(
        hf_token="hf_test",
        hf_model="example/model",
        openalex_api_key="oa_test",
        crossref_email="student@example.org",
        local_llm_enabled=True,
        local_llm_model="qwen3:4b",
        local_llm_base_url="http://127.0.0.1:11434/v1/chat/completions",
    )

    workflow = build_live_workflow(settings)

    gateway = workflow.planner.gateway
    assert isinstance(gateway, FailoverGateway)
    assert isinstance(gateway.primary, HuggingFaceGateway)
    assert isinstance(gateway.fallback, LocalLLMGateway)
    assert gateway.primary.model == "example/model"
    assert gateway.fallback.model == "qwen3:4b"
