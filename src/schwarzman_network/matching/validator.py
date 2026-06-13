from __future__ import annotations

import re
import unicodedata

from ..models import clean_text
from ..search.normalize import is_linkedin_profile_url


def name_match_score(expected_name: str, observed_text: str) -> float:
    expected_name = unicodedata.normalize("NFKD", clean_text(expected_name)).encode("ascii", "ignore").decode("ascii")
    observed_text = unicodedata.normalize("NFKD", clean_text(observed_text)).encode("ascii", "ignore").decode("ascii")
    tokens = [
        token
        for token in re.sub(r"[^a-z0-9\s-]", " ", expected_name.lower()).split()
        if len(token) > 1
    ]
    haystack = observed_text.lower()
    haystack_tokens = [
        token
        for token in re.sub(r"[^a-z0-9\s-]", " ", haystack).split()
        if len(token) > 1
    ]
    if not tokens or not haystack:
        return 0.0

    def token_matches(token: str) -> bool:
        if token in haystack:
            return True
        return any(
            len(observed) >= 4 and (token.startswith(observed) or token.endswith(observed))
            for observed in haystack_tokens
        )

    return sum(1 for token in tokens if token_matches(token)) / len(tokens)


def validate_linkedin_candidate(expected_name: str, url: str, title: str = "", snippet: str = "") -> dict[str, object]:
    score = name_match_score(expected_name, f"{title} {snippet} {url}")
    return {
        "is_linkedin_profile": is_linkedin_profile_url(url),
        "name_match_score": score,
        "accepted": is_linkedin_profile_url(url) and score >= 0.8,
        "reason": "strong_name_profile_match" if score >= 0.8 else "weak_or_missing_name_evidence",
    }
