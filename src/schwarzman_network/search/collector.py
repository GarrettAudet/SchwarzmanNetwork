from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module

from .queries import linkedin_queries
from .normalize import is_linkedin_profile_url, normalize_linkedin_url


@dataclass(frozen=True)
class SearchCandidate:
    url: str
    title: str = ""
    snippet: str = ""
    provider: str = ""
    query: str = ""


def collect_linkedin_candidates(
    name: str,
    country: str = "",
    cohort: str = "",
    providers: list[str] | None = None,
    max_results: int = 5,
) -> list[SearchCandidate]:
    """Return LinkedIn candidates from configured search providers."""
    provider_names = providers or ["google", "brave", "bing"]
    seen: set[str] = set()
    out: list[SearchCandidate] = []
    for query in linkedin_queries(name, country, cohort):
        for provider in provider_names:
            module = import_module(f"schwarzman_network.search.{provider}")
            try:
                results = module.search(query)[:max_results]
            except Exception:
                results = []
            for candidate in results:
                normalized = normalize_linkedin_url(candidate.url)
                if normalized in seen or not is_linkedin_profile_url(normalized):
                    continue
                seen.add(normalized)
                out.append(
                    SearchCandidate(
                        url=normalized,
                        title=candidate.title,
                        snippet=candidate.snippet,
                        provider=candidate.provider or provider,
                        query=query,
                    )
                )
    return out
