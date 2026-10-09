"""Planning role for decomposing a research goal into searchable subtasks.

The Planner is deliberately separate from orchestration. It produces an
inspectable plan before retrieval starts, matching the Plan-and-Execute design
from the Unit 6 proposal. Structured JSON is required from the model so that
the plan can be validated before any downstream action is allowed.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from research_agent.llm import LLMGateway
from research_agent.models import ResearchGoal, ResearchPlan


class PlanningError(RuntimeError):
    """Raised when the LLM output cannot be converted into a valid plan."""


class Planner:
    """Generate a validated research plan from a high-level goal."""

    def __init__(self, gateway: LLMGateway, max_subtasks: int = 5) -> None:
        if max_subtasks < 1:
            raise ValueError("max_subtasks must be at least 1")
        self.gateway = gateway
        self.max_subtasks = max_subtasks

    def create_plan(
        self,
        goal: ResearchGoal,
        feedback: list[str] | None = None,
    ) -> ResearchPlan:
        """Ask the model for a structured plan and validate the result.

        Validation feedback is optional and is used only during bounded
        re-planning. Keeping feedback explicit makes the escalation path
        inspectable instead of silently changing planner behaviour.
        """
        raw_output = self.gateway.generate(self._build_prompt(goal, feedback))
        payload = _load_json_object(raw_output)

        payload["goal"] = goal.model_dump()

        try:
            plan = ResearchPlan.model_validate(payload)
        except ValidationError as exc:
            raise PlanningError("Planner returned an invalid research plan") from exc

        if len(plan.subtasks) > self.max_subtasks:
            raise PlanningError(
                f"Planner returned {len(plan.subtasks)} subtasks; "
                f"maximum allowed is {self.max_subtasks}"
            )

        return plan

    def _build_prompt(
        self,
        goal: ResearchGoal,
        feedback: list[str] | None = None,
    ) -> str:
        """Construct a constrained prompt that exposes planning before execution."""
        objective = goal.objective or "Produce a traceable academic research package."
        feedback_text = ""
        if feedback:
            feedback_text = (
                "\n\nPrevious validation feedback to address during re-planning:\n- "
                + "\n- ".join(feedback)
            )

        return f"""
You are the planning component of an academic research agent.

Research topic:
{goal.topic}

Research objective:
{objective}{feedback_text}

Decompose the goal into between 2 and {self.max_subtasks} focused, searchable
academic sub-questions. Each subtask must be useful for structured scholarly
metadata retrieval from sources such as Crossref or OpenAlex.

Return JSON only, using exactly this shape:
{{
  "subtasks": [
    {{
      "id": "q1",
      "question": "A focused research question",
      "search_terms": ["term one", "term two"]
    }}
  ],
  "rationale": "Brief explanation of why this decomposition covers the goal."
}}

Do not include Markdown fences or any text outside the JSON object.
""".strip()


def _load_json_object(raw_output: str) -> dict[str, Any]:
    """Parse one planner JSON object without weakening plan validation.

    Hosted models normally obey the JSON-only instruction, so the complete
    response is parsed first. Some local instruction-tuned models prepend a
    short explanation or Markdown fence even when told not to. In that case,
    the parser makes one bounded recovery attempt from the first opening brace
    and uses JSONDecoder.raw_decode so trailing prose/fences are ignored.

    This is intentionally not a general "repair" routine: malformed JSON is
    still rejected, and the recovered value must still be an object before
    Pydantic validates the full ResearchPlan schema.
    """
    text = raw_output.strip()
    if not text:
        raise PlanningError("Planner returned invalid JSON")

    try:
        decoded = json.loads(text)
    except json.JSONDecodeError:
        first_object = text.find("{")
        if first_object < 0:
            raise PlanningError("Planner returned invalid JSON")

        try:
            decoded, _ = json.JSONDecoder().raw_decode(text[first_object:])
        except json.JSONDecodeError as exc:
            raise PlanningError("Planner returned invalid JSON") from exc

    if not isinstance(decoded, dict):
        raise PlanningError("Planner returned invalid JSON object")

    return decoded
