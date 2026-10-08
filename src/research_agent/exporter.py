"""Human-approved export of validated research evidence.

Export is intentionally separate from LangGraph execution. The workflow first
terminates at 'awaiting_approval' so a person can inspect the generated plan,
evidence, summaries, and audit trail. Only an explicit approval decision can
invoke this module and create persistent research-package files.
"""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from research_agent.models import RankedEvidence, ResearchGoal, ResearchPlan


class ExportApprovalError(RuntimeError):
    """Raised when export is attempted without the required human approval."""


def export_research_package(
    result: Mapping[str, Any],
    *,
    model: str,
    output_dir: str | Path,
    approved: bool,
) -> dict[str, Path]:
    """Write Markdown, JSON, and CSV outputs after explicit human approval.

    The function refuses to export unless the workflow has already reached the
    'awaiting_approval' state and the caller supplies approved=True. Keeping
    this guard in the export layer prevents a UI or CLI bug from bypassing the
    intended approval boundary.
    """
    if result.get("status") != "awaiting_approval":
        raise ExportApprovalError(
            "Research package can only be exported from awaiting_approval state"
        )
    if not approved:
        raise ExportApprovalError("Explicit human approval is required before export")

    goal = result.get("goal")
    plan = result.get("plan")
    evidence = result.get("all_evidence", [])

    if not isinstance(goal, ResearchGoal):
        raise ValueError("Workflow result is missing a valid ResearchGoal")
    if not isinstance(plan, ResearchPlan):
        raise ValueError("Workflow result is missing a valid ResearchPlan")
    if not all(isinstance(item, RankedEvidence) for item in evidence):
        raise ValueError("Workflow result contains invalid evidence items")

    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)

    stem = _safe_stem(goal.topic)
    paths = {
        "markdown": target / f"{stem}.md",
        "json": target / f"{stem}.json",
        "csv": target / f"{stem}.csv",
    }

    exported_at = datetime.now(timezone.utc).isoformat()
    payload = _build_payload(
        goal=goal,
        plan=plan,
        evidence=evidence,
        audit_log=list(result.get("audit_log", [])),
        model=model,
        exported_at=exported_at,
    )

    paths["json"].write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    paths["markdown"].write_text(
        _render_markdown(payload),
        encoding="utf-8",
    )
    _write_csv(paths["csv"], evidence)

    return paths


def _build_payload(
    *,
    goal: ResearchGoal,
    plan: ResearchPlan,
    evidence: list[RankedEvidence],
    audit_log: list[str],
    model: str,
    exported_at: str,
) -> dict[str, Any]:
    return {
        "run_metadata": {
            "exported_at_utc": exported_at,
            "model": model,
            "human_approved": True,
            "workflow_status_before_export": "awaiting_approval",
            "evidence_count": len(evidence),
        },
        "goal": goal.model_dump(mode="json"),
        "plan": plan.model_dump(mode="json"),
        "evidence": [item.model_dump(mode="json") for item in evidence],
        "audit_log": audit_log,
    }


def _render_markdown(payload: Mapping[str, Any]) -> str:
    goal = payload["goal"]
    plan = payload["plan"]
    metadata = payload["run_metadata"]
    evidence = payload["evidence"]

    lines = [
        "# Academic Research Evidence Package",
        "",
        f"**Topic:** {goal['topic']}",
    ]
    if goal.get("objective"):
        lines.append(f"**Objective:** {goal['objective']}")

    lines.extend(
        [
            "",
            "## Run metadata",
            "",
            f"- Model: {metadata['model']}",
            f"- Exported at (UTC): {metadata['exported_at_utc']}",
            "- Human approved: yes",
            f"- Unique evidence items: {metadata['evidence_count']}",
            "",
            "## Research plan",
            "",
        ]
    )

    for subtask in plan["subtasks"]:
        lines.append(f"- **{subtask['id']}** — {subtask['question']}")

    lines.extend(["", "## Evidence", ""])

    for index, item in enumerate(evidence, start=1):
        record = item["record"]
        lines.append(f"### {index}. {record['title']}")
        lines.append("")
        lines.append(f"- Source: {record['source']}")
        if record.get("authors"):
            lines.append(f"- Authors: {', '.join(record['authors'])}")
        if record.get("year"):
            lines.append(f"- Year: {record['year']}")
        if record.get("doi"):
            doi = record["doi"]
            doi_value = re.sub(r"^https?://(?:dx\\.)?doi\\.org/", "", doi, flags=re.I)
            lines.append(f"- DOI: https://doi.org/{doi_value}")
        elif record.get("url"):
            lines.append(f"- URL: {record['url']}")
        lines.append(f"- Relevance score: {item['relevance_score']:.2f}")
        lines.append(f"- Traceable: {'yes' if item['traceable'] else 'no'}")
        lines.extend(["", item["summary"], ""])

    lines.extend(["## Audit trail", ""])
    for event in payload["audit_log"]:
        lines.append(f"- {event}")

    lines.append("")
    return "\n".join(lines)


def _write_csv(path: Path, evidence: list[RankedEvidence]) -> None:
    fieldnames = [
        "title",
        "authors",
        "year",
        "doi",
        "url",
        "source",
        "relevance_score",
        "traceable",
        "summary",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in evidence:
            record = item.record
            writer.writerow(
                {
                    "title": record.title,
                    "authors": "; ".join(record.authors),
                    "year": record.year or "",
                    "doi": record.doi or "",
                    "url": str(record.url or ""),
                    "source": record.source,
                    "relevance_score": item.relevance_score,
                    "traceable": item.traceable,
                    "summary": item.summary,
                }
            )


def _safe_stem(topic: str) -> str:
    normalised = re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-")
    return normalised[:70].rstrip("-") or "research-package"
