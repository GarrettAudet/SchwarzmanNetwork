from __future__ import annotations

import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .collector import SearchCandidate
from ..config import load_dotenv


def search(query: str) -> list[SearchCandidate]:
    load_dotenv()
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_CSE_API_KEY")
    cx = os.environ.get("GOOGLE_CX") or os.environ.get("GOOGLE_CSE_ID")
    if not api_key or not cx:
        return []
    params = urlencode({"key": api_key, "cx": cx, "q": query, "num": "5"})
    request = Request(f"https://www.googleapis.com/customsearch/v1?{params}", headers={"Accept": "application/json"})
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return [
        SearchCandidate(
            url=item.get("link", ""),
            title=item.get("title", ""),
            snippet=item.get("snippet", ""),
            provider="google",
            query=query,
        )
        for item in payload.get("items", [])
    ]
