-- Grants from funders other than NSF (Marsden, ARC, UKRI, ANR, ...), loaded from the common
-- CSV format written by server/scripts/grants/*.py ("Load Funder Grants" step).
CREATE TABLE IF NOT EXISTS funder_grants (
  funder TEXT NOT NULL,           -- 'marsden', 'arc', 'ukri', 'anr', 'erc', 'snsf', 'kaken'
  grant_id TEXT NOT NULL,
  title TEXT NOT NULL,
  abstract TEXT,
  amount NUMERIC,
  currency TEXT,
  starts DATE,
  ends DATE,
  url TEXT,
  country TEXT,                   -- ISO alpha-2, lower case, of the funder
  scheme TEXT,
  field TEXT,                     -- the funder's own field label (panel, Field of Research, ...)
  PRIMARY KEY (funder, grant_id)
);

-- Investigators on those grants; professor is their CSRankings match ("Link Funder Grants" step).
CREATE TABLE IF NOT EXISTS funder_grant_people (
  funder TEXT NOT NULL,
  grant_id TEXT NOT NULL,
  full_name TEXT NOT NULL,
  first_name TEXT,
  last_name TEXT,
  role TEXT,                      -- 'PI' (lead / chief investigator) or 'CoI'
  institution TEXT,
  orcid TEXT,
  professor TEXT,
  match_method TEXT,
  PRIMARY KEY (funder, grant_id, full_name)
);
CREATE INDEX IF NOT EXISTS funder_grant_people_professor_idx ON funder_grant_people (professor);

-- Per professor, per funder: active/total grants and active amount (explorer_faculty.funding).
ALTER TABLE explorer_faculty ADD COLUMN IF NOT EXISTS funding JSONB;
