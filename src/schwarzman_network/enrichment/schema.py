from __future__ import annotations

from ..models import clean_text


def _experience_items(record: dict[str, object]) -> list[dict[str, object]]:
    experience = record.get("experience")
    out: list[dict[str, object]] = []
    if isinstance(experience, list):
        for item in experience:
            if not isinstance(item, dict):
                continue
            positions = item.get("positions")
            if isinstance(positions, list):
                for position in positions:
                    if not isinstance(position, dict):
                        continue
                    merged = dict(item)
                    merged.update(position)
                    merged["company"] = clean_text(item.get("company")) or clean_text(position.get("company"))
                    merged["company_id"] = clean_text(item.get("company_id")) or clean_text(position.get("company_id"))
                    merged["url"] = clean_text(item.get("url")) or clean_text(position.get("url"))
                    merged["location"] = clean_text(position.get("location")) or clean_text(item.get("location"))
                    out.append(merged)
            out.append(item)
    return out


def _is_current_experience(item: dict[str, object]) -> bool:
    end_date = clean_text(item.get("end_date")).lower()
    duration = clean_text(item.get("duration")).lower()
    if "present" in end_date or "present" in duration:
        return True
    return False


def _current_experience(record: dict[str, object]) -> dict[str, object]:
    items = _experience_items(record)
    for item in items:
        if _is_current_experience(item):
            return item
    return items[0] if items else {}


def _experience_value(record: dict[str, object], keys: list[str]) -> str:
    first = _current_experience(record)
    for key in keys:
        value = first.get(key)
        if value:
            return clean_text(value)
    return ""


def current_company_name(record: dict[str, object]) -> str:
    current_company = record.get("current_company")
    current_company_name_value = ""
    if isinstance(current_company, dict):
        current_company_name_value = clean_text(current_company.get("name") or current_company.get("company_name"))
    return (
        current_company_name_value
        or clean_text(record.get("current_company_name"))
        or _experience_value(record, ["company", "company_name"])
    )


def current_company_id(record: dict[str, object]) -> str:
    current_company = record.get("current_company")
    current_company_id_value = ""
    if isinstance(current_company, dict):
        current_company_id_value = clean_text(current_company.get("company_id"))
    return (
        current_company_id_value
        or clean_text(record.get("current_company_company_id"))
        or _experience_value(record, ["company_id"])
    )


def current_company_location(record: dict[str, object]) -> str:
    current_company = record.get("current_company")
    if isinstance(current_company, dict):
        return clean_text(current_company.get("location"))
    return ""


def current_job_title(record: dict[str, object]) -> str:
    current_company = record.get("current_company")
    company_title = clean_text(current_company.get("title")) if isinstance(current_company, dict) else ""
    return _experience_value(record, ["title", "position"]) or company_title or clean_text(record.get("position"))


def profile_location(record: dict[str, object]) -> str:
    return clean_text(record.get("location")) or clean_text(record.get("city"))


def job_location(record: dict[str, object]) -> tuple[str, str]:
    experience_location = _experience_value(record, ["location"])
    if experience_location:
        return experience_location, "experience.location"
    company_location = current_company_location(record)
    if company_location:
        return company_location, "current_company.location"
    return "", ""


def normalize_brightdata_record(record: dict[str, object], input_url: str = "") -> dict[str, str]:
    job_loc, job_loc_source = job_location(record)
    profile_loc = profile_location(record)
    normalized = {
        "input_url": clean_text(record.get("input_url") or record.get("url") or input_url),
        "name": clean_text(record.get("name")),
        "position": current_job_title(record),
        "current_company_name": current_company_name(record),
        "current_company_company_id": current_company_id(record),
        "profile_city": clean_text(record.get("city")),
        "profile_location": profile_loc,
        "job_location": job_loc,
        "job_location_source": job_loc_source,
        "city": clean_text(record.get("city")),
        "location": profile_loc,
        "experience_count": str(len(record.get("experience") or [])) if isinstance(record.get("experience"), list) else "",
        "education_count": str(len(record.get("education") or [])) if isinstance(record.get("education"), list) else "",
    }
    meaningful_keys = [
        "name",
        "position",
        "current_company_name",
        "profile_location",
        "job_location",
        "experience_count",
        "education_count",
    ]
    normalized["record_status"] = "ok" if any(normalized.get(key) for key in meaningful_keys) else "empty_response"
    return normalized
