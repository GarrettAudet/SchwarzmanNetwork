from __future__ import annotations


def company_description_prompt(company_name: str, role_context: str = "") -> str:
    return (
        "Write one factual sentence describing the company. "
        "If the company cannot be identified from the supplied context, return an empty string.\n\n"
        f"Company: {company_name}\n"
        f"Context: {role_context}\n"
    )
