from __future__ import annotations

import json
from json import JSONDecodeError
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..config import enrichlayer_api_key
from ..models import clean_text, utc_now_iso


class EnrichLayerError(RuntimeError):
    def __init__(self, message: str, status_code: int = 0) -> None:
        super().__init__(message)
        self.status_code = status_code


class EnrichLayerClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or enrichlayer_api_key()

    def fetch_profile(self, linkedin_url: str) -> dict[str, object]:
        if not self.api_key:
            raise EnrichLayerError("ENRICH_API is not set in the environment or .env file.")
        query = urlencode(
            {
                "profile_url": linkedin_url,
                "fallback_to_cache": "on-error",
                "use_cache": "if-present",
            }
        )
        request = Request(
            f"https://enrichlayer.com/api/v2/profile?{query}",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            },
            method="GET",
        )
        try:
            with urlopen(request, timeout=180) as response:
                body = response.read().decode("utf-8")
        except HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise EnrichLayerError(
                f"HTTP {error.code} from Enrichlayer: {body[:500]}",
                status_code=error.code,
            ) from error
        if not body.strip():
            return {}
        try:
            payload = json.loads(body)
        except JSONDecodeError as error:
            raise EnrichLayerError(f"Invalid JSON from Enrichlayer: {body[:500]}") from error
        return payload if isinstance(payload, dict) else {}


def _date_value(value: object) -> str:
    if not isinstance(value, dict):
        return clean_text(value)
    year = value.get("year")
    month = value.get("month")
    day = value.get("day")
    if not year:
        return ""
    if month and day:
        return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
    if month:
        return f"{int(year):04d}-{int(month):02d}"
    return f"{int(year):04d}"


def _profile_location(record: dict[str, object]) -> str:
    location = clean_text(record.get("location_str"))
    if location:
        return location
    parts = [
        clean_text(record.get("city")),
        clean_text(record.get("state")),
        clean_text(record.get("country_full_name") or record.get("country")),
    ]
    return ", ".join(part for part in parts if part)


def _experience_item(item: object) -> dict[str, str]:
    if not isinstance(item, dict):
        return {}
    return {
        "title": clean_text(item.get("title")),
        "company": clean_text(item.get("company")),
        "company_linkedin_profile_url": clean_text(item.get("company_linkedin_profile_url")),
        "location": clean_text(item.get("location")),
        "starts_at": _date_value(item.get("starts_at")),
        "ends_at": _date_value(item.get("ends_at")),
        "description": clean_text(item.get("description")),
    }


def _education_item(item: object) -> dict[str, str]:
    if not isinstance(item, dict):
        return {}
    return {
        "school": clean_text(item.get("school")),
        "degree_name": clean_text(item.get("degree_name")),
        "field_of_study": clean_text(item.get("field_of_study")),
        "starts_at": _date_value(item.get("starts_at")),
        "ends_at": _date_value(item.get("ends_at")),
        "description": clean_text(item.get("description")),
    }


def _current_experience(experiences: list[dict[str, str]]) -> dict[str, str]:
    for item in experiences:
        if not item.get("ends_at"):
            return item
    return experiences[0] if experiences else {}


def _compact_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def normalize_enrichlayer_record(
    record: dict[str, object],
    input_url: str,
    fetched_at: str | None = None,
    error: str = "",
) -> dict[str, str]:
    raw_experiences = record.get("experiences")
    raw_education = record.get("education")
    experiences = [_experience_item(item) for item in raw_experiences] if isinstance(raw_experiences, list) else []
    experiences = [item for item in experiences if item]
    education = [_education_item(item) for item in raw_education] if isinstance(raw_education, list) else []
    education = [item for item in education if item]
    current = _current_experience(experiences)
    status = "error" if error else "ok" if any((experiences, education, record.get("full_name"), record.get("occupation"))) else "empty_response"
    return {
        "input_url": input_url,
        "enrichlayer_full_name": clean_text(record.get("full_name")),
        "enrichlayer_headline": clean_text(record.get("headline")),
        "enrichlayer_occupation": clean_text(record.get("occupation")),
        "enrichlayer_profile_location": _profile_location(record),
        "enrichlayer_current_company": current.get("company", ""),
        "enrichlayer_current_job_title": current.get("title", ""),
        "enrichlayer_current_job_location": current.get("location", ""),
        "enrichlayer_current_started_at": current.get("starts_at", ""),
        "enrichlayer_experience_count": str(len(experiences)),
        "enrichlayer_education_count": str(len(education)),
        "enrichlayer_experience_json": _compact_json(experiences),
        "enrichlayer_education_json": _compact_json(education),
        "enrichlayer_status": status,
        "enrichlayer_error": clean_text(error),
        "enrichlayer_fetched_at": fetched_at or utc_now_iso(),
    }


ENRICHLAYER_FIELDNAMES = [
    "input_url",
    "enrichlayer_full_name",
    "enrichlayer_headline",
    "enrichlayer_occupation",
    "enrichlayer_profile_location",
    "enrichlayer_current_company",
    "enrichlayer_current_job_title",
    "enrichlayer_current_job_location",
    "enrichlayer_current_started_at",
    "enrichlayer_experience_count",
    "enrichlayer_education_count",
    "enrichlayer_experience_json",
    "enrichlayer_education_json",
    "enrichlayer_status",
    "enrichlayer_error",
    "enrichlayer_fetched_at",
]
