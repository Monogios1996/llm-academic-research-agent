"""Unit tests for deterministic evidence processing and ranking."""

import pytest

from research_agent.models import AcademicRecord, ResearchSubtask
from research_agent.processing import (
    deduplicate_records,
    process_records,
    relevance_score,
)


def _subtask() -> ResearchSubtask:
    return ResearchSubtask(
        id="q1",
        question="How are LLM planning agents evaluated?",
        search_terms=["LLM planning agents", "evaluation"],
    )


def test_deduplication_prefers_richer_record_with_same_doi() -> None:
    sparse = AcademicRecord(
        title="Evaluating LLM Planning Agents",
        source="Crossref",
        doi="10.1234/example",
    )
    rich = AcademicRecord(
        title="Evaluating LLM Planning Agents",
        source="OpenAlex",
        doi="https://doi.org/10.1234/example",
        authors=["A. Researcher"],
        year=2025,
        abstract="A study of evaluation methods for LLM planning agents.",
        url="https://example.org/work",
    )

    unique = deduplicate_records([sparse, rich])

    assert len(unique) == 1
    assert unique[0].source == "OpenAlex"
    assert unique[0].abstract is not None


def test_deduplication_falls_back_to_normalised_title() -> None:
    first = AcademicRecord(
        title="Planning Agents: An Evaluation",
        source="Crossref",
    )
    second = AcademicRecord(
        title="Planning agents an evaluation",
        source="OpenAlex",
        authors=["A. Researcher"],
    )

    unique = deduplicate_records([first, second])

    assert len(unique) == 1
    assert unique[0].authors == ["A. Researcher"]


def test_relevance_score_rewards_title_and_abstract_overlap() -> None:
    highly_relevant = AcademicRecord(
        title="Evaluation of LLM Planning Agents",
        source="Crossref",
        abstract="This work evaluates autonomous planning agents.",
    )
    unrelated = AcademicRecord(
        title="Marine Biology Field Methods",
        source="Crossref",
        abstract="A study of coastal ecosystems.",
    )

    assert relevance_score(highly_relevant, _subtask()) > relevance_score(
        unrelated, _subtask()
    )


def test_process_records_returns_ranked_top_k() -> None:
    records = [
        AcademicRecord(
            title="Evaluation of LLM Planning Agents",
            source="Crossref",
            year=2025,
        ),
        AcademicRecord(
            title="LLM Agents for Academic Planning",
            source="OpenAlex",
            year=2024,
        ),
        AcademicRecord(
            title="Unrelated Marine Biology",
            source="Crossref",
            year=2026,
        ),
    ]

    ranked = process_records(records, _subtask(), top_k=2)

    assert len(ranked) == 2
    assert ranked[0].relevance_score >= ranked[1].relevance_score
    assert all(item.record.title != "Unrelated Marine Biology" for item in ranked)


def test_process_records_rejects_invalid_top_k() -> None:
    with pytest.raises(ValueError, match="top_k must be at least 1"):
        process_records([], _subtask(), top_k=0)
