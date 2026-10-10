"""LangGraph orchestration for the academic research workflow.

LangGraph is used here for control flow rather than as a replacement for the
domain models. The graph keeps orchestration state lightweight while agent
boundaries continue to exchange validated Pydantic objects. This preserves the
Unit 6 separation between the Planner and Supervisor/Orchestrator roles.

The workflow is intentionally bounded:
plan -> retrieve -> process -> summarise -> validate.
Failed validation can trigger a targeted retrieval/processing retry. Once the
retry budget is exhausted, the failure is escalated to the Planner once for
re-planning. A final unresolved failure terminates cleanly rather than looping.
Successful completion stops at human approval; export is a later stage.
"""

from __future__ import annotations

from typing import Any, Literal, TypedDict
from uuid import uuid4

from langgraph.graph import END, START, StateGraph

from research_agent.models import (
    AcademicRecord,
    RankedEvidence,
    ResearchGoal,
    ResearchPlan,
    ResearchSubtask,
    ScoredRecord,
    ValidationResult,
)
from research_agent.planner import Planner
from research_agent.processing import deduplicate_evidence, process_records
from research_agent.retrieval import AcademicRetriever, retrieve_from_sources
from research_agent.summarisation import EvidenceSummariser
from research_agent.validation import EvidenceValidator


class WorkflowState(TypedDict, total=False):
    """Internal graph state.

    Pydantic models remain the messages crossing logical agent boundaries.
    TypedDict is used only for orchestration because LangGraph documents it as
    the normal lightweight state schema and the fields are replaced explicitly
    at each stage.
    """

    goal: ResearchGoal
    plan: ResearchPlan
    subtask_index: int
    current_subtask: ResearchSubtask
    retrieved_records: list[AcademicRecord]
    scored_records: list[ScoredRecord]
    ranked_evidence: list[RankedEvidence]
    all_evidence: list[RankedEvidence]
    validation: ValidationResult
    retry_count: int
    replan_count: int
    status: str
    failure_reason: str
    audit_log: list[str]
    run_id: str


