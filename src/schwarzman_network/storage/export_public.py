from __future__ import annotations

import csv
import json
from pathlib import Path

from .sqlite import connect
from ..config import PUBLIC_DIR
from ..reporting.coverage import coverage_summary


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
    companies_path = public_dir / "companies.csv"
    summary_path = public_dir / "dataset_summary.json"

    headers = [
        "Scholar Name",
        "Industry",
        "Cohort",
        "LinkedIn Address",
        "Current Location",
        "Current Job Title",
        "Current Company",
        "Company Description",
        "Country",
        "Confidence",
        "Last Updated",
        "Source URLs",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    with companies_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["Company", "Industry", "Company Description", "Confidence", "Method", "Source URL", "Enriched At"],
        )
        writer.writeheader()
        writer.writerows(company_rows)

    json_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    summary = coverage_summary(rows)
    summary["company_rows"] = len(company_rows)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return {"csv": csv_path, "json": json_path, "companies": companies_path, "summary": summary_path}
