"""Evidence validation before approval and export.

Validation is deliberately rule-based at this stage so failures are observable
and can be routed to a specific remediation path. This implements the Unit 6
design principle that validation should trigger bounded retrieval or processing
retries rather than silently accepting weak evidence.
"""

from __future__ import annotations

from collections.abc import Iterable

from research_agent.models import RankedEvidence, ValidationResult


class EvidenceValidator:
    """Check whether processed evidence is sufficient for downstream export."""

    def __init__(
        self,
        *,
        min_items: int = 2,
        min_traceable_ratio: float = 0.75,
        min_relevance_score: float = 0.10,
    ) -> None:
        if min_items < 1:
            raise ValueError("min_items must be at least 1")
        if not 0.0 <= min_traceable_ratio <= 1.0:
            raise ValueError("min_traceable_ratio must be between 0 and 1")
        if not 0.0 <= min_relevance_score <= 1.0:
            raise ValueError("min_relevance_score must be between 0 and 1")

        self.min_items = min_items
        self.min_traceable_ratio = min_traceable_ratio
        self.min_relevance_score = min_relevance_score

    def validate(self, evidence: Iterable[RankedEvidence]) -> ValidationResult:
        """Return a structured result and a targeted remediation destination."""
        items = list(evidence)
        issues: list[str] = []
        retry_target: str | None = None

        if len(items) < self.min_items:
            issues.append(
                f"Only {len(items)} evidence item(s) available; "
                f"at least {self.min_items} required."
            )
            retry_target = "retrieval"

        if items:
            traceable_count = sum(item.traceable for item in items)
            traceable_ratio = traceable_count / len(items)
            if traceable_ratio < self.min_traceable_ratio:
                issues.append(
                    f"Traceable evidence ratio {traceable_ratio:.2f} is below "
                    f"required {self.min_traceable_ratio:.2f}."
                )
                retry_target = retry_target or "retrieval"

            weak_items = [
                item for item in items
                if item.relevance_score < self.min_relevance_score
            ]
            if weak_items:
                issues.append(
                    f"{len(weak_items)} evidence item(s) fall below the "
                    f"minimum relevance score of {self.min_relevance_score:.2f}."
                )
                retry_target = retry_target or "processing"

            empty_summaries = [item for item in items if not item.summary.strip()]
            if empty_summaries:
                issues.append(
                    f"{len(empty_summaries)} evidence item(s) have empty summaries."
                )
                retry_target = retry_target or "processing"

        return ValidationResult(
            passed=not issues,
            issues=issues,
            retry_target=retry_target,
        )
