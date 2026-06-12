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

    def _extract_text(self, data: dict[str, object]) -> str:
        output_text = data.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()

        parts: list[str] = []
        output = data.get("output")
        if isinstance(output, list):
            for item in output:
                if not isinstance(item, dict):
                    continue
                content = item.get("content")
                if not isinstance(content, list):
                    continue
                for block in content:
                    if isinstance(block, dict) and isinstance(block.get("text"), str):
                        parts.append(block["text"])
        return "\n".join(part.strip() for part in parts if part.strip())

    def complete_text(self, prompt: str) -> str:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set; LLM enrichment is unavailable.")
        payload = {
            "model": self.model,
            "input": prompt,
            "temperature": 0.1,
            "max_output_tokens": 500,
        }
        request = Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
        return self._extract_text(data)
