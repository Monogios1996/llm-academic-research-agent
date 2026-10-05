"""Unit tests for shared workflow models."""

import pytest
from pydantic import ValidationError

from research_agent.models import (
    AcademicRecord,
    AgentState,
    ResearchGoal,
    ResearchPlan,
    ResearchSubtask,
    StepStatus,
)


def test_research_plan_accepts_valid_subtasks() -> None:
    goal = ResearchGoal(topic="LLM planning agents")
    subtask = ResearchSubtask(
        id="q1",
        question="How are LLM planning agents evaluated?",
        search_terms=["LLM planning agents", "evaluation"],
    )

    plan = ResearchPlan(goal=goal, subtasks=[subtask])

    assert plan.goal.topic == "LLM planning agents"
    assert plan.subtasks[0].status == StepStatus.PENDING


def test_research_plan_rejects_empty_subtask_list() -> None:
    goal = ResearchGoal(topic="LLM planning agents")

    with pytest.raises(ValidationError):
        ResearchPlan(goal=goal, subtasks=[])


def test_agent_state_defaults_to_unapproved_export() -> None:
    state = AgentState(goal=ResearchGoal(topic="academic research agents"))

    assert state.approved_for_export is False
    assert state.retrieved_records == []


def test_academic_record_supports_traceable_metadata() -> None:
    record = AcademicRecord(
        title="Example study",
        authors=["A. Researcher"],
        year=2025,
        doi="10.0000/example",
        source="Crossref",
        url="https://example.org/study",
    )

    assert record.source == "Crossref"
    assert record.doi == "10.0000/example"
