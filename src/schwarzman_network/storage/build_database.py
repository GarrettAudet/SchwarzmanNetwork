from __future__ import annotations

import csv
from pathlib import Path

from .sqlite import connect, initialize
from ..config import PUBLIC_DIR, SEED_DIR
from ..enrichment.company import enrich_company
from ..models import clean_text, utc_now_iso


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def build_database(
    db_path: Path | None = None,
    seed_dir: Path = SEED_DIR,
    processed_path: Path | None = None,
) -> Path:
    db = db_path or PUBLIC_DIR / "schwarzman_network.sqlite"
    conn = connect(db)
    initialize(conn)
    now = utc_now_iso()

    scholars = _read_csv(seed_dir / "scholars.csv")
    linkedin = _read_csv(seed_dir / "linkedin_profiles.csv")
    observations = _read_csv(seed_dir / "employment_observations.csv")
    processed = _read_csv(processed_path) if processed_path else []
    scholar_ids_by_name_cohort = {
        (clean_text(row.get("scholar_name")).lower(), clean_text(row.get("cohort")).upper()): row.get("scholar_id", "")
        for row in scholars
    }

    with conn:
        conn.execute("DELETE FROM review_queue")
        conn.execute("DELETE FROM companies")
        conn.execute("DELETE FROM employment_observations")
        conn.execute("DELETE FROM linkedin_profiles")
        conn.execute("DELETE FROM scholars")

        for row in scholars:
            conn.execute(
                """
                INSERT INTO scholars (
                  scholar_id, scholar_name, cohort, country, graduation_year,
                  official_url, official_bio, source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(scholar_id) DO UPDATE SET
                  scholar_name=excluded.scholar_name,
                  cohort=excluded.cohort,
                  country=excluded.country,
                  graduation_year=excluded.graduation_year,
                  official_url=excluded.official_url,
                  official_bio=excluded.official_bio,
                  source=excluded.source
                """,
                (
                    row.get("scholar_id"),
                    row.get("scholar_name"),
                    row.get("cohort"),
                    row.get("country"),
                    int(row["graduation_year"]) if row.get("graduation_year") else None,
                    row.get("official_url"),
                    row.get("official_bio"),
                    row.get("source"),
                ),
            )
        for row in linkedin:
            conn.execute(
                """
                INSERT INTO linkedin_profiles (scholar_id, linkedin_url, linkedin_slug, status, source)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(scholar_id) DO UPDATE SET
                  linkedin_url=excluded.linkedin_url,
                  linkedin_slug=excluded.linkedin_slug,
                  status=excluded.status,
                  source=excluded.source
                """,
                (
                    row.get("scholar_id"),
                    row.get("linkedin_url") or "N/A",
                    row.get("linkedin_slug"),
                    row.get("status") or "missing",
                    row.get("source"),
                ),
            )
        for row in observations:
            if not (row.get("current_company") or row.get("current_location") or row.get("current_title")):
                continue
            conn.execute(
                """
                INSERT INTO employment_observations (
                  scholar_id, observed_at, current_location, current_company,
                  current_title, source_kind, source_url, confidence, raw_source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row.get("scholar_id"),
                    row.get("observed_at") or now,
                    row.get("current_location"),
                    row.get("current_company"),
                    row.get("current_title"),
                    row.get("source_kind"),
                    row.get("source_url"),
                    row.get("confidence"),
                    row.get("raw_source"),
                ),
            )
        for row in processed:
            if not (row.get("Current Company") or row.get("Current Location") or row.get("Current Job Title")):
                continue
            scholar_id = scholar_ids_by_name_cohort.get(
                (clean_text(row.get("Scholar Name")).lower(), clean_text(row.get("Cohort")).upper())
            )
            if not scholar_id:
                continue
            conn.execute(
                """
                INSERT INTO employment_observations (
                  scholar_id, observed_at, current_location, current_company,
                  current_title, source_kind, source_url, confidence, raw_source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    scholar_id,
                    row.get("Last Updated") or now,
                    row.get("Current Location"),
                    row.get("Current Company"),
                    row.get("Current Job Title"),
                    "processed_profile",
                    row.get("Source URLs"),
                    row.get("Confidence"),
                    processed_path.name if processed_path else "",
                ),
            )
        for row in processed:
            company = clean_text(row.get("Current Company"))
            if not company:
                continue
            profile = enrich_company(company, row.get("Current Job Title", ""))
            conn.execute(
                """
                INSERT INTO companies (
                  company_name, industry, company_description, confidence,
                  method, source_url, enriched_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(company_name) DO UPDATE SET
                  industry=excluded.industry,
                  company_description=excluded.company_description,
                  confidence=excluded.confidence,
                  method=excluded.method,
                  source_url=excluded.source_url,
                  enriched_at=excluded.enriched_at
                """,
                (
                    profile.company_name,
                    row.get("Industry") or profile.industry,
                    row.get("Company Description") or profile.company_description,
                    profile.confidence,
                    profile.method,
                    row.get("Source URLs") or "",
                    now,
                ),
            )
    conn.close()
    return db
