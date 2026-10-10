"""Structured run-level telemetry for reproducible evaluation evidence.

The prototype records non-secret execution metadata as JSON so individual
research runs can be traced and compared without relying only on console
transcripts. Provider token/cost usage is left explicit as unavailable when the
current gateway does not expose it consistently.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_run_log(
    result: dict[str, Any],
    *,
    model: str,
    output_dir: str | Path,
    started_at: datetime,
    finished_at: datetime,
    fallback_calls: int | None = None,
    checkpoint_db: str | None = None,
) -> Path:
    """Write one structured JSON record for a completed workflow run."""
    run_id = str(result.get("run_id") or "").strip()
    if not run_id:
        raise ValueError("result must contain a non-empty run_id")

    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    if finished_at.tzinfo is None:
        finished_at = finished_at.replace(tzinfo=timezone.utc)

    duration_ms = max(
        0,
        int((finished_at - started_at).total_seconds() * 1000),
    )

    plan = result.get("plan")
    subtasks = []
    if plan is not None:
        subtasks = [
            {
                "id": item.id,
                "question": item.question,
            }
            for item in plan.subtasks
        ]

    payload = {
        "run_id": run_id,
        "started_at": started_at.astimezone(timezone.utc).isoformat(),
        "finished_at": finished_at.astimezone(timezone.utc).isoformat(),
        "duration_ms": duration_ms,
        "status": result.get("status"),
        "model": model,
        "fallback_calls": fallback_calls,
        "checkpoint_db": checkpoint_db,
        "subtasks": subtasks,
        "evidence_count": len(result.get("all_evidence", [])),
        "audit_log": list(result.get("audit_log", [])),
        "token_usage": None,
        "estimated_cost": None,
        "usage_note": (
            "Token and cost usage are not reported because the configured "
            "providers do not expose them consistently through this gateway."
        ),
    }

    path = destination / f"{run_id}.json"
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path
