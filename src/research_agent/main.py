"""Command-line entry point for the live research-agent prototype.

The CLI intentionally ends at the human-approval boundary. Export is not
performed here because the Unit 6 design requires explicit approval before the
final consequential action.
"""

from __future__ import annotations

import argparse

from research_agent.bootstrap import build_live_workflow
from research_agent.exporter import export_research_package
from research_agent.models import ResearchGoal
from research_agent.settings import ConfigurationError, LiveSettings


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
    return parser


def main() -> None:
    args = _parser().parse_args()

    try:
        settings = LiveSettings.from_env()
    except ConfigurationError as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc

    workflow = build_live_workflow(settings)
    result = workflow.run(
        ResearchGoal(topic=args.topic, objective=args.objective)
    )

    print("\n=== Research Agent Result ===")
    print(f"Status: {result['status']}")
    print(f"Model: {settings.hf_model}")

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
                    model=settings.hf_model,
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
        print(f"\nFailure reason: {result.get('failure_reason', 'Unknown')}")


if __name__ == "__main__":
    main()
