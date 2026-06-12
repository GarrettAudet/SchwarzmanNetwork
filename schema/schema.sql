PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS scholars (
  scholar_id TEXT PRIMARY KEY,
  scholar_name TEXT NOT NULL,
  cohort TEXT NOT NULL,
  country TEXT,
  graduation_year INTEGER,
  official_url TEXT,
  official_bio TEXT,
  source TEXT,
  UNIQUE (scholar_name, cohort)
);

CREATE TABLE IF NOT EXISTS linkedin_profiles (
  scholar_id TEXT PRIMARY KEY REFERENCES scholars(scholar_id) ON DELETE CASCADE,
  linkedin_url TEXT,
  linkedin_slug TEXT,
  status TEXT NOT NULL,
  source TEXT
);

CREATE TABLE IF NOT EXISTS employment_observations (
  observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
  scholar_id TEXT NOT NULL REFERENCES scholars(scholar_id) ON DELETE CASCADE,
  observed_at TEXT NOT NULL,
  current_location TEXT,
  profile_location TEXT,
  job_location TEXT,
  current_company TEXT,
  current_title TEXT,
  source_kind TEXT,
  source_url TEXT,
  confidence TEXT,
  raw_source TEXT
);

CREATE TABLE IF NOT EXISTS companies (
  company_name TEXT PRIMARY KEY,
  industry TEXT,
  company_description TEXT,
  confidence TEXT,
  method TEXT,
  source_url TEXT,
  enriched_at TEXT
);

CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT PRIMARY KEY,
  started_at TEXT NOT NULL,
  completed_at TEXT,
  pipeline_version TEXT,
  counts_json TEXT
);

CREATE TABLE IF NOT EXISTS review_queue (
  review_id INTEGER PRIMARY KEY AUTOINCREMENT,
  scholar_id TEXT REFERENCES scholars(scholar_id) ON DELETE CASCADE,
  reason TEXT NOT NULL,
  detail TEXT,
  created_at TEXT NOT NULL
);
