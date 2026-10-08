"""Deterministic processing and ranking of retrieved academic metadata.

The processing stage is intentionally separated from LLM summarisation.
Deduplication and relevance scoring are deterministic so they can be inspected,
tested, and reproduced independently of model variability.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from research_agent.models import AcademicRecord, RankedEvidence, ResearchSubtask, ScoredRecord


_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "how", "in", "is", "of", "on", "or", "that", "the", "to", "what",
    "when", "where", "which", "with",
}


def process_records(
    records: Iterable[AcademicRecord],
    subtask: ResearchSubtask,
    *,
    top_k: int = 10,
) -> list[ScoredRecord]:
    """Deduplicate, score, and rank records for one research subtask."""
    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    unique_records = deduplicate_records(records)
    scored = [
        ScoredRecord(record=record, relevance_score=relevance_score(record, subtask))
        for record in unique_records
    ]

    scored.sort(
        key=lambda item: (
            item.relevance_score,
            _metadata_completeness(item.record),
            item.record.year or 0,
        ),
        reverse=True,
    )
    return scored[:top_k]


def deduplicate_records(records: Iterable[AcademicRecord]) -> list[AcademicRecord]:
    """Collapse duplicate works, preferring the record with richer metadata.

    DOI is the strongest available identifier. When DOI is absent, a normalised
    title is used as a conservative fallback so that the same work retrieved
    from multiple providers is not counted twice.
    """
    best_by_key: dict[str, AcademicRecord] = {}

    for record in records:
        key = _record_key(record)
        existing = best_by_key.get(key)
        if existing is None or _metadata_completeness(record) > _metadata_completeness(existing):
            best_by_key[key] = record

    return list(best_by_key.values())


def deduplicate_evidence(items: Iterable[RankedEvidence]) -> list[RankedEvidence]:
    """Collapse duplicate works across the final multi-subtask evidence package.

    Validation is deliberately performed per subtask before this step so that
    each research question must still gather enough support independently.
    During final aggregation, DOI is used as the primary identity key and a
    normalised title is the fallback. When the same work supported more than
    one subtask, the stronger evidence instance is retained using relevance,
    metadata completeness, and summary length as deterministic tie-breakers.
    """
    best_by_key: dict[str, RankedEvidence] = {}

    for item in items:
        key = _record_key(item.record)
        existing = best_by_key.get(key)
        if existing is None or _evidence_quality(item) > _evidence_quality(existing):
            best_by_key[key] = item

    return list(best_by_key.values())


def relevance_score(record: AcademicRecord, subtask: ResearchSubtask) -> float:
    """Return a transparent lexical relevance score between zero and one.

    Title matches receive the greatest weight because titles are concise signals
    of topic relevance. Abstract matches provide supporting evidence without
    allowing a long abstract to dominate the ranking.
    """
    query_tokens = _query_tokens(subtask)
    if not query_tokens:
        return 0.0

    title_tokens = _tokenise(record.title)
    abstract_tokens = _tokenise(record.abstract or "")
    combined_tokens = title_tokens | abstract_tokens

    title_coverage = len(query_tokens & title_tokens) / len(query_tokens)
    combined_coverage = len(query_tokens & combined_tokens) / len(query_tokens)

    score = (0.7 * title_coverage) + (0.3 * combined_coverage)
    return round(min(max(score, 0.0), 1.0), 4)


def _query_tokens(subtask: ResearchSubtask) -> set[str]:
    raw = " ".join([subtask.question, *subtask.search_terms])
    return {token for token in _tokenise(raw) if token not in _STOPWORDS}


def _tokenise(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _record_key(record: AcademicRecord) -> str:
    if record.doi:
        doi = record.doi.lower().strip()
        doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi)
        return f"doi:{doi}"

    normalised_title = " ".join(re.findall(r"[a-z0-9]+", record.title.lower()))
    return f"title:{normalised_title}"


def _evidence_quality(item: RankedEvidence) -> tuple[float, int, int]:
    """Return a deterministic quality tuple for duplicate evidence selection."""
    return (
        item.relevance_score,
        _metadata_completeness(item.record),
        len(item.summary.strip()),
    )


def _metadata_completeness(record: AcademicRecord) -> int:
    """Score metadata richness for deterministic duplicate selection."""
    return sum(
        [
            3 if record.doi else 0,
            2 if record.abstract else 0,
            1 if record.url else 0,
            1 if record.authors else 0,
            1 if record.year else 0,
        ]
    )
