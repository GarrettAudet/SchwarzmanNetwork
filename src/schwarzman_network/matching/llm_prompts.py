from __future__ import annotations

import json

from ..models import clean_text
from ..search.collector import SearchCandidate


def company_description_prompt(company_name: str, role_context: str = "") -> str:
    return (
        "Write one factual sentence describing the company. "
        "If the company cannot be identified from the supplied context, return an empty string.\n\n"
        f"Company: {company_name}\n"
        f"Context: {role_context}\n"
    )


def linkedin_adjudication_prompt(
    scholar_name: str,
    country: str = "",
    cohort: str = "",
    official_bio: str = "",
    candidates: list[SearchCandidate] | None = None,
) -> str:
    candidate_rows = []
    for index, candidate in enumerate(candidates or [], start=1):
        candidate_rows.append(
            {
                "candidate_id": index,
                "url": clean_text(candidate.url),
                "title": clean_text(candidate.title),
                "snippet": clean_text(candidate.snippet),
                "provider": clean_text(candidate.provider),
                "query": clean_text(candidate.query),
            }
        )

    return (
        "You are verifying whether a search result is the correct LinkedIn profile "
        "for a Schwarzman Scholar.\n\n"
        "Rules:\n"
        "- Select only one candidate_id from the provided candidates, or return null.\n"
        "- Never invent, rewrite, or normalize a URL yourself.\n"
        "- A matching name alone is not enough for common names.\n"
        "- Prefer candidates with evidence tying the person to Schwarzman Scholars, "
        "Tsinghua, the cohort, the country, the official bio, education, or a highly "
        "specific career context.\n"
        "- If the evidence is ambiguous, conflicting, or only a name match, return null.\n"
        "- Auto-accepted matches must be high confidence.\n\n"
        "Return strict JSON only with this schema:\n"
        "{\n"
        '  "accepted": true | false,\n'
        '  "selected_candidate_id": number | null,\n'
        '  "confidence": "high" | "medium" | "low",\n'
        '  "rationale": "short reason based only on supplied evidence"\n'
        "}\n\n"
        "Scholar context:\n"
        f"Name: {clean_text(scholar_name)}\n"
        f"Country: {clean_text(country)}\n"
        f"Cohort: {clean_text(cohort)}\n"
        f"Official bio/context: {clean_text(official_bio)}\n\n"
        "Search-result candidates:\n"
        f"{json.dumps(candidate_rows, ensure_ascii=False, indent=2)}\n"
    )
