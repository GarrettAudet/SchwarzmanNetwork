from __future__ import annotations

from html import unescape
import re

from .cohort import cohort_from_graduation_year, parse_program_years
from ..config import OFFICIAL_SOURCE_URL
from ..models import clean_text


def _decode_html(value: str = "") -> str:
    return clean_text(unescape(value).replace("&amp;", "&"))


def _attr(chunk: str, name: str) -> str:
    match = re.search(rf'{name}="([^"]*)"', chunk, flags=re.S)
    return _decode_html(match.group(1)) if match else ""


def _html_text(chunk: str, selector_class: str) -> str:
    match = re.search(rf'<[^>]+class="{re.escape(selector_class)}"[^>]*>([\s\S]*?)</[^>]+>', chunk)
    if not match:
        return ""
    return _decode_html(re.sub(r"<[^>]+>", " ", match.group(1)))


def parse_official_html(html: str, source_url: str = OFFICIAL_SOURCE_URL) -> list[dict[str, object]]:
    pieces = html.split('<div class="people-feed__item"')[1:]
    scholars: list[dict[str, object]] = []
    for piece in pieces:
        chunk = f'<div class="people-feed__item"{piece}'
        data_year = _attr(chunk, "data-year")
        modal_title = _attr(chunk, "data-bio-modal-title")
        title = modal_title or _html_text(chunk, "people-card__title")
        title_parts = [part.strip() for part in title.split(" - ") if part.strip()]
        country = _attr(chunk, "data-country") or (title_parts[0] if title_parts else "")
        universities = (
            "; ".join(part.strip() for part in _attr(chunk, "data-university").split("|") if part.strip())
            or " - ".join(title_parts[1:])
        )
        class_year = _attr(chunk, "data-bio-modal-subtitle") or _html_text(chunk, "people-card__class")
        _program_start, graduation_year = parse_program_years(class_year, data_year)
        name = _attr(chunk, "data-bio-modal-name") or _html_text(chunk, "people-card__name")
        if not name or not graduation_year:
            continue
        profile_hash = _attr(chunk, "data-bio-modal-hash")
        scholars.append(
            {
                "name": name,
                "cohort": cohort_from_graduation_year(graduation_year),
                "graduationYear": graduation_year,
                "country": country,
                "universities": universities,
                "classYear": class_year,
                "bio": _attr(chunk, "data-bio-modal-text"),
                "profileHash": profile_hash,
                "sourceUrl": f"{source_url}#{profile_hash}" if profile_hash else source_url,
                "imageUrl": _attr(chunk, "data-bio-modal-image"),
            }
        )
    return sorted(scholars, key=lambda item: (int(item["graduationYear"]), str(item["name"]).lower()))


def normalize_official_json(payload: dict[str, object]) -> list[dict[str, object]]:
    rows = payload.get("scholars", [])
    normalized: list[dict[str, object]] = []
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        graduation_year = row.get("graduationYear")
        normalized.append(
            {
                "name": clean_text(row.get("name")),
                "cohort": clean_text(row.get("cohort")) or cohort_from_graduation_year(int(graduation_year or 0) or None),
                "graduationYear": graduation_year,
                "country": clean_text(row.get("country") or row.get("region")),
                "universities": clean_text(row.get("universities")),
                "bio": clean_text(row.get("bio")),
                "sourceUrl": clean_text(row.get("sourceUrl")),
            }
        )
    return [row for row in normalized if row["name"]]
