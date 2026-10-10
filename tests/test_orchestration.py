"""Integration-style tests for bounded LangGraph orchestration.

External APIs and the LLM remain deterministic test doubles here. The purpose
is to verify state transitions, routing, retry limits, re-planning, and the
human-approval boundary independently of network availability.
"""

from langgraph.checkpoint.memory import InMemorySaver

from research_agent.models import (
    AcademicRecord,
    RankedEvidence,
    ResearchGoal,
    ResearchPlan,
    ResearchSubtask,
)
from research_agent.orchestration import ResearchWorkflow
from research_agent.validation import EvidenceValidator


class FakePlanner:
    def __init__(self, plans: list[ResearchPlan]) -> None:
        self.plans = plans
        self.calls = 0
        self.feedback: list[list[str] | None] = []

    def create_plan(
        self,
        goal: ResearchGoal,
        feedback: list[str] | None = None,
    ) -> ResearchPlan:
        self.feedback.append(feedback)
        plan = self.plans[min(self.calls, len(self.plans) - 1)]
        self.calls += 1
        return plan


class SequenceRetriever:
    def __init__(self, batches: list[list[AcademicRecord]]) -> None:
        self.batches = batches
        self.calls = 0

    def search(self, subtask: ResearchSubtask, limit: int = 5) -> list[AcademicRecord]:
        batch = self.batches[min(self.calls, len(self.batches) - 1)]
        self.calls += 1
        return batch[:limit]


class FakeSummariser:
    def summarise_many(self, scored_records, subtask):
        return [
            RankedEvidence(
                record=item.record,
                relevance_score=item.relevance_score,
                summary=f"Evidence relevant to {subtask.id}: {item.record.title}",
                traceable=bool(item.record.doi or item.record.url),
            )
            for item in scored_records
        ]


def _goal() -> ResearchGoal:
    return ResearchGoal(topic="LLM planning agents")


def _plan(question: str = "How are LLM planning agents evaluated?") -> ResearchPlan:
    return ResearchPlan(
        goal=_goal(),
        subtasks=[
            ResearchSubtask(
                id="q1",
                question=question,
                search_terms=["LLM", "planning", "agents", "evaluation"],
            )
        ],
        rationale="A focused demonstrator plan.",
    )


def _record(title: str, doi: str | None = None) -> AcademicRecord:
    return AcademicRecord(
        title=title,
        source="Crossref",
        doi=doi,
        abstract="LLM planning agents evaluation evidence.",
    )


def test_workflow_reaches_human_approval_after_valid_evidence() -> None:
    planner = FakePlanner([_plan()])
    retriever = SequenceRetriever(
        [[
            _record("LLM Planning Agents Evaluation", "10.1/a"),
            _record("Evaluation of LLM Planning Agents", "10.1/b"),
        ]]
    )
    workflow = ResearchWorkflow(
        planner=planner,
        retrievers=[retriever],
        summariser=FakeSummariser(),
        validator=EvidenceValidator(min_items=2, min_traceable_ratio=1.0),
        max_retries=1,
        max_replans=1,
    )

    result = workflow.run(_goal())

    assert result["status"] == "awaiting_approval"
    assert len(result["all_evidence"]) == 2
    assert result["validation"].passed is True
    assert any("human approval required" in item for item in result["audit_log"])


def test_processing_audit_does_not_mislabel_top_k_exclusions() -> None:
    planner = FakePlanner([_plan()])
    retriever = SequenceRetriever(
        [[
            _record("LLM Planning Agents Evaluation A", "10.1/a"),
            _record("LLM Planning Agents Evaluation B", "10.1/b"),
            _record("LLM Planning Agents Evaluation C", "10.1/c"),
        ]]
    )
    workflow = ResearchWorkflow(
        planner=planner,
        retrievers=[retriever],
        summariser=FakeSummariser(),
        validator=EvidenceValidator(
            min_items=2,
            min_traceable_ratio=1.0,
            min_relevance_score=0.10,
        ),
        top_k=2,
        max_retries=0,
        max_replans=0,
    )

    result = workflow.run(_goal())

    audit = " ".join(result["audit_log"])
    assert "Selected 2 top-ranked record(s)" in audit
    assert "below the relevance threshold" not in audit


def test_failed_validation_triggers_targeted_retrieval_retry() -> None:
    planner = FakePlanner([_plan()])
    retriever = SequenceRetriever(
        [
            [_record("LLM Planning Agents Evaluation", "10.1/a")],
            [
                _record("LLM Planning Agents Evaluation", "10.1/a"),
                _record("Evaluation of LLM Planning Agents", "10.1/b"),
            ],
        ]
    )
    workflow = ResearchWorkflow(
        planner=planner,
        retrievers=[retriever],
        summariser=FakeSummariser(),
        validator=EvidenceValidator(min_items=2, min_traceable_ratio=1.0),
        max_retries=1,
        max_replans=0,
    )

    result = workflow.run(_goal())

    assert result["status"] == "awaiting_approval"
    assert retriever.calls == 2
    assert any("Retry 1 routed to retrieval" in item for item in result["audit_log"])


