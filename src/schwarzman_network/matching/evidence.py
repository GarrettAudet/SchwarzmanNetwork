from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Evidence:
    source_url: str
    source_kind: str
    text: str
    confidence: str = "medium"
