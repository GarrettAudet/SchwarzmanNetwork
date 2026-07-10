from __future__ import annotations

import csv
import json
from pathlib import Path

from .sqlite import connect
from ..config import AUDIT_DIR, PUBLIC_DIR
from ..reporting.coverage import coverage_summary


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def export_public(db_path: Path, public_dir: Path = PUBLIC_DIR) -> dict[str, Path]:
    public_dir.mkdir(parents=True, exist_ok=True)
    conn = connect(db_path)
    rows = [dict(row) for row in conn.execute("SELECT * FROM public_scholar_profiles")]
    company_rows = [
        dict(row)
        for row in conn.execute(
            """
            SELECT
              company_name AS "Company",
              industry AS "Industry",
              company_description AS "Company Description",
              confidence AS "Confidence",
              method AS "Method",
              source_url AS "Source URL",
              enriched_at AS "Enriched At"
            FROM companies
            ORDER BY company_name
            """
        )
    ]
    conn.close()

    csv_path = public_dir / "scholars.csv"
    json_path = public_dir / "scholars.json"
    enriched_profiles_path = public_dir / "enriched_profiles.csv"
    companies_path = public_dir / "companies.csv"
    summary_path = public_dir / "dataset_summary.json"

    headers = [
        "Scholar Name",
        "Industry",
        "Cohort",
        "LinkedIn Address",
        "Profile Location",
        "Job Location",
        "Current Job Title",
        "Current Company",
        "Company Description",
        "Experience Count",
        "Education Count",
        "Work History",
        "Education",
        "Enrichment Source",
        "Enrichment Status",
        "Country",
        "Confidence",
        "Last Updated",
        "Source URLs",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    public_by_url = {row.get("LinkedIn Address", ""): row for row in rows if row.get("LinkedIn Address")}
    enrichlayer_rows = _read_csv(AUDIT_DIR / "enrichlayer_profile_decisions.csv")
    enriched_headers = [
        "input_url",
        "enrichlayer_full_name",
        "Interesting Profile to Me",
        "Cohort",
        "Country",
        "Industry",
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
    enriched_rows: list[dict[str, str]] = []
    for row in enrichlayer_rows:
        public_row = public_by_url.get(row.get("input_url", ""), {})
        enriched_rows.append(
            {
                "input_url": row.get("input_url", ""),
                "enrichlayer_full_name": row.get("enrichlayer_full_name", ""),
                "Interesting Profile to Me": "",
                "Cohort": public_row.get("Cohort", ""),
                "Country": public_row.get("Country", ""),
                "Industry": public_row.get("Industry", ""),
                "enrichlayer_headline": row.get("enrichlayer_headline", ""),
                "enrichlayer_occupation": row.get("enrichlayer_occupation", ""),
                "enrichlayer_profile_location": row.get("enrichlayer_profile_location", ""),
                "enrichlayer_current_company": row.get("enrichlayer_current_company", ""),
                "enrichlayer_current_job_title": row.get("enrichlayer_current_job_title", ""),
                "enrichlayer_current_job_location": row.get("enrichlayer_current_job_location", ""),
                "enrichlayer_current_started_at": row.get("enrichlayer_current_started_at", ""),
                "enrichlayer_experience_count": row.get("enrichlayer_experience_count", ""),
                "enrichlayer_education_count": row.get("enrichlayer_education_count", ""),
                "enrichlayer_experience_json": row.get("enrichlayer_experience_json", ""),
                "enrichlayer_education_json": row.get("enrichlayer_education_json", ""),
                "enrichlayer_status": row.get("enrichlayer_status", ""),
                "enrichlayer_error": row.get("enrichlayer_error", ""),
                "enrichlayer_fetched_at": row.get("enrichlayer_fetched_at", ""),
            }
        )
    with enriched_profiles_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=enriched_headers, lineterminator="\n")
        writer.writeheader()
        writer.writerows(enriched_rows)

    with companies_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["Company", "Industry", "Company Description", "Confidence", "Method", "Source URL", "Enriched At"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(company_rows)

    json_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    summary = coverage_summary(rows)
    summary["company_rows"] = len(company_rows)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return {
        "csv": csv_path,
        "json": json_path,
        "enriched_profiles": enriched_profiles_path,
        "companies": companies_path,
        "summary": summary_path,
    }
