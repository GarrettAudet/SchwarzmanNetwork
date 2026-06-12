from __future__ import annotations


def linkedin_queries(name: str, country: str = "", cohort: str = "") -> list[str]:
    qualifiers = [
        "Schwarzman Scholar LinkedIn",
        "Schwarzman Scholars Tsinghua LinkedIn",
        "Schwarzman College LinkedIn",
    ]
    context = " ".join(part for part in (name, country, cohort) if part)
    return [f'{context} "{qualifier}"' for qualifier in qualifiers]
