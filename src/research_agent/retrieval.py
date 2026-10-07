"""Academic metadata retrieval from Crossref and OpenAlex.

Structured academic APIs are used instead of unrestricted web scraping because
the Unit 6 design prioritises provenance, reproducibility, and testability.
Each provider response is normalised into the same AcademicRecord model so
downstream processing does not depend on provider-specific JSON structures.
"""

from __future__ import annotations

from typing import Any, Iterable, Protocol

import httpx

from research_agent.models import AcademicRecord, ResearchSubtask


class RetrievalError(RuntimeError):
    """Raised when an academic metadata source cannot be queried reliably."""


class AcademicRetriever(Protocol):
    """Common interface for scholarly metadata providers."""

    def search(self, subtask: ResearchSubtask, limit: int = 5) -> list[AcademicRecord]:
        """Return normalised academic records relevant to a research subtask."""


class CrossrefRetriever:
    """Retrieve bibliographic metadata from the Crossref REST API."""

    BASE_URL = "https://api.crossref.org/v1/works"

    def __init__(
        self,
        *,
        email: str | None = None,
        client: httpx.Client | None = None,
        timeout: float = 15.0,
    ) -> None:
        self.email = email
        self._owns_client = client is None
        self.client = client or httpx.Client(timeout=timeout)
        self.user_agent = (
            "llm-academic-research-agent/0.1"
            + (f" (mailto:{email})" if email else "")
        )

    def search(self, subtask: ResearchSubtask, limit: int = 5) -> list[AcademicRecord]:
        if limit < 1:
            raise ValueError("limit must be at least 1")

        params: dict[str, str | int] = {
            "query.bibliographic": " ".join(subtask.search_terms),
            "rows": limit,
            "select": "DOI,title,author,published,URL,abstract",
        }
        if self.email:
            params["mailto"] = self.email

        try:
            response = self.client.get(
                self.BASE_URL,
                params=params,
                headers={"User-Agent": self.user_agent},
            )
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise RetrievalError("Crossref retrieval failed") from exc

        items = payload.get("message", {}).get("items", [])
        return [record for item in items if (record := _parse_crossref_item(item))]

    def close(self) -> None:
        if self._owns_client:
            self.client.close()


class OpenAlexRetriever:
    """Retrieve scholarly works from the OpenAlex API."""

    BASE_URL = "https://api.openalex.org/works"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        client: httpx.Client | None = None,
        timeout: float = 15.0,
    ) -> None:
        self.api_key = api_key
        self._owns_client = client is None
        self.client = client or httpx.Client(timeout=timeout)

    def search(self, subtask: ResearchSubtask, limit: int = 5) -> list[AcademicRecord]:
        if limit < 1:
            raise ValueError("limit must be at least 1")

        params: dict[str, str | int] = {
            "search": " ".join(subtask.search_terms),
            "per-page": limit,
        }
        if self.api_key:
            params["api_key"] = self.api_key

        try:
            response = self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise RetrievalError("OpenAlex retrieval failed") from exc

        results = payload.get("results", [])
        return [record for item in results if (record := _parse_openalex_item(item))]

    def close(self) -> None:
        if self._owns_client:
            self.client.close()


def retrieve_from_sources(
    subtask: ResearchSubtask,
    retrievers: Iterable[AcademicRetriever],
    *,
    limit_per_source: int = 5,
) -> list[AcademicRecord]:
    """Collect records from multiple providers without hiding provider failures.

    Provider failures are surfaced rather than silently ignored. This makes
    remediation visible to the orchestrator and supports the bounded retry
    strategy proposed in Unit 6.
    """

    records: list[AcademicRecord] = []
    for retriever in retrievers:
        records.extend(retriever.search(subtask, limit=limit_per_source))
    return records


def _parse_crossref_item(item: dict[str, Any]) -> AcademicRecord | None:
    titles = item.get("title") or []
    title = titles[0].strip() if titles and isinstance(titles[0], str) else ""
    if not title:
        return None

    authors = []
    for author in item.get("author") or []:
        name = " ".join(
            part for part in [author.get("given"), author.get("family")] if part
        ).strip()
        if name:
            authors.append(name)

    year = _crossref_year(item.get("published"))
    doi = item.get("DOI")
    url = item.get("URL")
    abstract = item.get("abstract")

    return AcademicRecord(
        title=title,
        authors=authors,
        year=year,
        doi=doi,
        source="Crossref",
        url=url,
        abstract=abstract,
    )


def _crossref_year(published: Any) -> int | None:
    try:
        parts = published["date-parts"]
        return int(parts[0][0])
    except (KeyError, IndexError, TypeError, ValueError):
        return None


def _parse_openalex_item(item: dict[str, Any]) -> AcademicRecord | None:
    title = (item.get("display_name") or item.get("title") or "").strip()
    if not title:
        return None

    authors = []
    for authorship in item.get("authorships") or []:
        author = authorship.get("author") or {}
        name = author.get("display_name")
        if name:
            authors.append(name)

    doi = item.get("doi")
    if isinstance(doi, str) and doi.startswith("https://doi.org/"):
        doi = doi.removeprefix("https://doi.org/")

    primary_location = item.get("primary_location") or {}
    url = primary_location.get("landing_page_url") or item.get("id")

    return AcademicRecord(
        title=title,
        authors=authors,
        year=item.get("publication_year"),
        doi=doi,
        source="OpenAlex",
        url=url,
        abstract=_reconstruct_openalex_abstract(item.get("abstract_inverted_index")),
    )


def _reconstruct_openalex_abstract(index: Any) -> str | None:
    """Reconstruct readable text from OpenAlex's inverted abstract index."""
    if not isinstance(index, dict) or not index:
        return None

    positioned_words: list[tuple[int, str]] = []
    for word, positions in index.items():
        if not isinstance(positions, list):
            continue
        for position in positions:
            if isinstance(position, int):
                positioned_words.append((position, word))

    if not positioned_words:
        return None

    positioned_words.sort(key=lambda item: item[0])
    return " ".join(word for _, word in positioned_words)
