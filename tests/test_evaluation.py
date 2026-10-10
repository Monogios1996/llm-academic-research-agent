"""Tests for the repeatable evaluation harness."""

import json

import pytest

from research_agent.evaluation import evaluate_result, load_cases
from research_agent.models import (
    AcademicRecord,
    RankedEvidence,
    ResearchGoal,
    ResearchPlan,
    ResearchSubtask,
    ValidationResult,
)


def _result(*, traceable: bool = True) -> dict:
    goal = ResearchGoal(topic="LLM planning agents")
    plan = ResearchPlan(
        goal=goal,
        subtasks=[
            ResearchSubtask(
                id="q1",
                question="How are planning agents evaluated?",
                search_terms=["planning agents", "evaluation"],
            ),
            ResearchSubtask(
                id="q2",
                question="Which benchmarks are used for planning agents?",
                search_terms=["planning agents", "benchmarks"],
            ),
        ],
        rationale="Evaluation test plan.",
    )
    evidence = [
        RankedEvidence(
            record=AcademicRecord(
                title=f"Planning Study {index}",
                source="OpenAlex",
                doi=f"10.1234/{index}" if traceable else None,
                abstract="Planning-agent evaluation evidence.",
            ),
            relevance_score=0.8,
            summary="Grounded evidence summary.",
            traceable=traceable,
        )
        for index in range(2)
    ]
    return {
        "run_id": "evaluation-test-run",
        "status": "awaiting_approval",
        "plan": plan,
        "all_evidence": evidence,
        "validation": ValidationResult(passed=True),
    }


def test_evaluate_result_passes_structurally_valid_run() -> None:
    outcome = evaluate_result(_result())

    assert outcome["passed"] is True
    assert outcome["subtask_count"] == 2
    assert outcome["evidence_count"] == 2
    assert outcome["traceable_ratio"] == 1.0
    assert outcome["validation_passed"] is True


def test_evaluate_result_fails_insufficient_traceability() -> None:
    outcome = evaluate_result(_result(traceable=False))

    assert outcome["passed"] is False
    assert outcome["traceable_ratio"] == 0.0


def test_load_cases_validates_manifest(tmp_path) -> None:
    path = tmp_path / "cases.json"
    path.write_text(
        json.dumps(
            {
                "target_success_rate": 0.9,
                "cases": [
                    {
                        "id": "E01",
                        "category": "clear-domain",
                        "topic": "How are LLM agents evaluated?",
                        "objective": "Identify evaluation methods.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    payload = load_cases(path)

    assert payload["target_success_rate"] == 0.9
    assert payload["cases"][0]["id"] == "E01"


def test_load_cases_rejects_missing_required_field(tmp_path) -> None:
    path = tmp_path / "cases.json"
    path.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "id": "E01",
                        "category": "clear-domain",
                        "topic": "How are LLM agents evaluated?",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="objective"):
        load_cases(path)
