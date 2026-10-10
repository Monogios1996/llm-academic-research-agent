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
        self.calls = 0

    def generate(self, prompt: str) -> str:
        self.calls += 1
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
    assert "named benchmarks" in gateway.last_prompt
    assert "numeric values" in gateway.last_prompt
    assert "Never infer substantive findings from" in gateway.last_prompt
    assert "use complete sentences" in gateway.last_prompt



def test_summariser_uses_deterministic_limitation_without_abstract() -> None:
    gateway = FakeGateway(
        "Invented benchmark findings that must never be used."
    )
    scored = ScoredRecord(
        record=AcademicRecord(
            title="FlowBench: Revisiting Workflow-Guided Planning",
            authors=["A. Researcher"],
            year=2024,
            doi="10.1234/flowbench",
            source="Crossref",
            abstract=None,
        ),
        relevance_score=0.74,
    )
    summariser = EvidenceSummariser(gateway=gateway)

    evidence = summariser.summarise(scored, _subtask())

    assert gateway.calls == 0
    assert "no abstract was available from Crossref" in evidence.summary
    assert "cannot be established from the retrieved evidence" in evidence.summary
    assert "Invented benchmark" not in evidence.summary


def test_summariser_falls_back_to_abstract_for_unsupported_acronym() -> None:
    gateway = FakeGateway(
        "The study evaluates LARC and RBLA benchmarks for LLM agents."
    )
    scored = ScoredRecord(
        record=AcademicRecord(
            title="Evaluation and Benchmarking of LLM Agents: A Survey",
            authors=["A. Researcher"],
            year=2025,
            doi="10.1234/survey",
            source="OpenAlex",
            abstract=(
                "The survey proposes a taxonomy of evaluation objectives and "
                "processes for LLM agents, including reliability, safety, "
                "datasets, benchmarks, and metric computation."
            ),
        ),
        relevance_score=0.80,
    )
    summariser = EvidenceSummariser(gateway=gateway)

    evidence = summariser.summarise(scored, _subtask())

    assert gateway.calls == 1
    assert evidence.summary.startswith("Abstract evidence:")
    assert "LARC" not in evidence.summary
    assert "RBLA" not in evidence.summary
    assert "taxonomy of evaluation objectives" in evidence.summary


def test_summariser_falls_back_to_abstract_for_unsupported_number() -> None:
    gateway = FakeGateway(
        "The benchmark reports a 97% success rate for LLM planning agents."
    )
    scored = ScoredRecord(
        record=AcademicRecord(
            title="Planning Agent Evaluation",
            authors=["A. Researcher"],
            year=2025,
            doi="10.1234/planning",
            source="OpenAlex",
            abstract=(
                "The study evaluates planning-agent reliability across "
                "multiple benchmark tasks."
            ),
        ),
        relevance_score=0.75,
    )
    summariser = EvidenceSummariser(gateway=gateway)

    evidence = summariser.summarise(scored, _subtask())

    assert evidence.summary.startswith("Abstract evidence:")
    assert "97%" not in evidence.summary
    assert "planning-agent reliability" in evidence.summary

def test_summariser_rejects_empty_output() -> None:
    summariser = EvidenceSummariser(gateway=FakeGateway("   "))

    with pytest.raises(SummarisationError, match="empty evidence summary"):
        summariser.summarise(_scored_record(), _subtask())



def test_summariser_prefers_complete_sentence_when_truncating() -> None:
    response = (
        "The first sentence provides enough relevant evidence for the record. "
        "The second sentence is intentionally much longer and would otherwise "
        "be cut off in the middle when the character limit is applied."
    )
    summariser = EvidenceSummariser(
        gateway=FakeGateway(response),
        max_summary_chars=100,
    )

    evidence = summariser.summarise(_scored_record(), _subtask())

    assert evidence.summary == (
        "The first sentence provides enough relevant evidence for the record."
    )
    assert len(evidence.summary) <= 100


def test_summariser_marks_truncation_when_no_sentence_boundary_fits() -> None:
    response = (
        "This deliberately long summary contains no sentence-ending punctuation "
        "before the configured limit and therefore needs an explicit truncation "
        "marker rather than a broken final word"
    )
    summariser = EvidenceSummariser(
        gateway=FakeGateway(response),
        max_summary_chars=100,
    )

    evidence = summariser.summarise(_scored_record(), _subtask())

    assert evidence.summary.endswith("…")
    assert len(evidence.summary) <= 100

def test_summariser_truncates_unbounded_output() -> None:
    summariser = EvidenceSummariser(
        gateway=FakeGateway("x" * 250),
        max_summary_chars=100,
    )

    evidence = summariser.summarise(_scored_record(), _subtask())

    assert len(evidence.summary) == 100
