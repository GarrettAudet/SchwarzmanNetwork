from __future__ import annotations


def coverage_summary(rows: list[dict[str, str]]) -> dict[str, int]:
    total = len(rows)
    with_linkedin = sum(1 for row in rows if row.get("LinkedIn Address") and row.get("LinkedIn Address") != "N/A")
    with_company = sum(1 for row in rows if row.get("Current Company"))
    with_title = sum(1 for row in rows if row.get("Current Job Title"))
    with_location = sum(1 for row in rows if row.get("Current Location"))
    with_industry = sum(1 for row in rows if row.get("Industry"))
    with_description = sum(1 for row in rows if row.get("Company Description"))
    return {
        "total_rows": total,
        "with_linkedin": with_linkedin,
        "missing_linkedin": total - with_linkedin,
        "with_company": with_company,
        "missing_company": total - with_company,
        "with_current_job_title": with_title,
        "missing_current_job_title": total - with_title,
        "with_current_location": with_location,
        "missing_current_location": total - with_location,
        "with_industry": with_industry,
        "missing_industry": total - with_industry,
        "with_company_description": with_description,
        "missing_company_description": total - with_description,
    }
