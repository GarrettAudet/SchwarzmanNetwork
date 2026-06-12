from __future__ import annotations


def coverage_summary(rows: list[dict[str, str]]) -> dict[str, int]:
    total = len(rows)
    with_linkedin = sum(1 for row in rows if row.get("LinkedIn Address") and row.get("LinkedIn Address") != "N/A")
    with_company = sum(1 for row in rows if row.get("Current Company"))
    with_title = sum(1 for row in rows if row.get("Current Job Title"))
    with_profile_location = sum(1 for row in rows if row.get("Profile Location"))
    with_job_location = sum(1 for row in rows if row.get("Job Location"))
    with_work_history = sum(1 for row in rows if row.get("Work History"))
    with_education = sum(1 for row in rows if row.get("Education"))
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
        "with_profile_location": with_profile_location,
        "missing_profile_location": total - with_profile_location,
        "with_job_location": with_job_location,
        "missing_job_location": total - with_job_location,
        "with_work_history": with_work_history,
        "missing_work_history": total - with_work_history,
        "with_education": with_education,
        "missing_education": total - with_education,
        "with_industry": with_industry,
        "missing_industry": total - with_industry,
        "with_company_description": with_description,
        "missing_company_description": total - with_description,
    }
