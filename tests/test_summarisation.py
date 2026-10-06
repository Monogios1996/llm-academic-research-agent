"""Unit tests for grounded LLM evidence summarisation."""

import pytest

from research_agent.models import (
    AcademicRecord,
    ResearchSubtask,
    ScoredRecord,
)
from research_agent.summarisation import EvidenceSummariser, SummarisationError


class FakeGateway:
    """Deterministic LLM substitute used to test summarisation behaviour."""

    def __init__(self, response: str) -> None:
        self.response = response
        self.last_prompt: str | None = None

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.response


def _subtask() -> ResearchSubtask:
    return ResearchSubtask(
        id="q1",
        question="How are LLM planning agents evaluated?",
        search_terms=["LLM planning agents", "evaluation"],
    )


def _scored_record() -> ScoredRecord:
    return ScoredRecord(
        record=AcademicRecord(
            title="Evaluating LLM Planning Agents",
            authors=["A. Researcher"],
            year=2025,
            doi="10.1234/example",
            source="Crossref",
            abstract="The study compares evaluation methods for planning agents.",
        ),
        relevance_score=0.82,
    )


def test_summariser_preserves_score_and_traceability() -> None:
    gateway = FakeGateway(
        "The record is relevant because it compares evaluation methods "
        "for planning agents."
    )
    summariser = EvidenceSummariser(gateway=gateway)

    evidence = summariser.summarise(_scored_record(), _subtask())

    assert evidence.relevance_score == 0.82
    assert evidence.traceable is True
    assert "evaluation methods" in evidence.summary
    assert gateway.last_prompt is not None
    assert "Do not invent" in gateway.last_prompt


def test_summariser_rejects_empty_output() -> None:
    summariser = EvidenceSummariser(gateway=FakeGateway("   "))

    with pytest.raises(SummarisationError, match="empty evidence summary"):
        summariser.summarise(_scored_record(), _subtask())


def test_summariser_truncates_unbounded_output() -> None:
    summariser = EvidenceSummariser(
        gateway=FakeGateway("x" * 250),
        max_summary_chars=100,
    )

    evidence = summariser.summarise(_scored_record(), _subtask())

    assert len(evidence.summary) == 100
