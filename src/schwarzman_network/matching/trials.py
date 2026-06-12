from __future__ import annotations

import json
from dataclasses import dataclass

from ..search.collector import SearchCandidate
from .adjudicator import choose_linkedin_candidate


@dataclass
class StaticLLMClient:
    response: dict[str, object]

    def available(self) -> bool:
        return True

    def complete_text(self, prompt: str) -> str:
        return json.dumps(self.response)


def run_linkedin_matching_trials() -> list[dict[str, object]]:
    cases = [
        {
            "case": "common_name_schwarzman_candidate_second",
            "scholar_name": "John Smith",
            "country": "United States",
            "cohort": "2027",
            "official_bio": "John Smith is a Schwarzman Scholar from the United States.",
            "expected_url": "https://www.linkedin.com/in/john-a-smith-schwarzman",
            "llm_response": {
                "accepted": True,
                "selected_candidate_id": 2,
                "confidence": "high",
                "rationale": "Candidate 2 explicitly mentions Schwarzman Scholars and Tsinghua; candidate 1 is only a name match.",
            },
            "candidates": [
                SearchCandidate(
                    url="https://www.linkedin.com/in/johnsmith/",
                    title="John Smith - Product Manager",
                    snippet="Product manager in New York.",
                    provider="trial",
                    query='John Smith "Schwarzman Scholar LinkedIn"',
                ),
                SearchCandidate(
                    url="https://www.linkedin.com/in/john-a-smith-schwarzman/",
                    title="John A. Smith - Schwarzman Scholar - Tsinghua University",
                    snippet="Schwarzman Scholar and graduate student at Tsinghua University.",
                    provider="trial",
                    query='John Smith "Schwarzman Scholar LinkedIn"',
                ),
            ],
        },
        {
            "case": "common_name_no_schwarzman_evidence",
            "scholar_name": "Maria Garcia",
            "country": "Mexico",
            "cohort": "2026",
            "official_bio": "Maria Garcia is a Schwarzman Scholar from Mexico.",
            "expected_url": "N/A",
            "llm_response": {
                "accepted": False,
                "selected_candidate_id": None,
                "confidence": "low",
                "rationale": "The candidates are name matches but do not include evidence connecting them to Schwarzman Scholars.",
            },
            "candidates": [
                SearchCandidate(
                    url="https://www.linkedin.com/in/maria-garcia/",
                    title="Maria Garcia - Consultant",
                    snippet="Consultant with international experience.",
                    provider="trial",
                    query='Maria Garcia "Schwarzman Scholar LinkedIn"',
                ),
                SearchCandidate(
                    url="https://www.linkedin.com/in/maria-garcia-mx/",
                    title="Maria Garcia - Analyst",
                    snippet="Analyst in Mexico City.",
                    provider="trial",
                    query='Maria Garcia "Schwarzman Scholar LinkedIn"',
                ),
            ],
        },
        {
            "case": "specific_schwarzman_match",
            "scholar_name": "Aisha Khan",
            "country": "Pakistan",
            "cohort": "2025",
            "official_bio": "Aisha Khan is a Schwarzman Scholar from Pakistan focused on climate finance.",
            "expected_url": "https://www.linkedin.com/in/aisha-khan-climate",
            "llm_response": {
                "accepted": True,
                "selected_candidate_id": 1,
                "confidence": "high",
                "rationale": "The result names the scholar and includes Schwarzman plus matching climate finance context.",
            },
            "candidates": [
                SearchCandidate(
                    url="https://www.linkedin.com/in/aisha-khan-climate/",
                    title="Aisha Khan - Schwarzman Scholar - Climate Finance",
                    snippet="Schwarzman Scholar from Pakistan working on climate finance.",
                    provider="trial",
                    query='Aisha Khan "Schwarzman Scholar LinkedIn"',
                ),
            ],
        },
    ]

    rows: list[dict[str, object]] = []
    for case in cases:
        heuristic_url, heuristic_decision = choose_linkedin_candidate(
            case["scholar_name"],
            case["candidates"],
            mode="heuristic",
        )
        llm_url, llm_decision = choose_linkedin_candidate(
            case["scholar_name"],
            case["candidates"],
            country=case["country"],
            cohort=case["cohort"],
            official_bio=case["official_bio"],
            mode="llm",
            client=StaticLLMClient(case["llm_response"]),
        )
        expected_url = case["expected_url"]
        rows.append(
            {
                "case": case["case"],
                "expected_url": expected_url,
                "heuristic_url": heuristic_url,
                "heuristic_reason": heuristic_decision.get("reason"),
                "llm_url": llm_url,
                "llm_reason": llm_decision.get("reason"),
                "llm_confidence": llm_decision.get("confidence"),
                "llm_rationale": llm_decision.get("rationale"),
                "heuristic_correct": heuristic_url == expected_url,
                "llm_correct": llm_url == expected_url,
            }
        )
    return rows
