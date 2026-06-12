from __future__ import annotations


def is_schwarzman_context(text: str) -> bool:
    lowered = (text or "").lower()
    return any(term in lowered for term in ("schwarzman", "tsinghua", "schwarzman college"))
