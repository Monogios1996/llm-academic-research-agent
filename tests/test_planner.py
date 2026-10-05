"""Unit tests for the LLM-powered planning role."""

import pytest

from research_agent.models import ResearchGoal
from research_agent.planner import Planner, PlanningError


class FakeGateway:
    """Deterministic test double that avoids live model/API calls."""

    def __init__(self, response: str) -> None:
        self.response = response
        self.last_prompt: str | None = None

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.response


def test_planner_creates_validated_plan() -> None:
    gateway = FakeGateway(
        """
        {
          "subtasks": [
            {
              "id": "q1",
              "question": "How are LLM planning agents architected?",
              "search_terms": ["LLM planning agents", "architecture"]
            },
            {
              "id": "q2",
              "question": "How are LLM planning agents evaluated?",
              "search_terms": ["LLM planning agents", "evaluation"]
            }
          ],
          "rationale": "Architecture and evaluation cover design and evidence."
        }
        """
    )
    planner = Planner(gateway=gateway, max_subtasks=4)
    goal = ResearchGoal(topic="LLM planning agents")

    plan = planner.create_plan(goal)

    assert len(plan.subtasks) == 2
    assert plan.subtasks[0].id == "q1"
    assert plan.goal.topic == "LLM planning agents"
    assert gateway.last_prompt is not None
    assert "Return JSON only" in gateway.last_prompt


def test_planner_rejects_invalid_json() -> None:
    planner = Planner(gateway=FakeGateway("not-json"))

    with pytest.raises(PlanningError, match="invalid JSON"):
        planner.create_plan(ResearchGoal(topic="academic planning agents"))


def test_planner_rejects_too_many_subtasks() -> None:
    gateway = FakeGateway(
        """
        {
          "subtasks": [
            {"id":"q1","question":"Question number one?","search_terms":["one"]},
            {"id":"q2","question":"Question number two?","search_terms":["two"]},
            {"id":"q3","question":"Question number three?","search_terms":["three"]}
          ],
          "rationale":"A deliberately excessive test plan."
        }
        """
    )
    planner = Planner(gateway=gateway, max_subtasks=2)

    with pytest.raises(PlanningError, match="maximum allowed"):
        planner.create_plan(ResearchGoal(topic="academic planning agents"))


def test_planner_rejects_invalid_structured_plan() -> None:
    gateway = FakeGateway(
        """
        {
          "subtasks": [
            {"id":"q1","question":"Short?","search_terms":[]}
          ]
        }
        """
    )
    planner = Planner(gateway=gateway)

    with pytest.raises(PlanningError, match="invalid research plan"):
        planner.create_plan(ResearchGoal(topic="academic planning agents"))
