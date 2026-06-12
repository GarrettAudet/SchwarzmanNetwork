from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
SEED_DIR = DATA_DIR / "seed"
RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
AUDIT_DIR = DATA_DIR / "audit"
PROCESSED_DIR = DATA_DIR / "processed"
PUBLIC_DIR = DATA_DIR / "public"
SCHEMA_DIR = ROOT / "schema"

OFFICIAL_SOURCE_URL = "https://www.schwarzmanscholars.org/scholars/"
BRIGHTDATA_DATASET_ID = "gd_l1viktl72bvl7bjuj0"
BRIGHTDATA_LINKEDIN_FIELDS = [
    "position",
    "education",
    "current_company_name",
    "city",
    "experience",
    "current_company_company_id",
    "location",
]


def ensure_data_dirs() -> None:
    for path in (SEED_DIR, RAW_DIR, INTERIM_DIR, AUDIT_DIR, PROCESSED_DIR, PUBLIC_DIR):
        path.mkdir(parents=True, exist_ok=True)


def load_dotenv(path: Path | None = None) -> None:
    env_path = path or ROOT / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and key not in os.environ:
            os.environ[key] = value


def brightdata_api_key() -> str:
    load_dotenv()
    return (
        os.environ.get("BRIGHT_DATA_API")
        or os.environ.get("BRIGHT_DATA_API_KEY")
        or os.environ.get("BRIGHTDATA_API_KEY")
        or ""
    )


def openai_api_key() -> str:
    load_dotenv()
    return os.environ.get("OPENAI_API_KEY", "")
