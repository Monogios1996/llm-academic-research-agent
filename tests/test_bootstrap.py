"""Tests for live dependency wiring without making network calls."""

from research_agent.huggingface import HuggingFaceGateway
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
