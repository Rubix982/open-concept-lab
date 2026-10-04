-- OpenAlex records for the explorer's papers, matched by DOI ("Load OpenAlex Works" step, from
-- data/openalex/works.csv written by server/scripts/openalex/works.py). Abstracts feed semantic
-- matching only; the explorer does not display them.
CREATE TABLE IF NOT EXISTS openalex_works (
  doi TEXT PRIMARY KEY,           -- lower case, without the https://doi.org/ prefix
  openalex_id TEXT,
  abstract TEXT,
  topic TEXT,
  subfield TEXT,
  field TEXT,
  cited_by INTEGER
);

-- Hash of the text each vector was embedded from, so a changed text (a new abstract) is re-embedded.
-- NULL: embedded before this column existed, from the title-only text.
ALTER TABLE explorer_embedded ADD COLUMN IF NOT EXISTS text_hash TEXT;
