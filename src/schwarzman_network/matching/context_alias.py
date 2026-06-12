from __future__ import annotations


ALIASES = {
    "bcg": "Boston Consulting Group",
    "mckinsey": "McKinsey & Company",
    "jpmorgan": "J.P. Morgan",
}


def expand_alias(text: str) -> str:
    lowered = (text or "").lower()
    return ALIASES.get(lowered, text)
