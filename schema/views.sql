DROP VIEW IF EXISTS public_scholar_profiles;

CREATE VIEW public_scholar_profiles AS
WITH ranked_observation AS (
  SELECT
    eo.*,
    ROW_NUMBER() OVER (
      PARTITION BY eo.scholar_id
      ORDER BY
        CASE WHEN eo.source_kind = 'processed_profile' THEN 1 ELSE 0 END DESC,
        eo.observed_at DESC,
        eo.observation_id DESC
    ) AS observation_rank
  FROM employment_observations eo
),
latest_observation AS (
  SELECT *
  FROM ranked_observation
  WHERE observation_rank = 1
)
SELECT
  s.scholar_name AS "Scholar Name",
  COALESCE(c.industry, '') AS "Industry",
  s.cohort AS "Cohort",
  COALESCE(lp.linkedin_url, 'N/A') AS "LinkedIn Address",
  COALESCE(lo.profile_location, '') AS "Profile Location",
  COALESCE(lo.job_location, '') AS "Job Location",
  COALESCE(lo.current_title, '') AS "Current Job Title",
  COALESCE(lo.current_company, '') AS "Current Company",
  COALESCE(c.company_description, '') AS "Company Description",
  COALESCE(lo.experience_count, '') AS "Experience Count",
  COALESCE(lo.education_count, '') AS "Education Count",
  COALESCE(lo.work_history_json, '') AS "Work History",
  COALESCE(lo.education_json, '') AS "Education",
  COALESCE(lo.enrichment_source, '') AS "Enrichment Source",
  COALESCE(lo.enrichment_status, '') AS "Enrichment Status",
  COALESCE(s.country, '') AS "Country",
  COALESCE(lo.confidence, '') AS "Confidence",
  COALESCE(lo.observed_at, '') AS "Last Updated",
  COALESCE(lo.source_url, '') AS "Source URLs"
FROM scholars s
LEFT JOIN linkedin_profiles lp ON lp.scholar_id = s.scholar_id
LEFT JOIN latest_observation lo ON lo.scholar_id = s.scholar_id
LEFT JOIN companies c ON c.company_name = lo.current_company
ORDER BY s.graduation_year, s.scholar_name;
