from __future__ import annotations

import re


def cohort_from_graduation_year(graduation_year: int | None) -> str:
    if not graduation_year:
        return ""
    cohort_number = graduation_year - 2016
    return f"C{cohort_number}" if cohort_number > 0 else ""


def graduation_year_from_cohort(cohort: str) -> int | None:
    match = re.search(r"\d+", cohort or "")
    if not match:
        return None
    return 2016 + int(match.group(0))


def parse_program_years(class_year: str = "", data_year: str = "") -> tuple[int | None, int | None]:
    years = [int(match.group(1)) for match in re.finditer(r"\b(20\d{2})\b", class_year or "")]
    data_year_int = int(data_year) if str(data_year).isdigit() else None
    program_start_year = years[0] if years else (data_year_int - 1 if data_year_int else None)
    graduation_year = years[1] if len(years) > 1 else data_year_int
    return program_start_year, graduation_year
