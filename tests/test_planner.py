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
    assert '"id": "q2"' in gateway.last_prompt



def test_planner_recovers_json_from_markdown_fence() -> None:
    gateway = FakeGateway(
        """Here is the requested plan:
```json
{
  "subtasks": [
    {
      "id": "q1",
      "question": "How are planning agents evaluated?",
      "search_terms": ["planning agents", "evaluation"]
    },
    {
      "id": "q2",
      "question": "Which benchmarks are used?",
      "search_terms": ["planning agents", "benchmarks"]
    }
  ],
  "rationale": "Evaluation methods and benchmarks cover the objective."
}
```
"""
    )
    planner = Planner(gateway=gateway)

    plan = planner.create_plan(ResearchGoal(topic="LLM planning agents"))

    assert len(plan.subtasks) == 2
    assert plan.subtasks[1].id == "q2"


def test_planner_recovers_json_with_trailing_prose() -> None:
    gateway = FakeGateway(
        """A concise plan follows.
{
  "subtasks": [
    {
      "id": "q1",
      "question": "What reliability measures are reported?",
      "search_terms": ["LLM agents", "reliability"]
    },
    {
      "id": "q2",
      "question": "How is reproducibility assessed?",
      "search_terms": ["LLM agents", "reproducibility"]
    }
  ],
  "rationale": "The subtasks cover reliability and reproducibility."
}
This plan can now be executed."""
    )
    planner = Planner(gateway=gateway)

    plan = planner.create_plan(ResearchGoal(topic="LLM planning agents"))

    assert plan.rationale.startswith("The subtasks cover")


def test_planner_still_rejects_malformed_embedded_json() -> None:
    planner = Planner(
        gateway=FakeGateway(
            'Here is the plan: {"subtasks": [}'
        )
    )

    with pytest.raises(PlanningError, match="invalid JSON"):
        planner.create_plan(ResearchGoal(topic="academic planning agents"))


def test_planner_rejects_non_object_json() -> None:
    planner = Planner(gateway=FakeGateway('["not", "a", "plan"]'))

    with pytest.raises(PlanningError, match="invalid JSON object"):
        planner.create_plan(ResearchGoal(topic="academic planning agents"))

def test_planner_rejects_invalid_json() -> None:
    planner = Planner(gateway=FakeGateway("not-json"))

    with pytest.raises(PlanningError, match="invalid JSON"):
        planner.create_plan(ResearchGoal(topic="academic planning agents"))



def test_planner_rejects_single_subtask() -> None:
    gateway = FakeGateway(
        """
        {
          "subtasks": [
            {
              "id": "q1",
              "question": "What metrics are used to evaluate planning agents?",
              "search_terms": ["planning agents", "evaluation metrics"]
            }
          ],
          "rationale": "Only one subtask was returned."
        }
        """
    )
    planner = Planner(gateway=gateway, max_subtasks=3)

    with pytest.raises(PlanningError, match="minimum required is 2"):
        planner.create_plan(ResearchGoal(topic="LLM planning agents"))


def test_planner_requires_capacity_for_two_subtasks() -> None:
    with pytest.raises(ValueError, match="max_subtasks must be at least 2"):
        Planner(gateway=FakeGateway("{}"), max_subtasks=1)

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


def test_replanning_feedback_is_visible_in_prompt() -> None:
    gateway = FakeGateway(
        """
        {
          "subtasks": [
            {
              "id":"q1",
              "question":"How can traceability be improved?",
              "search_terms":["traceability", "academic evidence"]
            },
            {
              "id":"q2",
              "question":"Which identifiers support source verification?",
              "search_terms":["DOI", "source verification"]
            }
          ],
          "rationale":"The revised plan addresses the validation problem."
        }
        """
    )
    planner = Planner(gateway=gateway)

    planner.create_plan(
        ResearchGoal(topic="academic planning agents"),
        feedback=["Traceable evidence ratio is below the required threshold."],
    )

    assert gateway.last_prompt is not None
    assert "Previous validation feedback" in gateway.last_prompt
    assert "Traceable evidence ratio" in gateway.last_prompt
