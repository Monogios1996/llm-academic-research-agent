"""Grounded summarisation for ranked academic evidence.

The summarisation stage uses the LLM only after deterministic retrieval and
ranking. Prompts explicitly constrain the model to supplied metadata so the
system does not treat unsupported model-generated claims as academic evidence.
"""

from __future__ import annotations

import re
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
            summary = _truncate_summary(summary, self.max_summary_chars)

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
the research sub-question. Keep the summary within {self.max_summary_chars}
characters and use complete sentences. Return plain text only.
""".strip()



def _truncate_summary(summary: str, max_chars: int) -> str:
    """Shorten an overlong summary without leaving a broken sentence fragment."""
    text = summary.strip()
    if len(text) <= max_chars:
        return text

    candidate = text[:max_chars]
    sentence_ends = [
        match.end()
        for match in re.finditer(r"[.!?](?=\s|$)", candidate)
    ]
    minimum_useful_length = int(max_chars * 0.5)
    viable_ends = [
        end for end in sentence_ends
        if end >= minimum_useful_length
    ]
    if viable_ends:
        return candidate[:viable_ends[-1]].strip()

    # If no complete sentence fits, cut at a nearby word boundary and make the
    # truncation explicit instead of silently returning a broken word/sentence.
    body_limit = max_chars - 1
    body = text[:body_limit].rstrip()
    word_boundary = body.rfind(" ")
    if word_boundary >= int(max_chars * 0.6):
        body = body[:word_boundary]

    body = body.rstrip(" ,;:-")
    return f"{body}…"
