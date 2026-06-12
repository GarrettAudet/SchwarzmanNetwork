from __future__ import annotations


def profile_context_text(record: dict[str, object]) -> str:
    parts = [record.get("position"), record.get("current_company_name"), record.get("location"), record.get("city")]
    return " | ".join(str(part) for part in parts if part)
