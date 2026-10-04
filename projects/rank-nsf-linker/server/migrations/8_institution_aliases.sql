-- The one rule for deciding that two institution names are the same institution.
-- Lowercase, drop parenthesised abbreviations ("(Mit)"), "&" -> "and", drop punctuation,
-- "Univ" -> "University", "Tech" -> "Technology", drop "the/at/of/in", drop spaces.
--   "The University Of Texas At Austin" = "University of Texas Austin" = "universitytexasaustin"
CREATE OR REPLACE FUNCTION institution_key(name TEXT) RETURNS TEXT
LANGUAGE sql IMMUTABLE STRICT AS $$
  SELECT regexp_replace(
    regexp_replace(
      regexp_replace(
      regexp_replace(
        regexp_replace(
          replace(regexp_replace(lower(name), '\([^)]*\)', ' ', 'g'), '&', ' and '),
          '[^a-z0-9]+', ' ', 'g'),
        '\muniv\M', 'university', 'g'),
      '\mtech\M', 'technology', 'g'),
      '\m(the|at|of|in)\M', ' ', 'g'),
    '\s+', '', 'g');
$$;

-- The university a name belongs to, with governing-body, foundation and department wording removed.
--   "Regents Of The University Of Michigan - Dearborn"  -> "University Of Michigan - Dearborn"
--   "University Of Kentucky Research Foundation"         -> "University Of Kentucky"
--   "Stanford University - Department Of Biology"        -> "Stanford University"
-- Only used when the result names an existing university (see the merge step).
CREATE OR REPLACE FUNCTION institution_parent_name(name TEXT) RETURNS TEXT
LANGUAGE sql IMMUTABLE STRICT AS $$
  SELECT btrim(
    regexp_replace(
    regexp_replace(
    regexp_replace(
    regexp_replace(
    regexp_replace(
    regexp_replace(
    regexp_replace(name,
      '^.*\m(on behalf of|obo)\M\s*', '', 'i'),
      '^(the\s+)?(president\s+and\s+)?(board\s+of\s+)?(regents|trustees)(\s+of)?(\s+the)?[\s,]+', '', 'i'),
      '^(the\s+)?(research\s+)?foundation\s+(of|for)(\s+the)?\s+', '', 'i'),
      '^(department|dept)\.?\s+of\s+[^,]+,\s*', '', 'i'),
      '[\s,-]+(department|dept\.?|sch|school)\s+of\s+.*$', '', 'i'),
      '[\s,-]+(board\s+of\s+trustees|research\s+(and\s+service\s+)?foundation|(applied\s+)?research\s+corporation|(medical\s+center\s+)?research\s+institute|center\s+for\s+research|sponsored\s+programs\s+foundation|auxiliary\s+services|foundation)([\s,]+inc\.?|\s*\(inc\.?\))?\s*$', '', 'i'),
      '([\s,]+(inc|incorporated)\.?|\s*\(inc\.?\)|[\s,]+(main\s+)?campus)\s*$', '', 'i'));
$$;

-- Every known spelling of an institution -> the name its row carries in universities.
-- source = 'curated' (backup/institution_aliases.csv) or 'merged' (found by the merge step).
CREATE TABLE IF NOT EXISTS institution_aliases (
  alias TEXT PRIMARY KEY,
  canonical TEXT NOT NULL,
  source TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS institution_aliases_canonical_idx ON institution_aliases (canonical);
