"""Minimal Streamlit demonstration interface for the research agent.

The UI intentionally stays thin: it exposes the existing workflow, evidence,
audit trail, and human-approval boundary without introducing a second
application architecture. The command-line interface remains available for
testing and reproducible evaluation.
"""

from __future__ import annotations

from datetime import datetime, timezone

import streamlit as st

from research_agent.bootstrap import build_live_workflow
from research_agent.exporter import export_research_package
from research_agent.llm import FailoverGateway
from research_agent.models import ResearchGoal
from research_agent.settings import ConfigurationError, LiveSettings
from research_agent.telemetry import write_run_log


CHECKPOINT_DB = "runtime/research_agent_checkpoints.sqlite3"
RUN_LOG_DIR = "runtime/run-logs"
OUTPUT_DIR = "outputs"


def _model_label(settings: LiveSettings, gateway) -> str:
    """Describe model provenance for logs and approved exports."""
    if isinstance(gateway, FailoverGateway) and gateway.fallback_count > 0:
        return (
            f"{settings.hf_model} (primary); "
            f"{settings.local_llm_model} "
            f"(fallback used {gateway.fallback_count} call(s))"
        )
    return settings.hf_model


def _run_agent(topic: str, objective: str) -> tuple[dict, str, str]:
    """Execute one live workflow and return result, model label, and log path."""
    settings = LiveSettings.from_env()
    workflow = build_live_workflow(
        settings,
        checkpoint_db=CHECKPOINT_DB,
    )
    started_at = datetime.now(timezone.utc)

    try:
        result = workflow.run(
            ResearchGoal(
                topic=topic.strip(),
                objective=objective.strip() or None,
            )
        )
        finished_at = datetime.now(timezone.utc)
        gateway = workflow.planner.gateway
        model_label = _model_label(settings, gateway)
        fallback_calls = (
            gateway.fallback_count
            if isinstance(gateway, FailoverGateway)
            else None
        )
        log_path = write_run_log(
            result,
            model=model_label,
            output_dir=RUN_LOG_DIR,
            started_at=started_at,
            finished_at=finished_at,
            fallback_calls=fallback_calls,
            checkpoint_db=CHECKPOINT_DB,
        )
        return result, model_label, str(log_path)
    finally:
        workflow.close()


def _show_result(result: dict, model_label: str, run_log: str) -> None:
    """Render the completed workflow result without hiding system evidence."""
    st.subheader("Run result")
    st.write(f"**Status:** {result['status']}")
    st.write(f"**Run ID:** {result['run_id']}")
    st.write(f"**Model provenance:** {model_label}")
    st.write(f"**Checkpoint database:** {CHECKPOINT_DB}")
    st.write(f"**Structured run log:** {run_log}")

    plan = result.get("plan")
    if plan is not None:
        st.subheader("Research plan")
        for subtask in plan.subtasks:
            st.write(f"**{subtask.id}** — {subtask.question}")

    evidence = list(result.get("all_evidence", []))
    st.subheader(f"Validated evidence ({len(evidence)})")
    for index, item in enumerate(evidence, start=1):
        record = item.record
        identifier = record.doi or str(record.url or "No DOI/URL")
        with st.expander(f"{index}. {record.title}", expanded=index <= 2):
            st.write(f"**Source:** {record.source}")
            st.write(f"**Identifier:** {identifier}")
            st.write(f"**Relevance:** {item.relevance_score:.2f}")
            st.write(f"**Traceable:** {'Yes' if item.traceable else 'No'}")
            st.write(item.summary)

    with st.expander("Audit trail"):
        for event in result.get("audit_log", []):
            st.write(f"- {event}")


def render_app() -> None:
    """Render the single-page university-project demonstration."""
    st.set_page_config(
        page_title="LLM Academic Research Agent",
        page_icon="📚",
        layout="centered",
    )
    st.title("LLM Academic Research Agent")
    st.caption(
        "University prototype: plan a research task, retrieve and validate "
        "academic evidence, then require human approval before export."
    )

    with st.form("research_form"):
        topic = st.text_input(
            "Research topic",
            placeholder="e.g. How are LLM planning agents evaluated?",
        )
        objective = st.text_area(
            "Objective (optional)",
            placeholder="e.g. Identify evaluation approaches and benchmarks.",
            height=90,
        )
        submitted = st.form_submit_button("Run Research Agent")

    if submitted:
        if len(topic.strip()) < 3:
            st.warning("Please enter a research topic.")
        else:
            try:
                with st.spinner("Running the research workflow..."):
                    result, model_label, run_log = _run_agent(
                        topic,
                        objective,
                    )
                st.session_state["research_result"] = result
                st.session_state["model_label"] = model_label
                st.session_state["run_log"] = run_log
                st.session_state.pop("export_paths", None)
            except ConfigurationError as exc:
                st.error(f"Configuration error: {exc}")
            except Exception as exc:
                st.error(
                    f"Workflow error: {type(exc).__name__}: {exc}"
                )

    result = st.session_state.get("research_result")
    if result is None:
        return

    model_label = st.session_state["model_label"]
    run_log = st.session_state["run_log"]
    _show_result(result, model_label, run_log)

    if result.get("status") == "awaiting_approval":
        st.info(
            "The workflow has stopped at the human-approval boundary. "
            "Review the plan and evidence before exporting."
        )
        if st.button("Approve & Export"):
            paths = export_research_package(
                result,
                model=model_label,
                output_dir=OUTPUT_DIR,
                approved=True,
            )
            st.session_state["export_paths"] = {
                label: str(path)
                for label, path in paths.items()
            }

    export_paths = st.session_state.get("export_paths")
    if export_paths:
        st.success("Export approved. Research package created.")
        for label, path in export_paths.items():
            st.write(f"**{label.title()}:** {path}")


if __name__ == "__main__":
    render_app()
