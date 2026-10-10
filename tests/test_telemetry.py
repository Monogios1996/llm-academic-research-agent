"""Tests for structured run telemetry."""

import json
from datetime import datetime, timezone

from research_agent.models import ResearchGoal, ResearchPlan, ResearchSubtask
from research_agent.telemetry import write_run_log


def test_write_run_log_records_traceable_execution_metadata(tmp_path) -> None:
    plan = ResearchPlan(
        goal=ResearchGoal(topic="LLM planning agents"),
        subtasks=[
            ResearchSubtask(
                id="q1",
                question="How are planning agents evaluated?",
                search_terms=["planning agents", "evaluation"],
            )
        ],
        rationale="Test plan.",
    )
    result = {
        "run_id": "run-123",
        "status": "awaiting_approval",
        "plan": plan,
        "all_evidence": [object(), object()],
        "audit_log": ["Plan created.", "Validation passed."],
    }
    started = datetime(2026, 10, 10, 8, 0, tzinfo=timezone.utc)
    finished = datetime(2026, 10, 10, 8, 0, 2, tzinfo=timezone.utc)

    path = write_run_log(
        result,
        model="hosted; qwen3:4b fallback",
        output_dir=tmp_path,
        started_at=started,
        finished_at=finished,
        fallback_calls=3,
        checkpoint_db="runtime/checkpoints.sqlite3",
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["run_id"] == "run-123"
    assert payload["duration_ms"] == 2000
    assert payload["status"] == "awaiting_approval"
    assert payload["fallback_calls"] == 3
    assert payload["evidence_count"] == 2
    assert payload["subtasks"][0]["id"] == "q1"
    assert payload["token_usage"] is None
    assert payload["estimated_cost"] is None


def test_write_run_log_requires_run_id(tmp_path) -> None:
    try:
        write_run_log(
            {"status": "failed"},
            model="test",
            output_dir=tmp_path,
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
        )
    except ValueError as exc:
        assert "run_id" in str(exc)
    else:
        raise AssertionError("Expected ValueError for missing run_id")
