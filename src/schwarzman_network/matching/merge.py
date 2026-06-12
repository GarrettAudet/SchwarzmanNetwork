from __future__ import annotations

import csv
import json
from pathlib import Path

from ..models import Scholar, clean_text, scholar_key
from ..official.parser import normalize_official_json
from ..search.normalize import linkedin_slug, normalize_linkedin_url


def append_new_official_scholars(seed_dir: Path, official_json_path: Path) -> dict[str, int]:
    scholars_path = seed_dir / "scholars.csv"
    linkedin_path = seed_dir / "linkedin_profiles.csv"
    payload = json.loads(official_json_path.read_text(encoding="utf-8"))
    official = normalize_official_json(payload)

    existing: dict[tuple[str, str], dict[str, str]] = {}
    if scholars_path.exists():
        with scholars_path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                existing[(clean_text(row.get("scholar_name")).lower(), clean_text(row.get("cohort")).upper())] = row

    new_scholars: list[Scholar] = []
    for row in official:
        name = clean_text(row.get("name"))
        cohort = clean_text(row.get("cohort")).upper()
        if not name or not cohort:
            continue
        if (name.lower(), cohort) in existing:
            continue
        new_scholars.append(
            Scholar(
                scholar_id=scholar_key(name, cohort),
                scholar_name=name,
                cohort=cohort,
                country=clean_text(row.get("country")),
                graduation_year=int(row["graduationYear"]) if row.get("graduationYear") else None,
                official_url=clean_text(row.get("sourceUrl")),
                official_bio=clean_text(row.get("bio")),
                source="official_append",
            )
        )

    if not new_scholars:
        return {"existing": len(existing), "appended": 0}

    with scholars_path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(new_scholars[0].row().keys()))
        if scholars_path.stat().st_size == 0:
            writer.writeheader()
        writer.writerows([scholar.row() for scholar in new_scholars])

    linkedin_exists = linkedin_path.exists() and linkedin_path.stat().st_size > 0
    with linkedin_path.open("a", encoding="utf-8", newline="") as handle:
        fieldnames = ["scholar_id", "scholar_name", "cohort", "linkedin_url", "linkedin_slug", "status", "source"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not linkedin_exists:
            writer.writeheader()
        for scholar in new_scholars:
            writer.writerow(
                {
                    "scholar_id": scholar.scholar_id,
                    "scholar_name": scholar.scholar_name,
                    "cohort": scholar.cohort,
                    "linkedin_url": "N/A",
                    "linkedin_slug": linkedin_slug("N/A"),
                    "status": "missing",
                    "source": "official_append",
                }
            )

    return {"existing": len(existing), "appended": len(new_scholars)}


def normalized_linkedin_seed_row(row: dict[str, str]) -> dict[str, str]:
    url = normalize_linkedin_url(row.get("linkedin_url") or row.get("LinkedIn") or "")
    return {
        **row,
        "linkedin_url": url,
        "linkedin_slug": linkedin_slug(url),
        "status": "present" if url != "N/A" else "missing",
    }
