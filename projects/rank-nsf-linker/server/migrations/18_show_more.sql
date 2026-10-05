-- Milestone 3: what the explorer shows beyond names and areas.
ALTER TABLE professors ADD COLUMN IF NOT EXISTS openalex_id TEXT;            -- OpenAlex researchers
ALTER TABLE explorer_faculty ADD COLUMN IF NOT EXISTS latest_work JSONB;      -- newest paper {title, year, url}
ALTER TABLE explorer_faculty ADD COLUMN IF NOT EXISTS first_year INTEGER;     -- first top-venue paper (CSRankings)
ALTER TABLE explorer_faculty ADD COLUMN IF NOT EXISTS orcid TEXT;
ALTER TABLE explorer_faculty ADD COLUMN IF NOT EXISTS openalex_id TEXT;
ALTER TABLE explorer_universities ADD COLUMN IF NOT EXISTS doctoral_degrees INTEGER;  -- IPEDS, latest year
ALTER TABLE explorer_universities ADD COLUMN IF NOT EXISTS doctoral_year INTEGER;
ALTER TABLE explorer_universities ADD COLUMN IF NOT EXISTS funders JSONB;     -- [{funder, people, active_people}]

-- Decode HTML entities some sources leave in titles ("&quot;Erlangen Programme&quot;", "&#8217;").
CREATE OR REPLACE FUNCTION html_unescape(s TEXT) RETURNS TEXT
LANGUAGE plpgsql IMMUTABLE STRICT AS $$
DECLARE
  m TEXT[];
BEGIN
  s := replace(replace(replace(replace(replace(replace(s,
         '&quot;', '"'), '&apos;', ''''), '&#39;', ''''), '&lt;', '<'), '&gt;', '>'), '&nbsp;', ' ');
  FOR m IN SELECT regexp_matches(s, '&#([0-9]{1,6});', 'g') LOOP
    s := replace(s, '&#' || m[1] || ';', chr(m[1]::int));
  END LOOP;
  FOR m IN SELECT regexp_matches(s, '&#[xX]([0-9a-fA-F]{1,5});', 'g') LOOP
    s := regexp_replace(s, '&#[xX]' || m[1] || ';', chr(('x' || lpad(m[1], 8, '0'))::bit(32)::int), 'g');
  END LOOP;
  -- Accented letters ("M&ouml;bius", "L&eacute;vy"): letter + combining mark, composed.
  FOR m IN SELECT regexp_matches(s, '&([A-Za-z])(acute|grave|uml|circ|tilde|cedil|ring);', 'g') LOOP
    s := replace(s, '&' || m[1] || m[2] || ';', normalize(m[1] || chr(CASE m[2]
           WHEN 'acute' THEN 769 WHEN 'grave' THEN 768 WHEN 'uml' THEN 776 WHEN 'circ' THEN 770
           WHEN 'tilde' THEN 771 WHEN 'cedil' THEN 807 ELSE 778 END), NFC));
  END LOOP;
  FOR m IN SELECT ARRAY[k, v] FROM (VALUES ('oslash', 'ø'), ('Oslash', 'Ø'), ('szlig', 'ß'), ('aelig', 'æ'),
      ('AElig', 'Æ'), ('sup1', '¹'), ('sup2', '²'), ('sup3', '³'), ('ndash', '–'), ('mdash', '—'),
      ('lsquo', '‘'), ('rsquo', '’'), ('ldquo', '“'), ('rdquo', '”'), ('hellip', '…'), ('times', '×'),
      ('deg', '°'), ('plusmn', '±'), ('micro', 'µ'), ('middot', '·'), ('reg', '®'), ('trade', '™'),
      ('copy', '©'), ('alpha', 'α'), ('beta', 'β'), ('gamma', 'γ'), ('delta', 'δ'), ('mu', 'μ'),
      ('pi', 'π'), ('sigma', 'σ'), ('lambda', 'λ')) e(k, v) WHERE position('&' || k || ';' IN s) > 0 LOOP
    s := replace(s, '&' || m[1] || ';', m[2]);
  END LOOP;
  RETURN replace(s, '&amp;', '&');  -- last, so "&amp;quot;" stays literal
END;
$$;
