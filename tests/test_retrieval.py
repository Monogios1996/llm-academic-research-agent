"""Tests for academic metadata retrieval and normalisation."""

import httpx
import pytest

from research_agent.models import ResearchSubtask
from research_agent.retrieval import (
    CrossrefRetriever,
    OpenAlexRetriever,
    RetrievalError,
    _reconstruct_openalex_abstract,
)


def _subtask() -> ResearchSubtask:
    return ResearchSubtask(
        id="q1",
        question="How are LLM planning agents evaluated?",
        search_terms=["LLM planning agents", "evaluation"],
    )


def test_crossref_retrieval_normalises_metadata() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["query.bibliographic"] == "LLM planning agents evaluation"
        assert "llm-academic-research-agent/0.1" in request.headers["User-Agent"]
        return httpx.Response(
            200,
            json={
                "message": {
                    "items": [
                        {
                            "DOI": "10.1234/example",
                            "title": ["Planning Agents in Practice"],
                            "author": [
                                {"given": "Ada", "family": "Researcher"},
                                {"family": "Scholar"},
                            ],
                            "published": {"date-parts": [[2025, 4, 1]]},
                            "URL": "https://doi.org/10.1234/example",
                        }
                    ]
                }
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    records = CrossrefRetriever(client=client).search(_subtask(), limit=3)

    assert len(records) == 1
    assert records[0].title == "Planning Agents in Practice"
    assert records[0].authors == ["Ada Researcher", "Scholar"]
    assert records[0].year == 2025
    assert records[0].source == "Crossref"


def test_openalex_retrieval_normalises_metadata() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["search"] == "LLM planning agents evaluation"
        assert request.url.params["api_key"] == "test-key"
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": "https://openalex.org/W123",
                        "display_name": "Evaluating Planning Agents",
                        "publication_year": 2024,
                        "doi": "https://doi.org/10.9999/openalex",
                        "authorships": [
                            {"author": {"display_name": "Grace Scholar"}}
                        ],
                        "primary_location": {
                            "landing_page_url": "https://example.org/work"
                        },
                        "abstract_inverted_index": {
                            "Planning": [0],
                            "agents": [1],
                            "are": [2],
                            "evaluated": [3],
                        },
                    }
                ]
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    records = OpenAlexRetriever(api_key="test-key", client=client).search(
        _subtask(), limit=2
    )

    assert len(records) == 1
    assert records[0].doi == "10.9999/openalex"
    assert records[0].abstract == "Planning agents are evaluated"
    assert records[0].source == "OpenAlex"


def test_provider_http_failure_is_not_silently_hidden() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "unavailable"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    retriever = CrossrefRetriever(client=client)

    with pytest.raises(RetrievalError, match="Crossref retrieval failed"):
        retriever.search(_subtask())


def test_openalex_abstract_reconstruction_orders_positions() -> None:
    index = {"second": [1], "first": [0], "third": [2]}

    assert _reconstruct_openalex_abstract(index) == "first second third"
