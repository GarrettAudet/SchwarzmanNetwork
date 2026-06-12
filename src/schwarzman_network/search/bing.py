from __future__ import annotations

import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .collector import SearchCandidate
from ..config import load_dotenv


def search(query: str) -> list[SearchCandidate]:
    load_dotenv()
    api_key = os.environ.get("BING_SEARCH_API_KEY")
    if not api_key:
        return []
    params = urlencode({"q": query, "count": "5"})
    request = Request(
        f"https://api.bing.microsoft.com/v7.0/search?{params}",
        headers={"Accept": "application/json", "Ocp-Apim-Subscription-Key": api_key},
    )
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return [
        SearchCandidate(
            url=item.get("url", ""),
            title=item.get("name", ""),
            snippet=item.get("snippet", ""),
            provider="bing",
            query=query,
        )
        for item in payload.get("webPages", {}).get("value", [])
    ]
