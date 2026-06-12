from __future__ import annotations

import json
import re
from typing import Protocol

from ..models import clean_text
from ..search.collector import SearchCandidate
from ..search.normalize import normalize_linkedin_url
from .llm_client import LLMClient
from .llm_prompts import linkedin_adjudication_prompt
from .validator import validate_linkedin_candidate


class TextCompleter(Protocol):
    def available(self) -> bool:
        ...

    def complete_text(self, prompt: str) -> str:
        ...


def _candidate_payload(candidates: list[SearchCandidate]) -> list[dict[str, object]]:
    return [
        {
            "candidate_id": index,
            "url": normalize_linkedin_url(candidate.url),
            "title": clean_text(candidate.title),
            "snippet": clean_text(candidate.snippet),
            "provider": clean_text(candidate.provider),
            "query": clean_text(candidate.query),
        }
        for index, candidate in enumerate(candidates, start=1)
    ]


def _decision(
    accepted: bool,
    reason: str,
    adjudicator: str,
    candidate_count: int,
    selected_candidate_id: int | None = None,
    selected_candidate_url: str = "N/A",
    confidence: str = "low",
    rationale: str = "",
    raw_response: str = "",
) -> dict[str, object]:
    return {
        "accepted": accepted,
        "reason": reason,
        "adjudicator": adjudicator,
        "confidence": confidence,
        "rationale": clean_text(rationale),
        "selected_candidate_id": selected_candidate_id,
        "selected_candidate_url": selected_candidate_url,
        "candidate_count": candidate_count,
        "raw_response": raw_response,
    }


def _json_object(text: str) -> dict[str, object]:
    cleaned = clean_text(text)
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("LLM response did not contain a JSON object.")
    parsed = json.loads(cleaned[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("LLM response JSON was not an object.")
    return parsed


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return clean_text(value).lower() in {"true", "yes", "1", "accepted", "accept"}


def choose_linkedin_candidate_heuristic(expected_name: str, candidates: list[SearchCandidate]) -> tuple[str, dict[str, object]]:
    for index, candidate in enumerate(candidates, start=1):
        decision = validate_linkedin_candidate(expected_name, candidate.url, candidate.title, candidate.snippet)
        if decision["accepted"]:
            url = normalize_linkedin_url(candidate.url)
            decision.update(
                _decision(
                    True,
                    clean_text(decision.get("reason")),
                    "heuristic",
                    len(candidates),
                    selected_candidate_id=index,
                    selected_candidate_url=url,
                    confidence="medium",
                    rationale="Accepted by deterministic name-token and LinkedIn profile-url match.",
                )
            )
            return url, decision
    return "N/A", _decision(False, "no_accepted_candidate", "heuristic", len(candidates))


def choose_linkedin_candidate_llm(
    expected_name: str,
    candidates: list[SearchCandidate],
    country: str = "",
    cohort: str = "",
    official_bio: str = "",
    client: TextCompleter | None = None,
) -> tuple[str, dict[str, object]]:
    if not candidates:
        return "N/A", _decision(False, "no_candidates", "llm", 0)

    llm = client or LLMClient()
    if not llm.available():
        return "N/A", _decision(False, "openai_api_key_missing", "llm_unavailable", len(candidates))

    prompt = linkedin_adjudication_prompt(expected_name, country, cohort, official_bio, candidates)
    try:
        raw_response = llm.complete_text(prompt)
        parsed = _json_object(raw_response)
    except Exception as exc:
        return "N/A", _decision(
            False,
            "llm_error",
            "llm_error",
            len(candidates),
            rationale=str(exc),
        )

    raw_response = clean_text(raw_response)
    selected = parsed.get("selected_candidate_id")
    confidence = clean_text(parsed.get("confidence")).lower()
    accepted_by_model = _as_bool(parsed.get("accepted"))
    rationale = clean_text(parsed.get("rationale"))
    if confidence not in {"high", "medium", "low"}:
        confidence = "low"

    selected_text = clean_text(selected).lower()
    if selected is None or selected_text in {"", "null", "none"}:
        return "N/A", _decision(
            False,
            "llm_returned_no_match",
            "llm",
            len(candidates),
            confidence=confidence,
            rationale=rationale,
            raw_response=raw_response,
        )

    try:
        selected_id = int(selected)
    except (TypeError, ValueError):
        return "N/A", _decision(
            False,
            "invalid_llm_candidate_id",
            "llm",
            len(candidates),
            confidence=confidence,
            rationale=rationale,
            raw_response=raw_response,
        )

    if selected_id < 1 or selected_id > len(candidates):
        return "N/A", _decision(
            False,
            "llm_candidate_id_out_of_range",
            "llm",
            len(candidates),
            selected_candidate_id=selected_id,
            confidence=confidence,
            rationale=rationale,
            raw_response=raw_response,
        )

    candidate = candidates[selected_id - 1]
    url = normalize_linkedin_url(candidate.url)
    accepted = accepted_by_model and confidence == "high" and url != "N/A"
    reason = "llm_high_confidence_match" if accepted else "llm_not_high_confidence"
    return (
        url if accepted else "N/A",
        _decision(
            accepted,
            reason,
            "llm",
            len(candidates),
            selected_candidate_id=selected_id,
            selected_candidate_url=url,
            confidence=confidence,
            rationale=rationale,
            raw_response=raw_response,
        ),
    )


def choose_linkedin_candidate(
    expected_name: str,
    candidates: list[SearchCandidate],
    country: str = "",
    cohort: str = "",
    official_bio: str = "",
    mode: str = "llm",
    client: TextCompleter | None = None,
) -> tuple[str, dict[str, object]]:
    if mode == "heuristic":
        return choose_linkedin_candidate_heuristic(expected_name, candidates)

    url, decision = choose_linkedin_candidate_llm(expected_name, candidates, country, cohort, official_bio, client=client)
    if mode == "llm-or-heuristic" and not decision.get("accepted") and decision.get("reason") in {
        "openai_api_key_missing",
        "llm_error",
    }:
        fallback_url, fallback = choose_linkedin_candidate_heuristic(expected_name, candidates)
        fallback["llm_reason"] = decision.get("reason")
        return fallback_url, fallback
    return url, decision


def candidate_evidence_json(candidates: list[SearchCandidate]) -> str:
    return json.dumps(_candidate_payload(candidates), ensure_ascii=False)
