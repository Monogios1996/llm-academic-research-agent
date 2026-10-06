"""Grounded summarisation for ranked academic evidence.

The summarisation stage uses the LLM only after deterministic retrieval and
ranking. Prompts explicitly constrain the model to supplied metadata so the
system does not treat unsupported model-generated claims as academic evidence.
"""

from __future__ import annotations

from collections.abc import Iterable

from research_agent.llm import LLMGateway
from research_agent.models import RankedEvidence, ResearchSubtask, ScoredRecord


class SummarisationError(RuntimeError):
    """Raised when the LLM does not return a usable evidence summary."""


class EvidenceSummariser:
    """Summarise ranked evidence while preserving source traceability."""

    def __init__(self, gateway: LLMGateway, max_summary_chars: int = 700) -> None:
        if max_summary_chars < 100:
            raise ValueError("max_summary_chars must be at least 100")
        self.gateway = gateway
        self.max_summary_chars = max_summary_chars

    def summarise(
        self,
        scored_record: ScoredRecord,
        subtask: ResearchSubtask,
    ) -> RankedEvidence:
        """Create one grounded summary from a scored academic record."""
        prompt = self._build_prompt(scored_record, subtask)
        summary = self.gateway.generate(prompt).strip()

        if not summary:
            raise SummarisationError("LLM returned an empty evidence summary")

        if len(summary) > self.max_summary_chars:
            summary = summary[: self.max_summary_chars].rstrip()

        record = scored_record.record
        return RankedEvidence(
            record=record,
            relevance_score=scored_record.relevance_score,
            summary=summary,
            traceable=bool(record.doi or record.url),
        )

    def summarise_many(
        self,
        scored_records: Iterable[ScoredRecord],
        subtask: ResearchSubtask,
    ) -> list[RankedEvidence]:
        """Summarise records in their existing ranked order."""
        return [self.summarise(item, subtask) for item in scored_records]

    def _build_prompt(
        self,
        scored_record: ScoredRecord,
        subtask: ResearchSubtask,
    ) -> str:
        record = scored_record.record
        authors = ", ".join(record.authors) if record.authors else "Not available"
        abstract = record.abstract or "Not available"
        doi = record.doi or "Not available"

        return f"""
You are the evidence-summarisation component of an academic research agent.

Research sub-question:
{subtask.question}

Use only the bibliographic metadata and abstract supplied below. Do not invent
methods, findings, sample sizes, quotations, or conclusions that are not present
in the supplied evidence. If the evidence is too limited, state that limitation
briefly.

Title: {record.title}
Authors: {authors}
Year: {record.year or "Not available"}
DOI: {doi}
Source: {record.source}
Abstract: {abstract}

Write a concise academic summary explaining how this record may contribute to
the research sub-question. Return plain text only.
""".strip()
