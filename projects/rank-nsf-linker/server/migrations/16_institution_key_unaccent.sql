-- institution_key, transliterating accented letters first ("École" = "Ecole", "Universität" = "Universitat").
-- Migration 8's version dropped them ("École" -> "cole"). unaccent comes from migration 9.
CREATE OR REPLACE FUNCTION institution_key(name TEXT) RETURNS TEXT
LANGUAGE sql IMMUTABLE STRICT AS $$
  SELECT regexp_replace(
    regexp_replace(
      regexp_replace(
      regexp_replace(
        regexp_replace(
          replace(regexp_replace(lower(unaccent('unaccent', name)), '\([^)]*\)', ' ', 'g'), '&', ' and '),
          '[^a-z0-9]+', ' ', 'g'),
        '\muniv\M', 'university', 'g'),
      '\mtech\M', 'technology', 'g'),
      '\m(the|at|of|in)\M', ' ', 'g'),
    '\s+', '', 'g');
$$;

-- CSRankings added ORCID iDs to csrankings.csv (2026).
ALTER TABLE professors ADD COLUMN IF NOT EXISTS orcid TEXT;
