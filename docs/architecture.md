# Schwarzman Network Architecture

This repo is organized as a small yearly data pipeline. The pipeline keeps the
original evidence and review steps separate from the public distribution layer.

## Source Package

```text
src/schwarzman_network/
  cli.py
  config.py
  models.py
  pipeline.py

  official/
    extractor.py
    parser.py
    cohort.py

  search/
    collector.py
    queries.py
    normalize.py
    manual_import.py
    yahoo.py
    bing.py
    aol.py
    brave.py
    duckduckgo.py
    google.py

  matching/
    llm_client.py
    llm_prompts.py
    adjudicator.py
    validator.py
    merge.py
    special_evidence.py
    post_profile.py
    context_alias.py
    evidence.py
    run_helpers.py

  enrichment/
    linkedin_api.py
    schema.py
    company.py

  storage/
    sqlite.py
    build_database.py
    export_public.py

  reporting/
    coverage.py
```

## Data Layout

```text
data/
  seed/
    scholars.csv
    linkedin_profiles.csv
    employment_observations.csv

  raw/
    official_scholars.json

  interim/
    brightdata_linkedin_profiles.jsonl
    search_cache_*.json

  audit/
    brightdata_profile_decisions.csv
    linkedin_decisions_*.csv
    coverage_report_*.json

  processed/
    scholar_information.csv

  public/
    schwarzman_network.sqlite
    scholars.csv
    scholars.json
    companies.csv
    dataset_summary.json
```

## Refresh Flow

1. Import the workbook once into normalized seed files.
2. Fetch the official Schwarzman Scholars roster.
3. Append net-new official scholars to `data/seed/scholars.csv`.
4. Add `N/A` LinkedIn rows for new scholars until a URL is verified.
5. Search configured providers for missing LinkedIn URLs and promote only validated matches.
6. Enrich verified LinkedIn URLs with Bright Data.
7. Build `data/processed/scholar_information.csv`.
8. Build `data/public/schwarzman_network.sqlite`.
9. Export `data/public/scholars.csv`, `scholars.json`, `companies.csv`, and `dataset_summary.json`.

Missing LinkedIn URLs are not guessed. Search providers and manual imports can
add candidates, but only validated profile URLs should be promoted into
`linkedin_profiles.csv`.

## Key Commands

```powershell
$env:PYTHONPATH='src'
python -m schwarzman_network.cli import-workbook --input "C:\Users\garre\OneDrive\Desktop\SchwarzmanNetworkAnalysis.xlsx"
python -m schwarzman_network.cli fetch-official
python -m schwarzman_network.cli sync-official
python -m schwarzman_network.cli find-linkedin
python -m schwarzman_network.cli enrich-brightdata --limit 25
python -m schwarzman_network.cli refresh
```

The Bright Data command reads `BRIGHT_DATA_API`, `BRIGHT_DATA_API_KEY`, or
`BRIGHTDATA_API_KEY` from the environment or `.env`.