def test_exhausted_retry_escalates_failure_feedback_to_planner() -> None:
    initial = _plan()
    revised = _plan("Which evaluation evidence is most traceable?")
    planner = FakePlanner([initial, revised])
    retriever = SequenceRetriever(
        [
            [_record("LLM Planning Agents Evaluation")],
            [
                _record("Traceable LLM Planning Evaluation", "10.2/a"),
                _record("Planning Agent Evaluation Evidence", "10.2/b"),
            ],
        ]
    )
    workflow = ResearchWorkflow(
        planner=planner,
        retrievers=[retriever],
        summariser=FakeSummariser(),
        validator=EvidenceValidator(min_items=2, min_traceable_ratio=1.0),
        max_retries=0,
        max_replans=1,
    )

    result = workflow.run(_goal())

    assert result["status"] == "awaiting_approval"
    assert planner.calls == 2
    assert planner.feedback[0] is None
    assert planner.feedback[1]
    assert any("Escalated to Planner" in item for item in result["audit_log"])


def test_workflow_fails_cleanly_when_all_budgets_are_exhausted() -> None:
    planner = FakePlanner([_plan()])
    retriever = SequenceRetriever(
        [[_record("Weak untraceable evidence")]]
    )
    workflow = ResearchWorkflow(
        planner=planner,
        retrievers=[retriever],
        summariser=FakeSummariser(),
        validator=EvidenceValidator(min_items=2, min_traceable_ratio=1.0),
        max_retries=0,
        max_replans=0,
    )

    result = workflow.run(_goal())

    assert result["status"] == "failed"
    assert "at least 2 required" in result["failure_reason"]
    assert any("bounded retries" in item for item in result["audit_log"])


def test_final_aggregation_deduplicates_work_reused_across_subtasks() -> None:
    goal = _goal()
    plan = ResearchPlan(
        goal=goal,
        subtasks=[
            ResearchSubtask(
                id="q1",
                question="How are LLM planning agents evaluated?",
                search_terms=["LLM", "planning", "agents", "evaluation"],
            ),
            ResearchSubtask(
                id="q2",
                question="Which benchmarks evaluate LLM planning agents?",
                search_terms=["LLM", "planning", "agents", "benchmarks"],
            ),
        ],
        rationale="Two related questions can legitimately retrieve the same paper.",
    )
    planner = FakePlanner([plan])
    retriever = SequenceRetriever(
        [
            [
                _record("Shared Planning Benchmark", "10.1/shared"),
                _record("Evaluation Methods", "10.1/methods"),
            ],
            [
                _record("Shared Planning Benchmark", "10.1/shared"),
                _record("Benchmark Dataset Study", "10.1/dataset"),
            ],
        ]
    )
    workflow = ResearchWorkflow(
        planner=planner,
        retrievers=[retriever],
        summariser=FakeSummariser(),
        validator=EvidenceValidator(min_items=2, min_traceable_ratio=1.0),
        max_retries=0,
        max_replans=0,
    )

    result = workflow.run(goal)

    assert result["status"] == "awaiting_approval"
    assert len(result["all_evidence"]) == 3
    assert sum(
        item.record.doi == "10.1/shared" for item in result["all_evidence"]
    ) == 1
    assert any(
        "Removed 1 duplicate evidence item" in event
        for event in result["audit_log"]
    )


def test_workflow_persists_state_with_explicit_thread_id() -> None:
    planner = FakePlanner([_plan()])
    retriever = SequenceRetriever(
        [[
            _record("LLM Planning Agents Evaluation", "10.1/a"),
            _record("Evaluation of LLM Planning Agents", "10.1/b"),
        ]]
    )
    checkpointer = InMemorySaver()
    workflow = ResearchWorkflow(
        planner=planner,
        retrievers=[retriever],
        summariser=FakeSummariser(),
        validator=EvidenceValidator(min_items=2, min_traceable_ratio=1.0),
        max_retries=0,
        max_replans=0,
        checkpointer=checkpointer,
    )

    result = workflow.run(_goal(), thread_id="evaluation-run-001")
    snapshot = workflow.graph.get_state(
        {"configurable": {"thread_id": "evaluation-run-001"}}
    )

    assert result["run_id"] == "evaluation-run-001"
    assert snapshot.values["run_id"] == "evaluation-run-001"
    assert snapshot.values["status"] == "awaiting_approval"
    assert snapshot.values["all_evidence"]
