# Schwarzman Network

This repository maintains a lightweight public dataset of Schwarzman Scholars,
their stable LinkedIn profile URLs where verified, and enriched current
professional information.

The project is designed to be rerun yearly. It keeps the official scholar roster
and manually verified LinkedIn URLs separate from enrichment outputs, then
publishes a SQLite database plus CSV/JSON exports.

## Outputs

- `data/public/schwarzman_network.sqlite` - queryable SQLite database.
- `data/public/scholars.csv` - flat public scholar export.
- `data/public/scholars.json` - JSON version of the scholar export.
- `data/public/companies.csv` - company-level industry and description export.
- `data/public/dataset_summary.json` - coverage summary.

The main scholar export uses this column order:

```text
Scholar Name, Industry, Cohort, LinkedIn Address, Profile Location, Job Location,
Current Job Title, Current Company, Company Description, Experience Count,
Education Count, Work History, Education, Enrichment Source, Enrichment Status,
Country, Confidence, Last Updated, Source URLs
```

## Broad Refresh Steps

1. Import or maintain the seed scholar list.
2. Fetch the official Schwarzman Scholars roster.
3. Append net-new official scholars to the seed data.
4. Keep missing or unverified LinkedIn URLs as `N/A`.
5. Search configured providers for missing LinkedIn URLs.
6. Ask an LLM to adjudicate the search-result candidates using scholar context.
7. Promote only high-confidence LinkedIn `/in/` URLs selected from the candidate list.
8. Enrich verified LinkedIn profiles in bulk with Bright Data.
9. Optionally enrich verified LinkedIn profiles one-by-one with Enrichlayer for work history, education, and job-location fields.
10. Classify companies into one-word industries.
11. Attach one-sentence company descriptions when evidence is available.
12. Build the processed scholar CSV.
13. Build SQLite and public CSV/JSON exports.
14. Commit refreshed public artifacts.

## Local Commands

Install the package:

```powershell
python -m pip install -e .
```

Run the full local build from committed seed and audit data:

```powershell
python -m schwarzman_network.cli refresh
```

Run yearly-style refresh steps:

```powershell
python -m schwarzman_network.cli fetch-official
python -m schwarzman_network.cli sync-official
python -m schwarzman_network.cli find-linkedin --matching-mode llm
python -m schwarzman_network.cli enrich-brightdata --refresh
python -m schwarzman_network.cli enrich-enrichlayer --limit 200 --delay-sec 10 --max-retries 1 --retry-after-sec 300
python -m schwarzman_network.cli refresh
```

Enrichlayer's profile endpoint accepts one `profile_url` per request, so this
step is checkpointed in `data/audit/enrichlayer_progress.json` and cached in
`data/audit/enrichlayer_profile_decisions.csv`. Re-running the command skips
completed profiles unless `--refresh` is passed.

Run controlled LinkedIn matching trials:

```powershell
python -m schwarzman_network.cli trial-linkedin-matching
```

## GitHub Actions

The workflow in `.github/workflows/yearly-refresh.yml` runs once per year on
January 15 and can also be triggered manually. Manual runs can set
`brightdata_refresh=true` to refetch all valid LinkedIn profiles instead of only
profiles not already present in the Bright Data audit cache. They can also set
`brightdata_batch_size` to control how many LinkedIn profiles are sent in each
Bright Data scrape request.

Enrichlayer runs after Bright Data when `ENRICH_API` or `ENRICH_API_KEY` is
configured. Manual runs can set `enrichlayer_limit`, `enrichlayer_delay_sec`,
and `enrichlayer_refresh`. The default cap is 200 profiles per run so a test key
can stop cleanly and resume later.

Required secret for Bright Data enrichment:

- `BRIGHTDATA_API_KEY` or `BRIGHT_DATA_API` or `BRIGHT_DATA_API_KEY`

Optional secret for Enrichlayer profile enrichment:

- `ENRICH_API` or `ENRICH_API_KEY`

Required secret for automated LinkedIn URL adjudication:

- `OPENAI_API_KEY`

Optional search provider secrets:

- `GOOGLE_API_KEY`
- `GOOGLE_CX`
- `BRAVE_SEARCH_API_KEY`
- `BING_SEARCH_API_KEY`

Optional email notification secrets:

- `SMTP_SERVER`
- `SMTP_PORT` defaults to `587`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `UPDATE_EMAIL_TO`
- `UPDATE_EMAIL_FROM` optional; defaults to `SMTP_USERNAME`

The email step sends a notice only when the yearly run actually commits updated
data. If SMTP secrets are not configured, the workflow creates a GitHub issue
mentioning the repository owner so GitHub's notification system can still alert
you after an update.

## Notes

The pipeline does not guess LinkedIn URLs. Rows with missing or non-profile URLs
remain `N/A` until a validated profile URL is found. The default LinkedIn
matching mode sends the scholar context and search-result candidates to an LLM,
which may select only one of the provided candidate URLs or return `N/A`. A
candidate is promoted only when the LLM returns a high-confidence match.

Bright Data and Enrichlayer enrichment are used only for verified LinkedIn
profile URLs. If neither source returns company or title data for a profile, the
field stays blank unless a prior reviewed seed value exists. `Profile Location`
is the profile city/location. `Job Location` is populated only from job-derived
fields such as Enrichlayer `experiences[].location`, Bright Data
`experience[].location`, nested Bright Data `experience[].positions[].location`,
or `current_company.location`; it does not fall back to profile location.
