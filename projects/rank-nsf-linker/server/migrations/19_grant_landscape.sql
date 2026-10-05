-- Every grant from every funder, linked to a person or not, for "where the money goes" on a search.
CREATE TABLE IF NOT EXISTS explorer_grants (
  funder        TEXT NOT NULL,
  id            TEXT NOT NULL,      -- the funder's grant id
  title         TEXT NOT NULL,
  snippet       TEXT,               -- start of the abstract
  amount        NUMERIC,
  currency      TEXT,
  starts        DATE,
  ends          DATE,
  url           TEXT,
  country       TEXT,
  lead          TEXT,               -- the principal investigator as the funder lists them
  institution   TEXT,               -- as the funder lists it
  university_id TEXT,               -- explorer_universities.id when the institution is on the map
  profile       TEXT,               -- explorer_faculty.name when the lead is in Advisor Atlas
  doc           TSVECTOR,
  PRIMARY KEY (funder, id)
);
CREATE INDEX IF NOT EXISTS explorer_grants_doc_idx ON explorer_grants USING gin (doc);

-- Signals a student can act on (see landscape.go): 'training' (a grant that pays PhD students: NIH T32,
-- NSF Research Traineeship) and 'new_lab' (a starting PI with money: NSF CAREER, ERC Starting, ...).
ALTER TABLE explorer_grants ADD COLUMN IF NOT EXISTS scheme TEXT;
ALTER TABLE explorer_grants ADD COLUMN IF NOT EXISTS programs TEXT[];   -- NSF programme names
ALTER TABLE explorer_grants ADD COLUMN IF NOT EXISTS signal TEXT;
ALTER TABLE explorer_faculty ADD COLUMN IF NOT EXISTS new_lab JSONB;    -- their newest running 'new_lab' grant
ALTER TABLE explorer_universities ADD COLUMN IF NOT EXISTS training JSONB; -- running 'training' grants
