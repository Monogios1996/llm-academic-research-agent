"""Command-line entry point for the live research-agent prototype.

The CLI displays the complete validated package before any consequential
export. SQLite checkpoints and structured run telemetry provide inspectable
execution evidence while explicit human approval remains mandatory for export.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

from research_agent.bootstrap import build_live_workflow
from research_agent.exporter import export_research_package
from research_agent.llm import FailoverGateway
from research_agent.models import ResearchGoal
from research_agent.settings import ConfigurationError, LiveSettings
from research_agent.telemetry import write_run_log


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the LLM-powered academic research planning agent."
    )
    parser.add_argument(
        "--topic",
        required=True,
        help="High-level academic research topic or question.",
    )
    parser.add_argument(
        "--objective",
        default=None,
        help="Optional research objective used by the Planner.",
    )
    parser.add_argument(
        "--prompt-for-approval",
        action="store_true",
        help=(
            "After displaying validated evidence, ask for explicit human "
            "approval before exporting Markdown/JSON/CSV files."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Directory used for approved exports (default: outputs).",
    )
    parser.add_argument(
        "--checkpoint-db",
        default="runtime/research_agent_checkpoints.sqlite3",
        help=(
            "SQLite file used for LangGraph checkpoints "
            "(default: runtime/research_agent_checkpoints.sqlite3)."
        ),
    )
    parser.add_argument(
        "--no-checkpointing",
        action="store_true",
        help="Disable SQLite checkpoint persistence for this run.",
    )
    parser.add_argument(
        "--run-log-dir",
        default="runtime/run-logs",
        help=(
            "Directory for structured JSON run logs "
            "(default: runtime/run-logs)."
        ),
    )
    return parser


def main() -> None:
    args = _parser().parse_args()

    try:
        settings = LiveSettings.from_env()
    except ConfigurationError as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc

    checkpoint_db = None if args.no_checkpointing else args.checkpoint_db
    workflow = build_live_workflow(
        settings,
        checkpoint_db=checkpoint_db,
    )
    started_at = datetime.now(timezone.utc)

    try:
        result = workflow.run(
            ResearchGoal(topic=args.topic, objective=args.objective)
        )
        finished_at = datetime.now(timezone.utc)

        print("\n=== Research Agent Result ===")
        print(f"Run ID: {result['run_id']}")
        print(f"Status: {result['status']}")
        print(f"Hosted model: {settings.hf_model}")
        if checkpoint_db:
            print(f"Checkpoint DB: {checkpoint_db}")
        else:
            print("Checkpointing: disabled")

        gateway = workflow.planner.gateway
        fallback_calls: int | None = None
        if isinstance(gateway, FailoverGateway):
            fallback_calls = gateway.fallback_count
            print(f"Local fallback enabled: yes ({settings.local_llm_model})")
            print(f"Local fallback calls: {gateway.fallback_count}")
        else:
            print("Local fallback enabled: no")

        plan = result.get("plan")
        if plan is not None:
            print("\nPlan:")
            for subtask in plan.subtasks:
                print(f"- {subtask.id}: {subtask.question}")

        evidence = result.get("all_evidence", [])
        print(f"\nValidated evidence items: {len(evidence)}")
        for index, item in enumerate(evidence, start=1):
            record = item.record
            identifier = record.doi or str(record.url or "No DOI/URL")
            print(f"\n{index}. {record.title}")
            print(f"   Source: {record.source}")
            print(f"   Identifier: {identifier}")
            print(f"   Relevance: {item.relevance_score:.2f}")
            print(f"   Summary: {item.summary}")

        print("\nAudit trail:")
        for event in result.get("audit_log", []):
            print(f"- {event}")

        model_label = settings.hf_model
        if isinstance(gateway, FailoverGateway) and gateway.fallback_count > 0:
            model_label = (
                f"{settings.hf_model} (primary); "
                f"{settings.local_llm_model} "
                f"(fallback used {gateway.fallback_count} call(s))"
            )

        run_log_path = write_run_log(
            result,
            model=model_label,
            output_dir=args.run_log_dir,
            started_at=started_at,
            finished_at=finished_at,
            fallback_calls=fallback_calls,
            checkpoint_db=checkpoint_db,
        )
        print(f"\nStructured run log: {run_log_path}")

        if result["status"] == "awaiting_approval":
            print(
                "\nThe workflow has stopped at the required human-approval boundary."
            )

            if args.prompt_for_approval:
                decision = input(
                    "Approve export of the validated research package? [y/N]: "
                ).strip().lower()
                if decision in {"y", "yes"}:
                    paths = export_research_package(
                        result,
                        model=model_label,
                        output_dir=args.output_dir,
                        approved=True,
                    )
                    print("\nExport approved. Files created:")
                    for label, path in paths.items():
                        print(f"- {label}: {path}")
                else:
                    print("Export not approved; no files were created.")
            else:
                print(
                    "No export has been performed. Re-run with "
                    "--prompt-for-approval to review and explicitly approve export."
                )
        elif result["status"] == "failed":
            print(
                f"\nFailure reason: "
                f"{result.get('failure_reason', 'Unknown')}"
            )
    finally:
        workflow.close()


if __name__ == "__main__":
    main()
