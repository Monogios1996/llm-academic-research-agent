"""Repeatable end-to-end evaluation harness for the research agent.

The assignment design calls for a varied evaluation set rather than a single
showcase query. This module runs a fixed JSON case set through the normal live
workflow, records structural success criteria, and writes a machine-readable
report without bypassing the human-approval boundary.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

from research_agent.bootstrap import build_live_workflow
from research_agent.llm import FailoverGateway
from research_agent.models import ResearchGoal
from research_agent.settings import ConfigurationError, LiveSettings


DEFAULT_CASES_PATH = "evaluation/cases.json"
DEFAULT_OUTPUT_DIR = "runtime/evaluation"
DEFAULT_CHECKPOINT_DB = "runtime/evaluation_checkpoints.sqlite3"


def load_cases(path: str | Path) -> dict[str, Any]:
    """Load and minimally validate the evaluation case manifest."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("evaluation manifest must contain a non-empty cases list")

    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("each evaluation case must be an object")
        for key in ("id", "category", "topic", "objective"):
            if not str(case.get(key, "")).strip():
                raise ValueError(f"evaluation case is missing required field: {key}")

    target = payload.get("target_success_rate", 0.90)
    if not isinstance(target, (int, float)) or not 0 <= target <= 1:
        raise ValueError("target_success_rate must be between 0 and 1")

    return payload


def evaluate_result(result: dict[str, Any]) -> dict[str, Any]:
    """Apply transparent structural success criteria to one completed run."""
    plan = result.get("plan")
    subtasks = len(plan.subtasks) if plan is not None else 0
    evidence = list(result.get("all_evidence", []))
    evidence_count = len(evidence)
    traceable_count = sum(1 for item in evidence if item.traceable)
    traceable_ratio = (
        traceable_count / evidence_count
        if evidence_count
        else 0.0
    )
    validation = result.get("validation")
    validation_passed = bool(
        validation is not None and getattr(validation, "passed", False)
    )

    passed = (
        result.get("status") == "awaiting_approval"
        and subtasks >= 2
        and evidence_count >= 2
        and traceable_ratio >= 0.75
        and validation_passed
    )

    return {
        "passed": passed,
        "status": result.get("status"),
        "run_id": result.get("run_id"),
        "subtask_count": subtasks,
        "evidence_count": evidence_count,
        "traceable_ratio": round(traceable_ratio, 4),
        "validation_passed": validation_passed,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the fixed end-to-end academic research evaluation set."
    )
    parser.add_argument(
        "--cases",
        default=DEFAULT_CASES_PATH,
        help=f"Evaluation manifest path (default: {DEFAULT_CASES_PATH}).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional number of cases for a partial smoke run.",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Report directory (default: {DEFAULT_OUTPUT_DIR}).",
    )
    parser.add_argument(
        "--checkpoint-db",
        default=DEFAULT_CHECKPOINT_DB,
        help=f"Checkpoint database (default: {DEFAULT_CHECKPOINT_DB}).",
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.limit is not None and args.limit < 1:
        raise SystemExit("--limit must be at least 1")

    manifest = load_cases(args.cases)
    all_cases = manifest["cases"]
    selected_cases = (
        all_cases[: args.limit]
        if args.limit is not None
        else all_cases
    )
    target = float(manifest.get("target_success_rate", 0.90))

    try:
        settings = LiveSettings.from_env()
    except ConfigurationError as exc:
        raise SystemExit(f"Configuration error: {exc}") from exc

    workflow = build_live_workflow(
        settings,
        checkpoint_db=args.checkpoint_db,
    )
    gateway = workflow.planner.gateway
    rows: list[dict[str, Any]] = []
    suite_started = datetime.now(timezone.utc)

    try:
        for index, case in enumerate(selected_cases, start=1):
            print(
                f"\n[{index}/{len(selected_cases)}] "
                f"{case['id']} — {case['topic']}"
            )
            started = perf_counter()
            fallback_before = (
                gateway.fallback_count
                if isinstance(gateway, FailoverGateway)
                else None
            )

            try:
                result = workflow.run(
                    ResearchGoal(
                        topic=case["topic"],
                        objective=case["objective"],
                    )
                )
                outcome = evaluate_result(result)
                error = None
            except Exception as exc:  # evaluation must record failures and continue
                outcome = {
                    "passed": False,
                    "status": "error",
                    "run_id": None,
                    "subtask_count": 0,
                    "evidence_count": 0,
                    "traceable_ratio": 0.0,
                    "validation_passed": False,
                }
                error = f"{type(exc).__name__}: {exc}"

            fallback_after = (
                gateway.fallback_count
                if isinstance(gateway, FailoverGateway)
                else None
            )
            fallback_calls = (
                fallback_after - fallback_before
                if fallback_before is not None and fallback_after is not None
                else None
            )
            duration_seconds = round(perf_counter() - started, 3)

            row = {
                "id": case["id"],
                "category": case["category"],
                "topic": case["topic"],
                "objective": case["objective"],
                **outcome,
                "duration_seconds": duration_seconds,
                "fallback_calls": fallback_calls,
                "error": error,
            }
            rows.append(row)

            label = "PASS" if row["passed"] else "FAIL"
            print(
                f"{label}: status={row['status']}, "
                f"subtasks={row['subtask_count']}, "
                f"evidence={row['evidence_count']}, "
                f"traceable={row['traceable_ratio']:.0%}, "
                f"fallback_calls={row['fallback_calls']}"
            )
            if error:
                print(f"Error: {error}")
    finally:
        workflow.close()

    passed_count = sum(1 for row in rows if row["passed"])
    total = len(rows)
    success_rate = passed_count / total if total else 0.0
    full_manifest_run = total == len(all_cases)

    report = {
        "suite_started_at": suite_started.isoformat(),
        "suite_finished_at": datetime.now(timezone.utc).isoformat(),
        "cases_file": str(args.cases),
        "full_manifest_run": full_manifest_run,
        "target_success_rate": target,
        "passed_cases": passed_count,
        "total_cases": total,
        "success_rate": round(success_rate, 4),
        "target_met": full_manifest_run and success_rate >= target,
        "success_criteria": {
            "status": "awaiting_approval",
            "minimum_subtasks": 2,
            "minimum_evidence_items": 2,
            "minimum_traceable_ratio": 0.75,
            "final_validation_passed": True,
        },
        "cases": rows,
    }

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = output_dir / f"evaluation-{stamp}.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\n=== Evaluation Summary ===")
    print(f"Passed: {passed_count}/{total}")
    print(f"Success rate: {success_rate:.1%}")
    if full_manifest_run:
        print(
            f"Target: {target:.0%} — "
            f"{'MET' if report['target_met'] else 'NOT MET'}"
        )
    else:
        print(
            f"Partial smoke run only; the {target:.0%} target is assessed "
            "only on the full manifest."
        )
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
