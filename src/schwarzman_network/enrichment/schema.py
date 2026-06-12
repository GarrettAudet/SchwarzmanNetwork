from __future__ import annotations

from ..models import clean_text


def _first_experience(record: dict[str, object]) -> dict[str, object]:
    experience = record.get("experience")
    if isinstance(experience, list):
        for item in experience:
            if isinstance(item, dict):
                return item
    return {}


def _experience_value(record: dict[str, object], keys: list[str]) -> str:
    first = _first_experience(record)
    for key in keys:
        value = first.get(key)
        if value:
            return clean_text(value)
    return ""


def current_company_name(record: dict[str, object]) -> str:
    current_company = record.get("current_company")
    if isinstance(current_company, dict):
        return clean_text(current_company.get("name"))
    return clean_text(record.get("current_company_name")) or _experience_value(record, ["company", "company_name"])


def current_company_id(record: dict[str, object]) -> str:
    current_company = record.get("current_company")
    if isinstance(current_company, dict):
        return clean_text(current_company.get("company_id"))
    return clean_text(record.get("current_company_company_id"))


def normalize_brightdata_record(record: dict[str, object], input_url: str = "") -> dict[str, str]:
    normalized = {
        "input_url": clean_text(record.get("input_url") or record.get("url") or input_url),
        "name": clean_text(record.get("name")),
        "position": clean_text(record.get("position")) or _experience_value(record, ["title", "position"]),
        "current_company_name": current_company_name(record),
        "current_company_company_id": current_company_id(record),
        "city": clean_text(record.get("city")),
        "location": clean_text(record.get("location")) or _experience_value(record, ["location"]),
        "experience_count": str(len(record.get("experience") or [])) if isinstance(record.get("experience"), list) else "",
        "education_count": str(len(record.get("education") or [])) if isinstance(record.get("education"), list) else "",
    }
    meaningful_keys = ["name", "position", "current_company_name", "city", "location", "experience_count", "education_count"]
    normalized["record_status"] = "ok" if any(normalized.get(key) for key in meaningful_keys) else "empty_response"
    return normalized
