from __future__ import annotations

import csv
from pathlib import Path

from .normalize import normalize_linkedin_url
from ..models import clean_text


def read_manual_linkedin_seed(path: Path) -> dict[tuple[str, str], str]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = csv.DictReader(handle)
        out: dict[tuple[str, str], str] = {}
        for row in rows:
            name = clean_text(row.get("scholar_name") or row.get("Scholar Name"))
            cohort = clean_text(row.get("cohort") or row.get("Cohort"))
            url = normalize_linkedin_url(row.get("linkedin_url") or row.get("LinkedIn") or "")
            if name and cohort:
                out[(name.lower(), cohort.upper())] = url
        return out
