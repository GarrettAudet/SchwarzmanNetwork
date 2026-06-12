from __future__ import annotations

from ..search.collector import SearchCandidate
from ..search.normalize import normalize_linkedin_url
from .validator import validate_linkedin_candidate


def choose_linkedin_candidate(expected_name: str, candidates: list[SearchCandidate]) -> tuple[str, dict[str, object]]:
    for candidate in candidates:
        decision = validate_linkedin_candidate(expected_name, candidate.url, candidate.title, candidate.snippet)
        if decision["accepted"]:
            return normalize_linkedin_url(candidate.url), decision
    return "N/A", {"accepted": False, "reason": "no_accepted_candidate"}
