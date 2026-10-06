"""Unit tests for evidence validation and targeted remediation."""

from research_agent.models import AcademicRecord, RankedEvidence
from research_agent.validation import EvidenceValidator


def _evidence(
    *,
    traceable: bool = True,
    relevance: float = 0.8,
    summary: str = "Relevant evidence summary.",
) -> RankedEvidence:
    return RankedEvidence(
        record=AcademicRecord(
            title="Example Study",
            source="Crossref",
            doi="10.1234/example" if traceable else None,
        ),
        relevance_score=relevance,
        summary=summary,
        traceable=traceable,
    )


def test_validator_passes_sufficient_traceable_evidence() -> None:
    validator = EvidenceValidator(min_items=2, min_traceable_ratio=0.5)

    result = validator.validate([_evidence(), _evidence()])

    assert result.passed is True
    assert result.issues == []
    assert result.retry_target is None


def test_validator_routes_insufficient_evidence_to_retrieval() -> None:
    validator = EvidenceValidator(min_items=2)

    result = validator.validate([_evidence()])

    assert result.passed is False
    assert result.retry_target == "retrieval"
    assert "at least 2 required" in result.issues[0]


def test_validator_routes_low_traceability_to_retrieval() -> None:
    validator = EvidenceValidator(min_items=2, min_traceable_ratio=0.75)

    result = validator.validate([
        _evidence(traceable=True),
        _evidence(traceable=False),
    ])

    assert result.passed is False
    assert result.retry_target == "retrieval"
    assert any("Traceable evidence ratio" in issue for issue in result.issues)


def test_validator_routes_weak_relevance_to_processing() -> None:
    validator = EvidenceValidator(
        min_items=1,
        min_traceable_ratio=0.0,
        min_relevance_score=0.5,
    )

    result = validator.validate([_evidence(relevance=0.2)])

    assert result.passed is False
    assert result.retry_target == "processing"
    assert any("minimum relevance score" in issue for issue in result.issues)


def test_validator_routes_empty_summary_to_processing() -> None:
    validator = EvidenceValidator(
        min_items=1,
        min_traceable_ratio=0.0,
        min_relevance_score=0.0,
    )

    result = validator.validate([_evidence(summary=" ")])

    assert result.passed is False
    assert result.retry_target == "processing"
    assert any("empty summaries" in issue for issue in result.issues)
