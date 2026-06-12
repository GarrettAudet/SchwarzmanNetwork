from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import PROCESSED_DIR, RAW_DIR, SEED_DIR
from .pipeline import (
    build_db_and_exports,
    build_processed_profiles,
    enrich_brightdata,
    find_missing_linkedin,
    fetch_official,
    import_workbook,
    sync_official,
)
from .matching.trials import run_linkedin_matching_trials


def _print(payload: object) -> None:
    print(json.dumps(payload, indent=2, default=str))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="schwarzman-network")
    sub = parser.add_subparsers(dest="command", required=True)

    import_cmd = sub.add_parser("import-workbook", help="Import the current workbook into normalized seed CSVs.")
    import_cmd.add_argument("--input", required=True, type=Path)
    import_cmd.add_argument("--seed-dir", default=SEED_DIR, type=Path)
    import_cmd.add_argument("--sheet", default="LinkedIn Addresses")

    fetch_cmd = sub.add_parser("fetch-official", help="Fetch and parse the official Schwarzman Scholars roster.")
    fetch_cmd.add_argument("--output", default=RAW_DIR / "official_scholars.json", type=Path)

    sync_cmd = sub.add_parser("sync-official", help="Append net-new official scholars to seed files with LinkedIn=N/A.")
    sync_cmd.add_argument("--official", default=RAW_DIR / "official_scholars.json", type=Path)
    sync_cmd.add_argument("--seed-dir", default=SEED_DIR, type=Path)

    find_cmd = sub.add_parser("find-linkedin", help="Search for missing LinkedIn URLs and promote only validated matches.")
    find_cmd.add_argument("--seed-dir", default=SEED_DIR, type=Path)
    find_cmd.add_argument("--limit", default=0, type=int)
    find_cmd.add_argument("--providers", default="google,brave,bing")
    find_cmd.add_argument(
        "--matching-mode",
        choices=["llm", "heuristic", "llm-or-heuristic"],
        default="llm",
        help="How to adjudicate search-result candidates. The yearly-safe default is llm.",
    )

    bright_cmd = sub.add_parser("enrich-brightdata", help="Enrich LinkedIn URLs through Bright Data.")
    bright_cmd.add_argument("--seed-dir", default=SEED_DIR, type=Path)
    bright_cmd.add_argument("--batch-size", default=25, type=int)
    bright_cmd.add_argument("--limit", default=0, type=int)
    bright_cmd.add_argument("--refresh", action="store_true")

    processed_cmd = sub.add_parser("build-processed", help="Build the flat scholar information CSV.")
    processed_cmd.add_argument("--seed-dir", default=SEED_DIR, type=Path)
    processed_cmd.add_argument("--output", default=PROCESSED_DIR / "scholar_information.csv", type=Path)
    processed_cmd.add_argument("--use-llm", action="store_true")

    db_cmd = sub.add_parser("build-db", help="Build SQLite and public CSV/JSON exports.")
    db_cmd.add_argument("--processed", default=PROCESSED_DIR / "scholar_information.csv", type=Path)

    sub.add_parser("trial-linkedin-matching", help="Run controlled trials comparing heuristic and LLM LinkedIn matching.")

    refresh_cmd = sub.add_parser("refresh", help="Run the yearly pipeline.")
    refresh_cmd.add_argument("--fetch-official", action="store_true")
    refresh_cmd.add_argument("--sync-official", action="store_true")
    refresh_cmd.add_argument("--find-linkedin", action="store_true")
    refresh_cmd.add_argument(
        "--linkedin-matching-mode",
        choices=["llm", "heuristic", "llm-or-heuristic"],
        default="llm",
    )
    refresh_cmd.add_argument("--brightdata", action="store_true")
    refresh_cmd.add_argument("--brightdata-limit", default=0, type=int)
    refresh_cmd.add_argument("--use-llm", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "import-workbook":
        _print(import_workbook(args.input, args.seed_dir, args.sheet))
    elif args.command == "fetch-official":
        _print({"official": str(fetch_official(args.output))})
    elif args.command == "sync-official":
        _print(sync_official(args.official, args.seed_dir))
    elif args.command == "find-linkedin":
        providers = [provider.strip() for provider in args.providers.split(",") if provider.strip()]
        _print(find_missing_linkedin(args.seed_dir, args.limit, providers, matching_mode=args.matching_mode))
    elif args.command == "enrich-brightdata":
        _print(enrich_brightdata(args.seed_dir, args.batch_size, args.limit, args.refresh))
    elif args.command == "build-processed":
        _print({"processed": str(build_processed_profiles(args.seed_dir, args.output, use_llm=args.use_llm))})
    elif args.command == "build-db":
        _print(build_db_and_exports(args.processed))
    elif args.command == "trial-linkedin-matching":
        _print(run_linkedin_matching_trials())
    elif args.command == "refresh":
        result: dict[str, object] = {}
        if args.fetch_official:
            result["official"] = str(fetch_official())
        if args.sync_official:
            result["sync"] = sync_official()
        if args.find_linkedin:
            result["find_linkedin"] = find_missing_linkedin(matching_mode=args.linkedin_matching_mode)
        if args.brightdata:
            result["brightdata"] = enrich_brightdata(limit=args.brightdata_limit)
        processed = build_processed_profiles(use_llm=args.use_llm)
        result["processed"] = str(processed)
        result["exports"] = build_db_and_exports(processed)
        _print(result)


if __name__ == "__main__":
    main()
