"""Minimal live-provider smoke test.

Each provider is tested independently so one failure does not hide the status
of the remaining integrations. The command exits non-zero when any provider
fails, making the result useful both interactively and in GitHub Actions.
"""

from __future__ import annotations

from collections.abc import Callable

from research_agent.huggingface import HuggingFaceGateway
from research_agent.models import ResearchSubtask
from research_agent.retrieval import CrossrefRetriever, OpenAlexRetriever
from research_agent.settings import LiveSettings


def _check(name: str, action: Callable[[], str]) -> str | None:
    try:
        detail = action()
        print(f"{name}: OK - {detail[:120]}")
        return None
    except Exception as exc:  # smoke test should report all provider outcomes
        message = f"{type(exc).__name__}: {exc}"
        print(f"{name}: FAILED - {message}")
        return message


def main() -> None:
    settings = LiveSettings.from_env()

    gateway = HuggingFaceGateway(
        token=settings.hf_token,
        model=settings.hf_model,
        max_tokens=40,
        temperature=0.0,
    )

    subtask = ResearchSubtask(
        id="smoke",
        question="How are LLM planning agents evaluated?",
        search_terms=["LLM planning agents", "evaluation"],
    )
    crossref = CrossrefRetriever(email=settings.crossref_email)
    openalex = OpenAlexRetriever(api_key=settings.openalex_api_key)

    failures = {
        "Hugging Face": _check(
            "Hugging Face",
            lambda: gateway.generate(
                "Reply in one short sentence confirming that the model connection works."
            ),
        ),
        "Crossref": _check(
            "Crossref",
            lambda: _first_title(crossref.search(subtask, limit=1)),
        ),
        "OpenAlex": _check(
            "OpenAlex",
            lambda: _first_title(openalex.search(subtask, limit=1)),
        ),
    }

    failed = {name: detail for name, detail in failures.items() if detail}
    if failed:
        raise SystemExit(
            "Live provider smoke test failed for: " + ", ".join(failed)
        )

    print("Live provider smoke test completed successfully.")


def _first_title(records) -> str:
    if not records:
        raise RuntimeError("Provider returned no records for the smoke query")
    return records[0].title


if __name__ == "__main__":
    main()
