CREATE EXTENSION IF NOT EXISTS unaccent;

-- NSF investigators, one row per NSF person id. Kept apart from professors (CSRankings faculty);
-- professor is the CSRankings match, set by the "Link NSF Investigators To Professors" step.
CREATE TABLE IF NOT EXISTS nsf_investigators (
  nsf_id TEXT PRIMARY KEY,
  full_name TEXT NOT NULL,
  first_name TEXT,
  last_name TEXT,
  middle_initial TEXT,
  professor TEXT REFERENCES professors(name) ON DELETE SET NULL,
  match_method TEXT
);
CREATE INDEX IF NOT EXISTS nsf_investigators_professor_idx ON nsf_investigators (professor);

-- investigator_id stays the NSF full name; nsf_id is the stable person id, email is per award
-- (it changes when people move, which is evidence for matching).
ALTER TABLE award_pi_rel ADD COLUMN IF NOT EXISTS nsf_id TEXT;
ALTER TABLE award_pi_rel ADD COLUMN IF NOT EXISTS email TEXT;
ALTER TABLE award_pi_rel DROP CONSTRAINT IF EXISTS award_pi_rel_investigator_id_fkey;
CREATE INDEX IF NOT EXISTS award_pi_rel_nsf_id_idx ON award_pi_rel (nsf_id);

-- Name tokens for matching people: unaccented, lowercase, hyphens and punctuation removed,
-- generational suffixes dropped. "José A. Ruiz-Pestana Jr." -> {jose, a, ruizpestana}
CREATE OR REPLACE FUNCTION person_name_tokens(name TEXT) RETURNS TEXT[]
LANGUAGE sql IMMUTABLE STRICT AS $$
  SELECT array_remove(
    regexp_split_to_array(
      btrim(regexp_replace(
        regexp_replace(
          regexp_replace(lower(unaccent('unaccent', name)), '[-''’]', '', 'g'),
          '[^a-z ]+', ' ', 'g'),
        '\m(jr|sr|ii|iii|iv|phd)\M', ' ', 'g')),
      '\s+'),
    '');
$$;

-- Registrable domain of an email address or URL: "foo@cs.cmu.edu" / "https://www.cs.cmu.edu/~x" -> "cmu.edu",
-- "https://www.imperial.ac.uk/people" -> "imperial.ac.uk". NULL for hosting/webmail domains,
-- which say nothing about where a person works.
CREATE OR REPLACE FUNCTION registrable_domain(addr TEXT) RETURNS TEXT
LANGUAGE sql IMMUTABLE STRICT AS $$
  SELECT CASE
    WHEN d IS NULL OR d ~ '^(gmail|googlemail|yahoo|hotmail|outlook|live|icloud|me|aol|proton|protonmail|github|gitlab|google|wordpress|wixsite|weebly|squarespace|medium|linkedin)\.' THEN NULL
    ELSE d END
  FROM (
    SELECT substring(h FROM '([a-z0-9-]+\.(?:(?:ac|edu|co|com|org|net|gov)\.[a-z]{2}|[a-z]+))$') AS d
    FROM (SELECT lower(COALESCE(substring(addr FROM '@([^@\s>]+)$'), substring(addr FROM '^[a-z]+://([^/:?#]+)'), addr)) AS h) x
  ) y;
$$;
