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

    def create_plan(self, goal: ResearchGoal) -> ResearchPlan:
        """Ask the model for a structured plan and validate the result."""
        raw_output = self.gateway.generate(self._build_prompt(goal))

        try:
            payload: dict[str, Any] = json.loads(raw_output)
        except json.JSONDecodeError as exc:
            raise PlanningError("Planner returned invalid JSON") from exc

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

    def _build_prompt(self, goal: ResearchGoal) -> str:
        """Construct a constrained prompt that exposes planning before execution."""
        objective = goal.objective or "Produce a traceable academic research package."

        return f"""
You are the planning component of an academic research agent.

Research topic:
{goal.topic}

Research objective:
{objective}

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
