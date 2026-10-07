"""Construction helpers for the live academic research workflow.

This module contains dependency wiring only. Keeping object construction out of
the domain modules makes the live configuration easy to inspect and keeps unit
tests free to inject deterministic substitutes.
"""

from __future__ import annotations

from research_agent.huggingface import HuggingFaceGateway
from research_agent.orchestration import ResearchWorkflow
from research_agent.planner import Planner
from research_agent.retrieval import CrossrefRetriever, OpenAlexRetriever
from research_agent.settings import LiveSettings
from research_agent.summarisation import EvidenceSummariser
from research_agent.validation import EvidenceValidator


def build_live_workflow(settings: LiveSettings) -> ResearchWorkflow:
    """Build the bounded live workflow from runtime configuration."""
    gateway = HuggingFaceGateway(
        token=settings.hf_token,
        model=settings.hf_model,
    )

    planner = Planner(gateway=gateway, max_subtasks=3)
    summariser = EvidenceSummariser(gateway=gateway, max_summary_chars=600)

    retrievers = [
        CrossrefRetriever(email=settings.crossref_email),
        OpenAlexRetriever(api_key=settings.openalex_api_key),
    ]

    validator = EvidenceValidator(
        min_items=2,
        min_traceable_ratio=0.75,
        min_relevance_score=0.10,
    )

    return ResearchWorkflow(
        planner=planner,
        retrievers=retrievers,
        summariser=summariser,
        validator=validator,
        retrieval_limit=3,
        top_k=3,
        max_retries=1,
        max_replans=1,
    )
