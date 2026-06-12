from __future__ import annotations

import json
from urllib.request import Request, urlopen

from ..config import openai_api_key


class LLMClient:
    def __init__(self, model: str = "gpt-4.1-mini") -> None:
        self.model = model
        self.api_key = openai_api_key()

    def available(self) -> bool:
        return bool(self.api_key)

    def complete_text(self, prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set; LLM enrichment is unavailable.")
        payload = {
            "model": self.model,
            "input": prompt,
            "temperature": 0.1,
        }
        request = Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data.get("output_text", "").strip()
