from __future__ import annotations

from urllib.parse import urlparse, urlunparse
import re

from ..models import clean_text


NA_VALUES = {"", "n/a", "na", "none", "null", "-"}


def normalize_linkedin_url(url: str) -> str:
    text = clean_text(url)
    if text.lower() in NA_VALUES:
        return "N/A"
    if not text:
        return "N/A"
    if not re.match(r"^https?://", text, flags=re.I):
        text = f"https://{text}"
    parsed = urlparse(text)
    host = parsed.netloc.lower()
    if not host.endswith("linkedin.com"):
        return "N/A"
    host = "www.linkedin.com"
    path = re.sub(r"/+$", "", parsed.path)
    profile_match = re.match(r"^/in/([^/]+)", path, flags=re.I)
    if not profile_match:
        return "N/A"
    path = f"/in/{profile_match.group(1)}"
    return urlunparse(("https", host, path, "", "", ""))


def linkedin_slug(url: str) -> str:
    normalized = normalize_linkedin_url(url)
    if normalized == "N/A":
        return ""
    match = re.search(r"linkedin\.com/in/([^/?#]+)", normalized, flags=re.I)
    return match.group(1).strip("/") if match else ""


def is_linkedin_profile_url(url: str) -> bool:
    normalized = normalize_linkedin_url(url)
    return bool(re.search(r"^https://www\.linkedin\.com/in/[^/?#]+$", normalized, flags=re.I))
