from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import re


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def clean_text(value: object) -> str:
    text = str(value or "").replace("\u00a0", " ")
    replacements = {
        "â€™": "'",
        "â€˜": "'",
        "â€œ": '"',
        "â€": '"',
        "â€“": "-",
        "â€”": "-",
        "â€¦": "...",
        "Ã©": "e",
        "Ã¨": "e",
        "Ã¼": "u",
        "Ã¶": "o",
        "Ã¡": "a",
        "Ã­": "i",
        "Ã³": "o",
        "Ã±": "n",
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    return re.sub(r"\s+", " ", text).strip()


def slugify(value: str) -> str:
    text = clean_text(value).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "unknown"


def scholar_key(name: str, cohort: str) -> str:
    return f"{clean_text(cohort).lower()}-{slugify(name)}"


@dataclass(frozen=True)
class Scholar:
    scholar_id: str
    scholar_name: str
    cohort: str
    country: str = ""
    graduation_year: int | None = None
    official_url: str = ""
    official_bio: str = ""
    source: str = "seed"

    def row(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class LinkedInProfile:
    scholar_id: str
    scholar_name: str
    cohort: str
    linkedin_url: str
    linkedin_slug: str
    status: str
    source: str

    def row(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class EmploymentObservation:
    scholar_id: str
    scholar_name: str
    cohort: str
    observed_at: str
    current_location: str
    current_company: str
    current_title: str
    source_kind: str
    source_url: str
    confidence: str
    raw_source: str = ""

    def row(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class CompanyProfile:
    company_name: str
    industry: str
    company_description: str
    confidence: str
    method: str
    source_url: str = ""

    def row(self) -> dict[str, object]:
        return asdict(self)
