from __future__ import annotations

import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .collector import SearchCandidate
from ..config import load_dotenv


def search(query: str) -> list[SearchCandidate]:
    load_dotenv()
    api_key = os.environ.get("BRAVE_SEARCH_API_KEY")
    if not api_key:
        return []
    params = urlencode({"q": query, "count": "5"})
    request = Request(
        f"https://api.search.brave.com/res/v1/web/search?{params}",
        headers={"Accept": "application/json", "X-Subscription-Token": api_key},
    )
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return [
        SearchCandidate(
            url=item.get("url", ""),
            title=item.get("title", ""),
            snippet=item.get("description", ""),
            provider="brave",
            query=query,
        )
        for item in payload.get("web", {}).get("results", [])
    ]
