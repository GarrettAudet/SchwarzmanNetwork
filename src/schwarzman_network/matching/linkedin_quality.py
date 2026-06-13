from __future__ import annotations

import csv
import re
from pathlib import Path

from ..config import AUDIT_DIR, SEED_DIR
from ..models import clean_text, utc_now_iso
from ..search.normalize import linkedin_slug, normalize_linkedin_url
from .validator import name_match_score


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _profile_names_by_url() -> dict[str, str]:
    names: dict[str, str] = {}
    for row in _read_csv(AUDIT_DIR / "brightdata_profile_decisions.csv"):
        url = normalize_linkedin_url(row.get("input_url", ""))
        name = clean_text(row.get("name"))
        if url != "N/A" and name:
            names[url] = name
    for row in _read_csv(AUDIT_DIR / "enrichlayer_profile_decisions.csv"):
        url = normalize_linkedin_url(row.get("input_url", ""))
        name = clean_text(row.get("enrichlayer_full_name"))
        if url != "N/A" and name:
            names[url] = name
    return names


def _has_latin_name_token(value: str) -> bool:
    return any(len(token) > 1 for token in re.findall(r"[A-Za-z]+", value or ""))


def review_linkedin_quality(seed_dir: Path = SEED_DIR) -> dict[str, object]:
    """Normalize pasted LinkedIn URLs and remove duplicated links unless ownership is clear."""
    linkedin_path = seed_dir / "linkedin_profiles.csv"
    observation_path = seed_dir / "employment_observations.csv"
    linkedin_rows = _read_csv(linkedin_path)
    observation_rows = _read_csv(observation_path)
    if not linkedin_rows:
        return {"reviewed": 0, "normalized": 0, "cleared": 0, "audit": ""}

    profile_names = _profile_names_by_url()
    by_url: dict[str, list[dict[str, str]]] = {}
    original_urls: dict[str, str] = {}
    normalized_count = 0
    for row in linkedin_rows:
        original_url = clean_text(row.get("linkedin_url"))
        original_urls[row.get("scholar_id", "")] = original_url
        normalized_url = normalize_linkedin_url(original_url)
        if normalized_url == "N/A":
            continue
        if normalized_url != original_url:
            row["linkedin_url"] = normalized_url
            row["linkedin_slug"] = linkedin_slug(normalized_url)
            normalized_count += 1
        by_url.setdefault(normalized_url, []).append(row)

    cleared_ids: set[str] = set()
    review_rows: list[dict[str, str]] = []
    reviewed = 0
    for url, rows in sorted(by_url.items()):
        if len(rows) < 2:
            continue
        reviewed += len(rows)
        profile_name = profile_names.get(url, "")
        observed_identity = f"{profile_name} {url}"
        scores = [(row, name_match_score(row.get("scholar_name", ""), observed_identity)) for row in rows]
        max_score = max((score for _, score in scores), default=0.0)
        winners = [row for row, score in scores if score == max_score and score >= 0.8]
        owner_id = winners[0].get("scholar_id", "") if len(winners) == 1 else ""

        for row, score in scores:
            action = "kept_unique_profile_name_match" if row.get("scholar_id") == owner_id else "cleared_duplicate_url"
            reason = "profile_name_match" if owner_id else "ambiguous_duplicate_url"
            if row.get("scholar_id") != owner_id:
                cleared_ids.add(row.get("scholar_id", ""))
                row["linkedin_url"] = "N/A"
                row["linkedin_slug"] = ""
                row["status"] = "missing"
                row["source"] = "duplicate_url_review"
            review_rows.append(
                {
                    "reviewed_at": utc_now_iso(),
                    "canonical_url": url,
                    "profile_name": profile_name,
                    "scholar_id": row.get("scholar_id", ""),
                    "scholar_name": row.get("scholar_name", ""),
                    "cohort": row.get("cohort", ""),
                    "name_match_score": f"{score:.3f}",
                    "action": action,
                    "reason": reason,
                }
            )

    for row in linkedin_rows:
        if row.get("scholar_id", "") in cleared_ids:
            continue
        url = normalize_linkedin_url(row.get("linkedin_url", ""))
        if url == "N/A":
            continue
        profile_name = profile_names.get(url, "")
        observed_identity = f"{profile_name} {url}"
        score = name_match_score(row.get("scholar_name", ""), observed_identity)
        original_url = original_urls.get(row.get("scholar_id", ""), "")
        has_pasted_label = "(linkedin)" in original_url.lower()
        should_clear = bool(profile_name and _has_latin_name_token(profile_name) and score <= 0.0) or bool(
            has_pasted_label and score <= 0.0
        )
        if not should_clear:
            continue
        cleared_ids.add(row.get("scholar_id", ""))
        row["linkedin_url"] = "N/A"
        row["linkedin_slug"] = ""
        row["status"] = "missing"
        row["source"] = "linkedin_quality_review"
        review_rows.append(
            {
                "reviewed_at": utc_now_iso(),
                "canonical_url": url,
                "profile_name": profile_name,
                "scholar_id": row.get("scholar_id", ""),
                "scholar_name": row.get("scholar_name", ""),
                "cohort": row.get("cohort", ""),
                "name_match_score": f"{score:.3f}",
                "action": "cleared_identity_mismatch",
                "reason": "profile_or_slug_name_mismatch",
            }
        )

    for row in observation_rows:
        if row.get("scholar_id") not in cleared_ids:
            continue
        row["current_location"] = ""
        row["current_company"] = ""
        row["current_title"] = ""
        row["source_url"] = ""
        row["confidence"] = "duplicate_url_review_missing"

    _write_csv(linkedin_path, linkedin_rows, list(linkedin_rows[0].keys()))
    if observation_rows:
        _write_csv(observation_path, observation_rows, list(observation_rows[0].keys()))

    audit_path = AUDIT_DIR / "linkedin_duplicate_review.csv"
    if review_rows:
        _write_csv(audit_path, review_rows, list(review_rows[0].keys()))

    return {
        "reviewed": reviewed,
        "normalized": normalized_count,
        "cleared": len(cleared_ids),
        "duplicates": len([rows for rows in by_url.values() if len(rows) > 1]),
        "audit": str(audit_path) if review_rows else "",
    }
