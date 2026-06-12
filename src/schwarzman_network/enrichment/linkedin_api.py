from __future__ import annotations

import json
import time
from json import JSONDecodeError
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ..config import BRIGHTDATA_DATASET_ID, BRIGHTDATA_LINKEDIN_FIELDS, brightdata_api_key


class BrightDataLinkedInClient:
    def __init__(self, api_key: str | None = None, dataset_id: str = BRIGHTDATA_DATASET_ID) -> None:
        self.api_key = api_key or brightdata_api_key()
        self.dataset_id = dataset_id

    def _read_json(self, request: Request, timeout: int = 180) -> object:
        try:
            with urlopen(request, timeout=timeout) as response:
                text = response.read().decode("utf-8")
        except HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {error.code} from Bright Data: {body[:1000]}") from error
        if not text.strip():
            return {}
        try:
            return json.loads(text)
        except JSONDecodeError:
            records = []
            for line in text.splitlines():
                if not line.strip():
                    continue
                records.append(json.loads(line))
            return records

    def _get_json(self, url: str, timeout: int = 180) -> object:
        request = Request(url, headers={"Authorization": f"Bearer {self.api_key}", "Accept": "application/json"})
        return self._read_json(request, timeout=timeout)

    def wait_for_snapshot(self, snapshot_id: str, max_wait_seconds: int = 900, poll_seconds: int = 5) -> dict[str, object]:
        deadline = time.monotonic() + max_wait_seconds
        last_payload: object = {}
        while time.monotonic() < deadline:
            time.sleep(poll_seconds)
            last_payload = self._get_json(f"https://api.brightdata.com/datasets/v3/progress/{snapshot_id}", timeout=60)
            if isinstance(last_payload, dict) and last_payload.get("status") == "ready":
                return last_payload
            if isinstance(last_payload, dict) and last_payload.get("status") == "failed":
                raise RuntimeError(f"Bright Data snapshot {snapshot_id} failed: {json.dumps(last_payload)[:500]}")
        raise TimeoutError(f"Bright Data snapshot {snapshot_id} was not ready after {max_wait_seconds}s: {last_payload}")

    def download_snapshot(self, snapshot_id: str) -> list[dict[str, object]]:
        query = urlencode({"format": "json"})
        payload = self._get_json(f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}?{query}", timeout=180)
        if isinstance(payload, list):
            return [record for record in payload if isinstance(record, dict)]
        if isinstance(payload, dict) and isinstance(payload.get("data"), list):
            return [record for record in payload["data"] if isinstance(record, dict)]
        if isinstance(payload, dict) and isinstance(payload.get("result"), dict):
            return [payload["result"]]
        return []

    def scrape_profiles(self, urls: list[str], include_errors: bool = True) -> object:
        if not self.api_key:
            raise RuntimeError("BRIGHT_DATA_API is not set in the environment or .env file.")
        if not urls:
            return []
        query = urlencode(
            {
                "dataset_id": self.dataset_id,
                "custom_output_fields": ",".join(BRIGHTDATA_LINKEDIN_FIELDS),
                "notify": "false",
                "include_errors": "true" if include_errors else "false",
            }
        )
        endpoint = f"https://api.brightdata.com/datasets/v3/scrape?{query}"
        payload = {"input": [{"url": url} for url in urls]}
        request = Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        result = self._read_json(request, timeout=180)
        if isinstance(result, dict) and result.get("snapshot_id"):
            snapshot_id = str(result["snapshot_id"])
            self.wait_for_snapshot(snapshot_id)
            return self.download_snapshot(snapshot_id)
        return result
