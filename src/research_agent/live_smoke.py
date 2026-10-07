"""Minimal live-provider smoke test.

This module deliberately tests each external dependency once rather than
running a full research workflow. It is intended to establish that credentials,
network access, and provider response parsing work before spending model credits
on a complete multi-step demonstration.
"""

from __future__ import annotations

from research_agent.huggingface import HuggingFaceGateway
from research_agent.models import ResearchSubtask
from research_agent.retrieval import CrossrefRetriever, OpenAlexRetriever
from research_agent.settings import LiveSettings


def main() -> None:
    settings = LiveSettings.from_env()

    gateway = HuggingFaceGateway(
        token=settings.hf_token,
        model=settings.hf_model,
        max_tokens=40,
        temperature=0.0,
    )
    model_output = gateway.generate(
        "Reply in one short sentence confirming that the model connection works."
    )
    print(f"Hugging Face: OK - {model_output[:120]}")

    subtask = ResearchSubtask(
        id="smoke",
        question="How are LLM planning agents evaluated?",
        search_terms=["LLM planning agents", "evaluation"],
    )

    crossref = CrossrefRetriever(email=settings.crossref_email)
    crossref_records = crossref.search(subtask, limit=1)
    if not crossref_records:
        raise RuntimeError("Crossref returned no records for the smoke query")
    print(f"Crossref: OK - {crossref_records[0].title[:120]}")

    openalex = OpenAlexRetriever(api_key=settings.openalex_api_key)
    openalex_records = openalex.search(subtask, limit=1)
    if not openalex_records:
        raise RuntimeError("OpenAlex returned no records for the smoke query")
    print(f"OpenAlex: OK - {openalex_records[0].title[:120]}")

    print("Live provider smoke test completed successfully.")


if __name__ == "__main__":
    main()