class ResearchWorkflow:
    """Coordinate the specialised roles through a bounded LangGraph workflow."""

    def __init__(
        self,
        *,
        planner: Planner,
        retrievers: list[AcademicRetriever],
        summariser: EvidenceSummariser,
        validator: EvidenceValidator,
        retrieval_limit: int = 5,
        top_k: int = 5,
        max_retries: int = 1,
        max_replans: int = 1,
        checkpointer: Any | None = None,
        checkpoint_store: Any | None = None,
    ) -> None:
        if not retrievers:
            raise ValueError("At least one academic retriever is required")
        if retrieval_limit < 1:
            raise ValueError("retrieval_limit must be at least 1")
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        if max_retries < 0 or max_replans < 0:
            raise ValueError("Retry and re-plan limits cannot be negative")

        self.planner = planner
        self.retrievers = retrievers
        self.summariser = summariser
        self.validator = validator
        self.retrieval_limit = retrieval_limit
        self.top_k = top_k
        self.max_retries = max_retries
        self.max_replans = max_replans
        self.checkpointer = checkpointer
        self.checkpoint_store = checkpoint_store
        self.graph = self._build_graph()

    def close(self) -> None:
        """Release owned persistence resources, if configured."""
        if self.checkpoint_store is not None:
            self.checkpoint_store.close()

    def run(
        self,
        goal: ResearchGoal,
        *,
        thread_id: str | None = None,
    ) -> WorkflowState:
        """Execute the workflow with a traceable run/thread identifier."""
        run_id = thread_id or uuid4().hex
        initial_state: WorkflowState = {
            "goal": goal,
            "subtask_index": 0,
            "all_evidence": [],
            "retry_count": 0,
            "replan_count": 0,
            "status": "running",
            "audit_log": [],
            "run_id": run_id,
        }

        if self.checkpointer is None:
            return self.graph.invoke(initial_state)

        config = {"configurable": {"thread_id": run_id}}
        return self.graph.invoke(initial_state, config=config)

    def _build_graph(self):
        builder = StateGraph(WorkflowState)

        builder.add_node("plan", self._plan)
        builder.add_node("select_subtask", self._select_subtask)
        builder.add_node("retrieve", self._retrieve)
        builder.add_node("process", self._process)
        builder.add_node("summarise", self._summarise)
        builder.add_node("validate", self._validate)
        builder.add_node("prepare_retry", self._prepare_retry)
        builder.add_node("advance", self._advance)
        builder.add_node("replan", self._replan)
        builder.add_node("await_approval", self._await_approval)
        builder.add_node("fail", self._fail)

        builder.add_edge(START, "plan")
        builder.add_edge("plan", "select_subtask")
        builder.add_edge("select_subtask", "retrieve")
        builder.add_edge("retrieve", "process")
        builder.add_edge("process", "summarise")
        builder.add_edge("summarise", "validate")

        builder.add_conditional_edges("validate", self._route_after_validation)
        builder.add_conditional_edges("prepare_retry", self._route_retry_target)
        builder.add_conditional_edges("advance", self._route_after_advance)

        builder.add_edge("replan", "select_subtask")
        builder.add_edge("await_approval", END)
        builder.add_edge("fail", END)

        return builder.compile(checkpointer=self.checkpointer)

    def _plan(self, state: WorkflowState) -> dict:
        plan = self.planner.create_plan(state["goal"])
        return {
            "plan": plan,
            "subtask_index": 0,
            "status": "running",
            "audit_log": self._log(state, f"Plan created with {len(plan.subtasks)} subtasks."),
        }

    def _select_subtask(self, state: WorkflowState) -> dict:
        index = state["subtask_index"]
        subtask = state["plan"].subtasks[index]
        return {
            "current_subtask": subtask,
            "retrieved_records": [],
            "scored_records": [],
            "ranked_evidence": [],
            "retry_count": 0,
            "audit_log": self._log(state, f"Selected subtask {subtask.id}."),
        }

    def _retrieve(self, state: WorkflowState) -> dict:
        # A retrieval retry should change the search effort rather than repeat the
        # same request unchanged. The bounded retry therefore expands the result
        # window while preserving the same scholarly sources and sub-question.
        retry_count = state.get("retry_count", 0)
        effective_limit = self.retrieval_limit * (retry_count + 1)
        records = retrieve_from_sources(
            state["current_subtask"],
            self.retrievers,
            limit_per_source=effective_limit,
        )
        return {
            "retrieved_records": records,
            "audit_log": self._log(
                state,
                f"Retrieved {len(records)} record(s) "
                f"(limit {effective_limit} per source).",
            ),
        }

    def _process(self, state: WorkflowState) -> dict:
        scored = process_records(
            state["retrieved_records"],
            state["current_subtask"],
            top_k=self.top_k,
            min_relevance_score=self.validator.min_relevance_score,
        )

        # When validation specifically requests re-processing, weak items are
        # removed using the validator's explicit threshold. This makes the retry
        # materially different from the first pass. If too few items remain,
        # the next validation step redirects the workflow to retrieval.
        validation = state.get("validation")
        if (
            state.get("retry_count", 0) > 0
            and validation is not None
            and validation.retry_target == "processing"
        ):
            scored = [
                item
                for item in scored
                if item.relevance_score >= self.validator.min_relevance_score
            ]

        message = (
            f"Selected {len(scored)} top-ranked record(s) after relevance "
            f"filtering at threshold "
            f"{self.validator.min_relevance_score:.2f}."
        )

        return {
            "scored_records": scored,
            "audit_log": self._log(state, message),
        }

    def _summarise(self, state: WorkflowState) -> dict:
        evidence = self.summariser.summarise_many(
            state["scored_records"],
            state["current_subtask"],
        )
        return {
            "ranked_evidence": evidence,
            "audit_log": self._log(state, f"Summarised {len(evidence)} evidence item(s)."),
        }

    def _validate(self, state: WorkflowState) -> dict:
        result = self.validator.validate(state["ranked_evidence"])
        outcome = "passed" if result.passed else "failed"
        return {
            "validation": result,
            "audit_log": self._log(state, f"Evidence validation {outcome}."),
        }

    def _route_after_validation(
        self,
        state: WorkflowState,
    ) -> Literal["advance", "prepare_retry", "replan", "fail"]:
        if state["validation"].passed:
            return "advance"
        if state.get("retry_count", 0) < self.max_retries:
            return "prepare_retry"
        if state.get("replan_count", 0) < self.max_replans:
            return "replan"
        return "fail"

    def _prepare_retry(self, state: WorkflowState) -> dict:
        target = state["validation"].retry_target or "retrieval"
        return {
            "retry_count": state.get("retry_count", 0) + 1,
            "audit_log": self._log(
                state,
                f"Retry {state.get('retry_count', 0) + 1} routed to {target}.",
            ),
        }

    def _route_retry_target(
        self,
        state: WorkflowState,
    ) -> Literal["retrieve", "process"]:
        if state["validation"].retry_target == "processing":
            return "process"
        return "retrieve"

    def _advance(self, state: WorkflowState) -> dict:
        next_index = state["subtask_index"] + 1
        combined = state.get("all_evidence", []) + state["ranked_evidence"]
        accumulated = deduplicate_evidence(combined)
        duplicates_removed = len(combined) - len(accumulated)

        message = f"Accepted evidence for subtask {state['current_subtask'].id}."
        if duplicates_removed:
            message += (
                f" Removed {duplicates_removed} duplicate evidence item(s) "
                "during final aggregation."
            )

        return {
            "subtask_index": next_index,
            "all_evidence": accumulated,
            "retry_count": 0,
            "audit_log": self._log(state, message),
        }

    def _route_after_advance(
        self,
        state: WorkflowState,
    ) -> Literal["select_subtask", "await_approval"]:
        if state["subtask_index"] >= len(state["plan"].subtasks):
            return "await_approval"
        return "select_subtask"

    def _replan(self, state: WorkflowState) -> dict:
        issues = state["validation"].issues
        replanned = self.planner.create_plan(state["goal"], feedback=issues)
        return {
            "plan": replanned,
            "subtask_index": 0,
            "retrieved_records": [],
            "scored_records": [],
            "ranked_evidence": [],
            "all_evidence": [],
            "retry_count": 0,
            "replan_count": state.get("replan_count", 0) + 1,
            "audit_log": self._log(
                state,
                f"Escalated to Planner after validation failure; re-plan "
                f"{state.get('replan_count', 0) + 1} created.",
            ),
        }

    def _await_approval(self, state: WorkflowState) -> dict:
        return {
            "status": "awaiting_approval",
            "audit_log": self._log(
                state,
                "All subtasks validated; human approval required before export.",
            ),
        }

    def _fail(self, state: WorkflowState) -> dict:
        reason = "; ".join(state["validation"].issues) or "Validation failed."
        return {
            "status": "failed",
            "failure_reason": reason,
            "audit_log": self._log(
                state,
                "Workflow stopped after bounded retries and re-planning were exhausted.",
            ),
        }

    @staticmethod
    def _log(state: WorkflowState, message: str) -> list[str]:
        return [*state.get("audit_log", []), message]
