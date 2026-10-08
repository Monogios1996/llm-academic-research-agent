"""Tests for the explicit approval and export boundary."""

import csv
import json

import pytest

from research_agent.exporter import ExportApprovalError, export_research_package
from research_agent.models import (
    AcademicRecord,
    RankedEvidence,
    ResearchGoal,
    ResearchPlan,
    ResearchSubtask,
)


def _result(status: str = "awaiting_approval") -> dict:
    goal = ResearchGoal(
        topic="LLM planning agents",
        objective="Review evaluation approaches.",
    )
    plan = ResearchPlan(
        goal=goal,
        subtasks=[
            ResearchSubtask(
                id="q1",
                question="How are LLM planning agents evaluated?",
                search_terms=["LLM planning", "evaluation"],
            )
        ],
        rationale="One focused research question.",
    )
    evidence = [
        RankedEvidence(
            record=AcademicRecord(
                title="Agent Planning Benchmark",
                authors=["A. Researcher"],
                year=2026,
                doi="10.1234/example",
                source="OpenAlex",
                url="https://example.org/paper",
                abstract="Evaluation benchmark for planning agents.",
            ),
            relevance_score=0.8,
            summary="The paper presents a planning-agent evaluation benchmark.",
            traceable=True,
        )
    ]
    return {
        "status": status,
        "goal": goal,
        "plan": plan,
        "all_evidence": evidence,
        "audit_log": [
            "Plan created with 1 subtask.",
            "All subtasks validated; human approval required before export.",
        ],
    }


def test_export_refuses_missing_human_approval(tmp_path) -> None:
    with pytest.raises(ExportApprovalError, match="Explicit human approval"):
        export_research_package(
            _result(),
            model="test-model",
            output_dir=tmp_path,
            approved=False,
        )

    assert list(tmp_path.iterdir()) == []


def test_export_refuses_non_approval_workflow_state(tmp_path) -> None:
    with pytest.raises(ExportApprovalError, match="awaiting_approval"):
        export_research_package(
            _result(status="failed"),
            model="test-model",
            output_dir=tmp_path,
            approved=True,
        )

    assert list(tmp_path.iterdir()) == []


def test_approved_export_writes_markdown_json_and_csv(tmp_path) -> None:
    paths = export_research_package(
        _result(),
        model="test-model",
        output_dir=tmp_path,
        approved=True,
    )

    assert set(paths) == {"markdown", "json", "csv"}
    assert all(path.exists() for path in paths.values())

    payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert payload["run_metadata"]["human_approved"] is True
    assert payload["run_metadata"]["evidence_count"] == 1
    assert payload["goal"]["topic"] == "LLM planning agents"

    markdown = paths["markdown"].read_text(encoding="utf-8")
    assert "# Academic Research Evidence Package" in markdown
    assert "https://doi.org/10.1234/example" in markdown
    assert "Human approved: yes" in markdown

    with paths["csv"].open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["title"] == "Agent Planning Benchmark"
    assert rows[0]["doi"] == "10.1234/example"
