from __future__ import annotations

import json
from pathlib import Path
from urllib.request import Request, urlopen

from .parser import parse_official_html
from ..config import OFFICIAL_SOURCE_URL, RAW_DIR
from ..models import utc_now_iso


def fetch_html(url: str = OFFICIAL_SOURCE_URL, timeout: int = 60) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; SchwarzmanNetwork/0.1; +public research)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch_official_scholars(url: str = OFFICIAL_SOURCE_URL) -> dict[str, object]:
    html = fetch_html(url)
    scholars = parse_official_html(html, source_url=url)
    counts_by_year: dict[str, int] = {}
    for scholar in scholars:
        year = str(scholar.get("graduationYear", ""))
        counts_by_year[year] = counts_by_year.get(year, 0) + 1
    return {
        "sourceUrl": url,
        "fetchedAt": utc_now_iso(),
        "count": len(scholars),
        "countsByYear": counts_by_year,
        "scholars": scholars,
    }


def write_official_snapshot(output_path: Path | None = None, url: str = OFFICIAL_SOURCE_URL) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = output_path or RAW_DIR / "official_scholars.json"
    payload = fetch_official_scholars(url)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
